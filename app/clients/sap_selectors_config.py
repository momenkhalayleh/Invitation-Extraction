import json
from functools import lru_cache
from pathlib import Path

from selenium.webdriver.common.by import By

_SELECTORS_FILE = Path(__file__).with_name("sap_selectors.json")
_BY_MAP = {
    "id": By.ID,
    "name": By.NAME,
    "xpath": By.XPATH,
    "css selector": By.CSS_SELECTOR,
}


@lru_cache(maxsize=1)
def _load_raw() -> dict:
    with _SELECTORS_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _to_locators(values: list[list[str]]) -> tuple[tuple[str, str], ...]:
    return tuple((_BY_MAP[by.lower()], selector) for by, selector in values)


_raw = _load_raw()

USERNAME_FIELDS = _to_locators(_raw["USERNAME_FIELDS"])
PASSWORD_FIELDS = _to_locators(_raw["PASSWORD_FIELDS"])
LOGIN_SUBMIT_BUTTONS = _to_locators(_raw["LOGIN_SUBMIT_BUTTONS"])
FIORI_SEARCH_TOGGLES = _to_locators(_raw["FIORI_SEARCH_TOGGLES"])
FIORI_SEARCH_FIELDS = _to_locators(_raw["FIORI_SEARCH_FIELDS"])
MANAGE_INQUIRIES_TILES = _to_locators(_raw["MANAGE_INQUIRIES_TILES"])
SALES_ENQUIRY_TARGETS = _to_locators(_raw["SALES_ENQUIRY_TARGETS"])
DATE_PICKER_TOGGLES = _to_locators(_raw["DATE_PICKER_TOGGLES"])
DATE_OK_BUTTONS = _to_locators(_raw["DATE_OK_BUTTONS"])
DATE_OPTION_YESTERDAY = _to_locators(_raw["DATE_OPTION_YESTERDAY"])
GO_BUTTONS = _to_locators(_raw["GO_BUTTONS"])
SALES_INQUIRY_LINKS = _to_locators(_raw["SALES_INQUIRY_LINKS"])
CHANGE_INQUIRY_LINKS = _to_locators(_raw["CHANGE_INQUIRY_LINKS"])
BACK_BUTTONS = _to_locators(_raw["BACK_BUTTONS"])
NEXT_PAGE_BUTTONS = _to_locators(_raw["NEXT_PAGE_BUTTONS"])
WEBGUI_ANCHORS = _to_locators(_raw["WEBGUI_ANCHORS"])
CUST_REFERENCE_LABELS = _to_locators(_raw["CUST_REFERENCE_LABELS"])
FORWARD_SCROLL_BUTTONS = _to_locators(_raw["FORWARD_SCROLL_BUTTONS"])
CUSTOM_FIELDS_TABS = _to_locators(_raw["CUSTOM_FIELDS_TABS"])
WEBGUI_FIELD_INPUTS = {
    field: _to_locators(locators) for field, locators in _raw["WEBGUI_FIELD_INPUTS"].items()
}
WEBGUI_LABEL_FRAGMENTS = {
    field: tuple(fragments) for field, fragments in _raw["WEBGUI_LABEL_FRAGMENTS"].items()
}
WEBGUI_LABEL_VALUE_FIELDS = frozenset(_raw["WEBGUI_LABEL_VALUE_FIELDS"])
