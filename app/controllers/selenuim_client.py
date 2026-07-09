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

from app.clients import sap_selectors_config as selectors
from app.configs.auth import SapCredentials, get_sap_credentials
from app.configs.settings import Settings, get_settings

logger = logging.getLogger("al_ghanem.extraction.sap")


class SapClientError(Exception):
    """Raised when SAP browser automation fails."""


class SapClient:
    """Selenium client for SAP S/4HANA Cloud Fiori (web)."""

    MANAGE_SALES_ENQUIRIES_LABEL = "Manage Sales Enquiries"

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

    def navigate_to_manage_sales_enquiries(self) -> None:
        self._require_driver()
        self.ensure_launchpad()

        if self.settings.sap_manage_sales_enquiries_url:
            logger.info("Opening Manage Sales Enquiries via direct URL")
            self.driver.get(self.settings.sap_manage_sales_enquiries_url)
            self._wait_for_app_shell()
            return

        # Preferred: click the app tile in the launchpad favorites section.
        tile = self._find_clickable(
            selectors.MANAGE_INQUIRIES_TILES,
            "Manage Sales Inquiries tile",
            timeout=15,
            required=False,
        )
        if tile is not None:
            logger.info("Opening Manage Sales Inquiries via favorites tile")
            tile.click()
            self._wait_for_app_shell()
            logger.info("Manage Sales Inquiries screen opened")
            return

        logger.info("Tile not found; searching Fiori launchpad for '%s'", self.MANAGE_SALES_ENQUIRIES_LABEL)

        # In Fiori the search box is hidden behind a magnifier toggle; click it first.
        self._click_if_present(selectors.FIORI_SEARCH_TOGGLES, "Fiori search toggle")
        time.sleep(1)

        search_field = self._find_clickable(
            selectors.FIORI_SEARCH_FIELDS,
            "Fiori search field",
            required=False,
        )
        if search_field is None:
            raise SapClientError(
                "Could not find the Fiori search field. Set SAP_MANAGE_SALES_ENQUIRIES_URL in .env "
                "to open the app directly (recommended)."
            )

        search_field.clear()
        search_field.send_keys(self.MANAGE_SALES_ENQUIRIES_LABEL)
        time.sleep(1)
        search_field.send_keys(Keys.ENTER)
        time.sleep(2)

        tile = self._find_clickable(
            selectors.SALES_ENQUIRY_TARGETS,
            "Manage Sales Enquiries tile",
            timeout=20,
        )
        tile.click()
        self._wait_for_app_shell()
        logger.info("Manage Sales Enquiries screen opened")

    def apply_date_filter(self, date_from: str, date_to: str) -> None:
        self._require_driver()
        date_option = self.settings.sap_date_option
        logger.info("Applying date filter: option=%s (%s to %s)", date_option, date_from, date_to)

        # Open the Document Date picker (calendar button on the filter bar).
        self._click_if_present(selectors.DATE_PICKER_TOGGLES, "Document Date picker")
        time.sleep(1)

        # The picker shows a dropdown of options (Date / Today / Yesterday / From / To ...).
        if not self._click_text_option(self._date_option_labels(date_option)):
            logger.warning("Could not select date option '%s' in picker", date_option)
            return

        time.sleep(1)

        # Single-day options (Today, Yesterday, Tomorrow) need no further input.
        if date_option.strip().lower() in {"today", "yesterday", "tomorrow"}:
            self._click_if_present(selectors.DATE_OK_BUTTONS, "date OK")
            logger.info("Selected single-day option '%s'", date_option)
            return

        from_field = self._find_visible(selectors.DATE_FROM_FIELDS, "date-from field", required=False)
        if from_field is None:
            logger.warning("Date-from field not found after selecting '%s'", date_option)
        else:
            self._set_input_value(from_field, date_from)

        to_field = self._find_visible(selectors.DATE_TO_FIELDS, "date-to field", required=False)
        if to_field is None:
            logger.warning("Date-to field not found after selecting '%s'", date_option)
        else:
            self._set_input_value(to_field, date_to)

        # Confirm the picker quickly so Go can run with minimal delay.
        self._click_if_present(selectors.DATE_OK_BUTTONS, "date OK")
        time.sleep(0.3)

    @staticmethod
    def _date_option_labels(option: str) -> tuple[str, ...]:
        cleaned = option.strip()
        variants = {cleaned}
        # Normalize spacing around slashes, e.g. "From / To" <-> "From/To"
        variants.add(cleaned.replace(" / ", "/"))
        variants.add(cleaned.replace("/", " / "))
        return tuple(variants)

    def _click_text_option(self, labels: tuple[str, ...]) -> bool:
        self._require_driver()
        for label in labels:
            xpaths = (
                # Matches the SAP list item span, e.g. id="...-option-TODAY-titleText"
                f"//span[contains(@id,'-option-') and normalize-space(text())='{label}']",
                f"//div[contains(@class,'sapMSLITitleOnly')]/span[normalize-space(text())='{label}']",
                f"//span[normalize-space(text())='{label}']/ancestor::li[1]",
                f"//li[@role='option'][.//span[normalize-space(text())='{label}']]",
                f"//*[@role='option'][normalize-space(.)='{label}']",
                f"//li[normalize-space(.)='{label}']",
            )
            for xpath in xpaths:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if not element.is_displayed():
                        continue
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", element
                    )
                    time.sleep(0.3)
                    try:
                        element.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", element)
                    logger.info("Clicked date option '%s'", label)
                    return True
        return False

    def click_go(self) -> None:
        self._require_driver()
        go_button = self._find_clickable(selectors.GO_BUTTONS, "Go button", required=False)
        if go_button is None:
            logger.warning("Go button not found; selectors may need updating in Step 4")
            return
        go_button.click()
        time.sleep(0.5)
        logger.info("Clicked Go to load enquiry results")

    def wait_for_results_table(self, timeout: int | None = None) -> None:
        self._require_driver()
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "table, [role='grid'], .sapMList, .sapUiTable")
                )
            )
            logger.info("Results area detected on screen")
        except TimeoutException as exc:
            raise SapClientError("Timed out waiting for enquiry results table") from exc

    def return_to_results_list(self) -> None:
        self._require_driver()
        for by, value in selectors.BACK_BUTTONS:
            buttons = self.driver.find_elements(by, value)
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    time.sleep(1.5)
                    logger.debug("Returned to results list via Back")
                    return
        self.driver.back()
        time.sleep(1.5)
        logger.debug("Returned to results list via browser back")

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

    def wait_until_not_busy(self, timeout: int | None = None) -> None:
        """Wait for document ready and SAP busy indicators to clear."""
        self._require_driver()
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        try:
            wait.until(self._is_document_ready)
            wait.until(self._is_sap_not_busy)
        except TimeoutException:
            logger.debug("Page still busy after %ss; continuing", timeout or self.timeout)
        self._settle()

    def wait_for_locators(
        self,
        locator_options: Iterable[tuple[str, str]],
        label: str,
        *,
        clickable: bool = False,
        timeout: int | None = None,
        required: bool = True,
    ) -> WebElement | None:
        """Wait for the first matching locator to appear (or become clickable)."""
        if clickable:
            return self._find_clickable(locator_options, label, timeout=timeout, required=required)
        return self._find_visible(locator_options, label, timeout=timeout, required=required)

    def _settle(self) -> None:
        delay = self.settings.sap_settle_ms / 1000
        if delay > 0:
            time.sleep(delay)

    @staticmethod
    def _is_document_ready(driver: WebDriver) -> bool:
        try:
            return driver.execute_script("return document.readyState") == "complete"
        except Exception:
            return True

    @staticmethod
    def _is_sap_not_busy(driver: WebDriver) -> bool:
        busy_selectors = (
            ".sapUiBusy",
            ".sapUiLocalBusyIndicator",
            ".sapUiBlockLayer",
            "[aria-busy='true']",
        )
        for selector in busy_selectors:
            for element in driver.find_elements(By.CSS_SELECTOR, selector):
                if element.is_displayed():
                    return False
        return True
