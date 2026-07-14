"""SAP Fiori login workflow (username / password / post-login wait)."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.controllers.selenuim_client import SapClient, SapClientError
from app.tags import loader as selectors

logger = logging.getLogger("al_ghanem.extraction.sap.login")


class LoginController:
    """Owns the SAP login form flow; uses SapClient for the browser session."""

    def __init__(self, client: SapClient) -> None:
        self.client = client

    def login(self) -> None:
        self.client._require_driver()
        logger.info("Opening SAP login URL")
        self.client.driver.get(self.client.credentials.url)
        self._submit_username()
        self._submit_password()
        self._wait_for_post_login()
        self.client.ensure_launchpad()
        logger.info("SAP login completed. URL: %s", self.client.driver.current_url)

    def _submit_username(self) -> None:
        self._fill_field(
            selectors.USERNAME_FIELDS,
            self.client.credentials.username,
            "username field",
        )
        self.client._click_if_present(selectors.LOGIN_SUBMIT_BUTTONS, "username submit")
        self._wait_for_password_step()

    def _submit_password(self) -> None:
        filled = self._fill_field(
            selectors.PASSWORD_FIELDS,
            self.client.credentials.password,
            "password field",
            timeout=20,
            required=False,
        )
        if not filled:
            logger.info("Password field not shown separately; continuing")
            return

        self.client._click_if_present(selectors.LOGIN_SUBMIT_BUTTONS, "password submit")

    def _wait_for_password_step(self) -> None:
        self.client._require_driver()
        wait = WebDriverWait(self.client.driver, 15)
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
                field = self.client._find_visible(
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
            raise SapClientError(
                f"Could not fill {label}: page changed during login"
            ) from last_error
        return False

    def _wait_for_post_login(self) -> None:
        self.client._require_driver()
        wait = WebDriverWait(self.client.driver, self.client.timeout)
        try:
            wait.until(lambda driver: "login" not in driver.current_url.lower())
        except TimeoutException:
            logger.warning("Login redirect not detected; continuing anyway")

    def _set_input_value(self, element: WebElement, value: str) -> None:
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.DELETE)
        element.send_keys(value)
