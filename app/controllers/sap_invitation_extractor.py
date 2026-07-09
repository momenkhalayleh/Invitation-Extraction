import logging
import re
import time
from collections.abc import Iterator
from datetime import date, datetime

from selenium.common.exceptions import (
    InvalidSessionIdException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.clients import sap_selectors_config as selectors
from app.controllers.selenuim_client import SapClient, SapClientError
from app.schemas.invitation import InvitationCreate

logger = logging.getLogger("al_ghanem.extraction.sap.invitations")

DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y")


class SapInvitationExtractor:
    """Scrapes invitation records from Manage Sales Enquiries."""

    def __init__(self, client: SapClient) -> None:
        self.client = client

    @property
    def driver(self) -> WebDriver:
        return self.client.web_driver

    @property
    def timeout(self) -> int:
        return self.client.timeout

    def prepare_search(self, date_from: str, date_to: str) -> None:
        self.client.ensure_launchpad()
        self.client.navigate_to_manage_sales_enquiries()
        self.client.apply_date_filter(date_from, date_to)
        self.client.click_go()
        self.client.wait_for_results_table()

    def iter_invitations(self, max_count: int | None = None) -> Iterator[InvitationCreate]:
        processed_refs: set[str] = set()
        limit = (
            self.client.settings.sap_max_invitations
            if max_count is None
            else max_count
        )
        unlimited = limit <= 0
        saved_count = 0

        if self.client.settings.sap_skip_first_inquiry:
            first_links = self._get_inquiry_links()
            if first_links:
                first_ref = self._link_ref(first_links[0])
                if first_ref:
                    processed_refs.add(first_ref)
                    logger.info("Skipping first inquiry %s (locked / test mode)", first_ref)

        while unlimited or saved_count < limit:
            links = self._get_inquiry_links()
            unprocessed = [
                (link, ref)
                for link, ref in ((link, self._link_ref(link)) for link in links)
                if ref and ref not in processed_refs
            ]

            if not unprocessed:
                if self._go_next_page():
                    continue
                break

            link, ref_hint = unprocessed[0]
            processed_refs.add(ref_hint)

            try:
                self._open_inquiry(link)
                if not self._click_change_view():
                    logger.warning("'Change Sales Inquiries' link not found for %s", ref_hint)
                if not self.open_custom_fields_section():
                    raise SapClientError(
                        "Change Sales Inquiries did not open the expected WebGUI page "
                        "(Cust. Reference not found)"
                    )
                invitation = self.scrape_current_invitation(known_ref=ref_hint)
            except (
                SapClientError,
                StaleElementReferenceException,
                InvalidSessionIdException,
                WebDriverException,
            ) as exc:
                logger.warning("Skipping inquiry %s due to error: %s", ref_hint, exc)
                self._recover_to_list()
                continue

            processed_refs.add(invitation.inv_ref)
            logger.info("Scraped invitation %s", invitation.inv_ref)
            yield invitation
            saved_count += 1
            self._back_to_list()

        logger.info("Extraction finished (%s invitation(s))", saved_count)

    def extract_by_ref(self, inv_ref: str) -> InvitationCreate:
        """Find and scrape one invitation by Sales Inquiry ID from the current search results."""
        target = inv_ref.strip().upper()

        while True:
            links = self._get_inquiry_links()
            for link in links:
                ref = self._link_ref(link)
                if not ref or ref.upper() != target:
                    continue

                try:
                    self._open_inquiry(link)
                    if not self._click_change_view():
                        logger.warning("'Change Sales Inquiries' link not found for %s", ref)
                    if not self.open_custom_fields_section():
                        raise SapClientError(
                            "Change Sales Inquiries did not open the expected WebGUI page "
                            "(Cust. Reference not found)"
                        )
                    invitation = self.scrape_current_invitation(known_ref=ref)
                except (
                    SapClientError,
                    StaleElementReferenceException,
                    InvalidSessionIdException,
                    WebDriverException,
                ) as exc:
                    raise SapClientError(
                        f"Failed to extract invitation {target}: {exc}"
                    ) from exc

                logger.info("Scraped invitation %s", invitation.inv_ref)
                return invitation

            if not self._go_next_page():
                break

        raise SapClientError(f"Invitation {target} not found in search results")

    def _get_inquiry_links(self) -> list[WebElement]:
        for by, value in selectors.SALES_INQUIRY_LINKS:
            found = self.driver.find_elements(by, value)
            links = [el for el in found if el.is_displayed()]
            if links:
                return links
        return []

    def _link_ref(self, link: WebElement) -> str | None:
        try:
            return self._normalize_text(link.text)
        except StaleElementReferenceException:
            return None

    def _open_inquiry(self, link: WebElement) -> None:
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
        time.sleep(0.5)
        try:
            link.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", link)
        time.sleep(2)
        self._wait_for_object_page()

    def _click_change_view(self) -> bool:
        wait = WebDriverWait(self.driver, self.timeout)
        for by, value in selectors.CHANGE_INQUIRY_LINKS:
            try:
                element = wait.until(EC.element_to_be_clickable((by, value)))
            except TimeoutException:
                continue
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", element)
            # WebGUI change view is heavy; give it time to load before continuing.
            time.sleep(4)
            self._switch_to_latest_window()
            return True
        return False

    def open_custom_fields_section(self) -> bool:
        """Navigate the WebGUI change view: focus Cust. Reference,
        click Forward, then open the Custom Fields tab."""
        if not self._enter_webgui_context(selectors.WEBGUI_ANCHORS):
            logger.warning("WebGUI change view not detected (Cust. Reference not found)")
            return False

        # Step 1: click the "Cust. Reference" label itself (the Hotspot), not its input.
        self._click_webgui_label("customer_ref")
        time.sleep(1)

        # Step 2: click Forward to reveal further tab-strip items.
        self._click_webgui(selectors.FORWARD_SCROLL_BUTTONS, "Forward button", required=False)
        time.sleep(1.5)

        # Step 3: open the Custom Fields tab.
        clicked = self._click_webgui(selectors.CUSTOM_FIELDS_TABS, "Custom Fields tab")
        time.sleep(1.5)
        return clicked

    def _click_webgui_label(self, field_key: str) -> bool:
        """Click the WebGUI field label (Hotspot) itself, not the input beside it."""
        label = self._find_webgui_label(field_key)
        if label is None:
            logger.warning("WebGUI label for '%s' not found", field_key)
            return False
        self._click_element(label, f"{field_key} label (Cust. Reference)")
        return True

    def _webgui_input_for_label(self, field_key: str) -> WebElement | None:
        """Resolve a WebGUI input via its label's ``for`` attribute (stable across sessions)."""
        wait = WebDriverWait(self.driver, self.timeout)

        label = self._find_webgui_label(field_key, wait=wait)
        if label is None:
            return None

        target_id = label.get_attribute("for")
        if not target_id:
            logger.debug("Label for '%s' has no 'for' attribute", field_key)
            return None

        try:
            return wait.until(EC.presence_of_element_located((By.ID, target_id)))
        except TimeoutException:
            # Fallback: CSS attribute selector handles special characters in IDs.
            try:
                return wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f"[id='{target_id}']"))
                )
            except TimeoutException:
                logger.warning("Input with id='%s' not found for field '%s'", target_id, field_key)
                return None

    def _find_webgui_label(
        self,
        field_key: str,
        wait: WebDriverWait | None = None,
    ) -> WebElement | None:
        fragments = selectors.WEBGUI_LABEL_FRAGMENTS.get(field_key, ())
        waiter = wait or WebDriverWait(self.driver, self.timeout)

        for fragment in fragments:
            xpath = f"//label[contains(normalize-space(.), '{fragment}')]"
            try:
                label = waiter.until(EC.presence_of_element_located((By.XPATH, xpath)))
                if label.is_displayed():
                    return label
            except TimeoutException:
                continue

        for by, value in selectors.CUST_REFERENCE_LABELS:
            if field_key != "customer_ref":
                break
            try:
                label = waiter.until(EC.presence_of_element_located((by, value)))
                if label.is_displayed():
                    return label
            except TimeoutException:
                continue

        return None

    def _read_webgui_field_by_label(self, field_key: str) -> str | None:
        input_el = self._webgui_input_for_label(field_key)
        if input_el is None:
            return None
        return self._normalize_text(input_el.get_attribute("value"))

    def _click_element(self, element: WebElement, label: str) -> None:
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)
        logger.info("Clicked %s", label)

    def _switch_to_latest_window(self) -> None:
        handles = self.driver.window_handles
        if len(handles) > 1:
            self.driver.switch_to.window(handles[-1])
            time.sleep(1)

    def _enter_webgui_context(self, locators: tuple, timeout: int = 20) -> bool:
        """Locate the WebGUI content, switching into its iframe if needed.
        Leaves the driver focused on the frame that contains the anchor."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.driver.switch_to.default_content()
            if self._present(locators):
                return True

            frames = self.driver.find_elements(By.TAG_NAME, "iframe")
            for frame in frames:
                self.driver.switch_to.default_content()
                try:
                    self.driver.switch_to.frame(frame)
                except Exception:
                    continue
                if self._present(locators):
                    return True
                # one level of nesting
                nested = self.driver.find_elements(By.TAG_NAME, "iframe")
                for nested_frame in nested:
                    try:
                        self.driver.switch_to.frame(nested_frame)
                    except Exception:
                        continue
                    if self._present(locators):
                        return True
                    self.driver.switch_to.default_content()
                    try:
                        self.driver.switch_to.frame(frame)
                    except Exception:
                        break
            time.sleep(1)

        self.driver.switch_to.default_content()
        return False

    def _present(self, locators: tuple) -> bool:
        for by, value in locators:
            if self.driver.find_elements(by, value):
                return True
        return False

    def _click_webgui(self, locators: tuple, label: str, required: bool = True) -> bool:
        wait = WebDriverWait(self.driver, self.timeout)
        for by, value in locators:
            try:
                element = wait.until(EC.element_to_be_clickable((by, value)))
            except TimeoutException:
                continue
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", element)
            logger.info("Clicked %s", label)
            return True
        if required:
            logger.warning("%s not found", label)
        return False

    def _recover_to_list(self) -> None:
        # Leave any WebGUI iframe/window before returning to the Fiori list.
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        handles = self.driver.window_handles
        if len(handles) > 1:
            self.driver.switch_to.window(handles[0])
            time.sleep(1)
        self._back_to_list()

    def _wait_for_object_page(self) -> None:
        wait = WebDriverWait(self.driver, self.timeout)
        try:
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[id*='ObjectPage']")),
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[.//span[normalize-space()='Change Sales Inquiries']]")
                    ),
                )
            )
        except TimeoutException as exc:
            raise SapClientError("Object Page did not load after opening inquiry") from exc

    def _back_to_list(self) -> None:
        for _ in range(4):
            if self._get_inquiry_links():
                return
            self.client.return_to_results_list()
            time.sleep(1.5)
        logger.warning("Could not confirm return to results list")

    def scrape_current_invitation(self, known_ref: str | None = None) -> InvitationCreate:
        payload: dict[str, str | date | None] = {}

        # inv_ref = Sales Inquiry number from the Fiori results list (e.g. UAE1401321).
        payload["inv_ref"] = known_ref

        field_sources = {
            "customer_ref": self._read_webgui_field("customer_ref"),
            "customer_name": self._read_webgui_field("customer_name"),
            "scope_of_work": self._read_webgui_field("scope_of_work"),
            "inv_subject": self._read_webgui_field("inv_subject"),
            "product_type": self._read_webgui_field("product_type"),
            "closing_date": self._parse_date(self._read_webgui_field("closing_date")),
        }

        for field_name, value in field_sources.items():
            if value is not None:
                payload[field_name] = value
                logger.info("Field %s = %s", field_name, value)

        if not payload.get("inv_ref"):
            raise SapClientError("Could not determine invitation reference (no link ref available)")

        return InvitationCreate(**payload)

    def _read_webgui_field(self, field_key: str) -> str | None:
        locators = selectors.WEBGUI_FIELD_INPUTS.get(field_key, ())
        if not locators:
            return self._read_webgui_field_by_label(field_key)

        wait = WebDriverWait(self.driver, self.timeout)
        for by, value in locators:
            try:
                element = wait.until(EC.presence_of_element_located((by, value)))
            except TimeoutException:
                continue
            if not element.is_displayed():
                continue

            if field_key in selectors.WEBGUI_LABEL_VALUE_FIELDS:
                raw = element.get_attribute("title") or element.text
            else:
                raw = element.get_attribute("value") or element.text

            normalized = self._normalize_text(raw)
            if normalized:
                return normalized

        # Fallback for customer_ref: label -> for -> input.
        if field_key == "customer_ref":
            return self._read_webgui_field_by_label("customer_ref")

        return None

    def _wait_for_detail_page(self) -> None:
        wait = WebDriverWait(self.driver, self.timeout)
        try:
            wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(@class,'sapMObjectHeader') or contains(@class,'sapMObjectPage') "
                        "or contains(@class,'sapMForm') or contains(., 'Sales Inquir')]",
                    )
                )
            )
            time.sleep(1)
        except TimeoutException as exc:
            raise SapClientError("Invitation detail page did not load") from exc

    def _go_next_page(self) -> bool:
        for by, value in selectors.NEXT_PAGE_BUTTONS:
            buttons = self.driver.find_elements(by, value)
            for button in buttons:
                if not button.is_displayed() or not button.is_enabled():
                    continue
                if button.get_attribute("aria-disabled") == "true":
                    continue
                button.click()
                time.sleep(2)
                logger.info("Moved to next results page")
                return True
        return False

    def _read_field_by_labels(self, labels: tuple[str, ...]) -> str | None:
        for label in labels:
            value = self._read_label_value(label)
            if value:
                return value
        return None

    def _read_label_value(self, label: str) -> str | None:
        xpaths = [
            f"//*[normalize-space(text())='{label}']/following::*[self::span or self::div or self::textarea or self::input][1]",
            f"//*[contains(normalize-space(.), '{label}')]/following::span[contains(@class,'sapMText')][1]",
            f"//label[contains(normalize-space(.), '{label}')]/following::span[1]",
            f"//span[contains(normalize-space(.), '{label}')]/ancestor::div[1]/following-sibling::div//span[1]",
            f"//*[contains(@aria-label, '{label}')]",
        ]
        for xpath in xpaths:
            elements = self.driver.find_elements(By.XPATH, xpath)
            for element in elements:
                if not element.is_displayed():
                    continue
                if element.tag_name == "input":
                    value = element.get_attribute("value")
                elif element.tag_name == "textarea":
                    value = element.get_attribute("value") or element.text
                else:
                    value = element.text
                value = self._normalize_text(value)
                if value and value.lower() != label.lower():
                    return value
        return None

    def _read_title_inv_ref(self) -> str | None:
        title_elements = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".sapMTitle, .sapMObjectHeaderTitle, [id*='ObjectPage'] h1, [id*='ObjectPage'] h2",
        )
        for element in title_elements:
            text = self._normalize_text(element.text)
            if text:
                return text.split(" ")[0]
        return None

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        candidate = value.strip()
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
        match = re.search(r"\d{2}[./-]\d{2}[./-]\d{4}|\d{4}-\d{2}-\d{2}", candidate)
        if not match:
            return None
        token = match.group(0)
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(token, fmt).date()
            except ValueError:
                continue
        return None
