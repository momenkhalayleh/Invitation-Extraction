import logging
import time
from collections.abc import Iterable
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.tags import loader as selectors
from app.configs.auth import SapCredentials, get_sap_credentials
from app.configs.settings import Settings, get_settings

logger = logging.getLogger("al_ghanem.extraction.sap")


class SapClientError(Exception):
    """Raised when SAP browser automation fails."""


class SapClient:
    """Selenium client for SAP S/4HANA Cloud Fiori (web)."""

    def __init__(
        self,
        settings: Settings | None = None,
        credentials: SapCredentials | None = None,
        headless: bool | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.credentials = credentials or get_sap_credentials(self.settings)
        self.headless = self.settings.headless if headless is None else headless
        self.timeout = self.settings.selenium_timeout
        self.driver: WebDriver | None = None

    def __enter__(self) -> "SapClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    @property
    def current_url(self) -> str:
        self._require_driver()
        return self.driver.current_url

    @property
    def page_title(self) -> str:
        self._require_driver()
        return self.driver.title

    def start(self) -> None:
        if self.driver is not None:
            return

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver_path = self._resolve_chromedriver_path()
        if driver_path:
            logger.info("Using local ChromeDriver: %s", driver_path)
            service = Service(driver_path)
        else:
            logger.warning("No local ChromeDriver found; attempting webdriver-manager download")
            service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(0)
        logger.info("Chrome WebDriver started (headless=%s)", self.headless)

    def stop(self) -> None:
        if self.driver is None:
            return
        self.driver.quit()
        self.driver = None
        logger.info("Chrome WebDriver stopped")

    def _resolve_chromedriver_path(self) -> str | None:
        """Resolve ChromeDriver without network when possible (corporate SSL safe)."""
        if self.settings.chromedriver_path:
            configured = Path(self.settings.chromedriver_path)
            if configured.is_file():
                return str(configured)
            raise SapClientError(f"CHROMEDRIVER_PATH does not exist: {configured}")

        wdm_cache = Path.home() / ".wdm" / "drivers" / "chromedriver"
        if not wdm_cache.exists():
            return None

        candidates = sorted(
            wdm_cache.rglob("chromedriver.exe"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return str(candidates[0]) if candidates else None

    def login(self) -> None:
        self._require_driver()
        logger.info("Opening SAP login URL")
        self.driver.get(self.credentials.url)
        self._submit_username()
        self._submit_password()
        self._wait_for_post_login()
        self.ensure_launchpad()
        logger.info("SAP login completed. URL: %s", self.driver.current_url)

    def ensure_launchpad(self) -> None:
        self._require_driver()
        if self.settings.sap_manage_sales_enquiries_url:
            return

        current_url = self.driver.current_url.lower()
        on_launchpad = any(token in current_url for token in ("shell", "launchpad", "flp", "ui5"))
        if on_launchpad:
            logger.info("Already on Fiori shell")
            return

        if not self.settings.sap_launchpad_url:
            logger.warning(
                "Not on Fiori launchpad after login. Set SAP_LAUNCHPAD_URL or SAP_MANAGE_SALES_ENQUIRIES_URL in .env"
            )
            return

        logger.info("Navigating to Fiori launchpad")
        self.driver.get(self.settings.sap_launchpad_url)
        self._wait_for_app_shell()

    def click_back_button(self) -> bool:
        """
        Click the Fiori/UI5 Back button once (title/aria-description='Back', nav-back icon).

        Searches the shell document and application iframes, including open shadow roots,
        because after WebGUI scraping the driver is often on default_content while Back
        lives inside the app iframe.
        """
        self._require_driver()

        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

        contexts: list[object | None] = [None]  # None = stay on current/default
        try:
            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
        except Exception:
            frames = []
        contexts.extend(frames)

        for frame in contexts:
            try:
                self.driver.switch_to.default_content()
                if frame is not None:
                    self.driver.switch_to.frame(frame)
            except Exception:
                continue

            if self._click_back_in_current_document():
                try:
                    self.driver.switch_to.default_content()
                except Exception:
                    pass
                return True

            # One level of nested iframe (common for WebGUI inside Fiori).
            try:
                nested_frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            except Exception:
                nested_frames = []
            for nested in nested_frames:
                try:
                    self.driver.switch_to.frame(nested)
                except Exception:
                    continue
                if self._click_back_in_current_document():
                    try:
                        self.driver.switch_to.default_content()
                    except Exception:
                        pass
                    return True
                try:
                    self.driver.switch_to.parent_frame()
                except Exception:
                    try:
                        self.driver.switch_to.default_content()
                        if frame is not None:
                            self.driver.switch_to.frame(frame)
                    except Exception:
                        break

        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        return False

    def _click_back_in_current_document(self) -> bool:
        """Find and click a visible Back control in the current browsing context."""
        # Prefer JS: pierces open shadow roots used by UI5 web components.
        clicked = self.driver.execute_script(
            """
            function isBack(el) {
              if (!el) return false;
              const title = (el.getAttribute('title') || '').trim();
              const desc = (el.getAttribute('aria-description') || '').trim();
              const label = (el.getAttribute('aria-label') || '').trim();
              if (title === 'Back' || desc === 'Back' || label === 'Back') return true;
              if (el.querySelector) {
                if (el.querySelector('[name="sap-icon://nav-back"]')) return true;
                if (el.querySelector('[aria-label="Navigate Back"]')) return true;
              }
              return false;
            }
            function collect(root, out) {
              if (!root) return;
              const nodes = root.querySelectorAll(
                "button, [role='button'], ui5-button, .ui5-button-root"
              );
              for (const n of nodes) {
                if (isBack(n)) out.push(n);
              }
              const all = root.querySelectorAll('*');
              for (const el of all) {
                if (el.shadowRoot) collect(el.shadowRoot, out);
              }
            }
            const found = [];
            collect(document, found);
            for (const el of found) {
              try {
                const style = window.getComputedStyle(el);
                if (style && (style.display === 'none' || style.visibility === 'hidden')) continue;
                el.scrollIntoView({block: 'center'});
                el.click();
                return true;
              } catch (e) {}
            }
            return false;
            """
        )
        if clicked:
            logger.info("Clicked Back button (UI5)")
            return True

        for by, value in selectors.BACK_BUTTONS:
            try:
                buttons = self.driver.find_elements(by, value)
            except Exception:
                continue
            for button in buttons:
                try:
                    if not button.is_displayed() or not button.is_enabled():
                        continue
                except StaleElementReferenceException:
                    continue
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", button
                    )
                    self.driver.execute_script("arguments[0].click();", button)
                except Exception:
                    try:
                        button.click()
                    except Exception:
                        continue
                logger.info("Clicked Back button")
                return True
        return False

    @property
    def web_driver(self) -> WebDriver:
        self._require_driver()
        return self.driver

    def keep_open(self, seconds: int) -> None:
        if seconds <= 0:
            return
        logger.info("Keeping browser open for %s seconds", seconds)
        time.sleep(seconds)

    def _submit_username(self) -> None:
        self._fill_field(selectors.USERNAME_FIELDS, self.credentials.username, "username field")
        self._click_if_present(selectors.LOGIN_SUBMIT_BUTTONS, "username submit")
        self._wait_for_password_step()

    def _submit_password(self) -> None:
        filled = self._fill_field(
            selectors.PASSWORD_FIELDS,
            self.credentials.password,
            "password field",
            timeout=20,
            required=False,
        )
        if not filled:
            logger.info("Password field not shown separately; continuing")
            return

        self._click_if_present(selectors.LOGIN_SUBMIT_BUTTONS, "password submit")

    def _wait_for_password_step(self) -> None:
        self._require_driver()
        wait = WebDriverWait(self.driver, 15)
        try:
            wait.until(
                EC.any_of(
                    *[
                        EC.visibility_of_element_located((by, value))
                        for by, value in selectors.PASSWORD_FIELDS
                    ]
                )
            )
            time.sleep(0.5)
        except TimeoutException:
            logger.debug("No separate password step detected after username submit")

    def _fill_field(
        self,
        locator_options: Iterable[tuple[str, str]],
        value: str,
        label: str,
        timeout: int | None = None,
        required: bool = True,
    ) -> bool:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                field = self._find_visible(
                    locator_options,
                    label,
                    timeout=timeout,
                    required=required,
                )
                if field is None:
                    return False
                field.click()
                field.clear()
                field.send_keys(value)
                return True
            except StaleElementReferenceException as exc:
                last_error = exc
                logger.debug("Stale element on %s, retrying (attempt %s)", label, attempt + 1)
                time.sleep(0.75)

        if last_error:
            raise SapClientError(f"Could not fill {label}: page changed during login") from last_error
        return False

    def _wait_for_post_login(self) -> None:
        self._require_driver()
        wait = WebDriverWait(self.driver, self.timeout)
        try:
            wait.until(lambda driver: "login" not in driver.current_url.lower())
        except TimeoutException:
            logger.warning("Login redirect not detected; continuing anyway")

    def _wait_for_app_shell(self) -> None:
        self._require_driver()
        wait = WebDriverWait(self.driver, self.timeout)
        try:
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "shell")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[id*='application']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table, [role='grid'], .sapMPage")),
                )
            )
        except TimeoutException:
            logger.warning("Fiori app shell not detected within timeout; continuing")

    def _set_input_value(self, element: WebElement, value: str) -> None:
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.DELETE)
        element.send_keys(value)

    def _find_visible(
        self,
        locator_options: Iterable[tuple[str, str]],
        label: str,
        timeout: int | None = None,
        required: bool = True,
    ) -> WebElement | None:
        self._require_driver()
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        last_error: Exception | None = None

        for by, value in locator_options:
            try:
                return wait.until(EC.visibility_of_element_located((by, value)))
            except TimeoutException as exc:
                last_error = exc

        if required:
            raise SapClientError(f"Could not find {label}") from last_error
        return None

    def _find_clickable(
        self,
        locator_options: Iterable[tuple[str, str]],
        label: str,
        timeout: int | None = None,
        required: bool = True,
    ) -> WebElement | None:
        self._require_driver()
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        last_error: Exception | None = None

        for by, value in locator_options:
            try:
                return wait.until(EC.element_to_be_clickable((by, value)))
            except TimeoutException as exc:
                last_error = exc

        if required:
            raise SapClientError(f"Could not find clickable {label}") from last_error
        return None

    def _click_if_present(
        self,
        locator_options: Iterable[tuple[str, str]],
        label: str,
    ) -> None:
        button = self._find_clickable(locator_options, label, timeout=5, required=False)
        if button is not None:
            button.click()

    def _require_driver(self) -> None:
        if self.driver is None:
            raise SapClientError("WebDriver is not started. Call start() or use SapClient as a context manager.")
