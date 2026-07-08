"""SAP Fiori / Cloud Identity selector fallbacks.

Update these selectors once the live SAP screens are confirmed during Step 4.
"""

from selenium.webdriver.common.by import By

# Login — SAP Cloud Identity (username step)
USERNAME_FIELDS = (
    (By.ID, "j_username"),
    (By.NAME, "j_username"),
    (By.NAME, "UserName"),
    (By.CSS_SELECTOR, "input[type='email']"),
    (By.CSS_SELECTOR, "input[name='username']"),
)

# Login — password step (may appear on same page or a follow-up screen)
PASSWORD_FIELDS = (
    (By.ID, "j_password"),
    (By.NAME, "j_password"),
    (By.NAME, "Password"),
    (By.CSS_SELECTOR, "input[type='password']"),
)

LOGIN_SUBMIT_BUTTONS = (
    (By.CSS_SELECTOR, "button[type='submit']"),
    (By.ID, "logOnFormSubmit"),
    (By.CSS_SELECTOR, "input[type='submit']"),
    (By.XPATH, "//button[contains(., 'Continue') or contains(., 'Log') or contains(., 'Sign')]"),
)

# Fiori launchpad shell search toggle (magnifier button that reveals the search input)
FIORI_SEARCH_TOGGLES = (
    (By.ID, "sf"),
    (By.CSS_SELECTOR, "#shell-header [aria-label*='Search']"),
    (By.CSS_SELECTOR, "button[title='Search']"),
    (By.CSS_SELECTOR, "[id$='-search']"),
)

# Fiori launchpad shell search input (visible after toggle is clicked)
FIORI_SEARCH_FIELDS = (
    (By.ID, "searchFieldInShell-input"),
    (By.CSS_SELECTOR, "#searchFieldInShell input"),
    (By.CSS_SELECTOR, "input[id*='searchFieldInShell']"),
    (By.CSS_SELECTOR, "input[aria-label*='Search']"),
    (By.CSS_SELECTOR, "input[placeholder*='Search']"),
)

# Manage Sales Inquiries app tile on the launchpad home (favorites section)
MANAGE_INQUIRIES_TILES = (
    (By.ID, "favApps-app-0-tile"),
    (By.CSS_SELECTOR, "[id*='favApps'][id$='-tile']"),
)

# Manage Sales Enquiries tile / search result (fallback via shell search)
SALES_ENQUIRY_TARGETS = (
    (By.ID, "favApps-app-0-tile"),
    (By.XPATH, "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'manage sales inquir')]"),
    (By.XPATH, "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'manage sales enquir')]"),
    (By.XPATH, "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sales inquir')]"),
)

# Document Date picker toggle (calendar button on the List Report filter bar)
DATE_PICKER_TOGGLES = (
    (By.XPATH, "//span[@title='Open Picker']"),
    (By.CSS_SELECTOR, "span[title='Open Picker']"),
    (By.XPATH, "//button[@title='Open Picker']"),
)

# Confirmation button inside the date picker popover
DATE_OK_BUTTONS = (
    (By.XPATH, "//button[.//bdi[normalize-space(text())='OK']]"),
    (By.XPATH, "//bdi[normalize-space(text())='OK']/ancestor::button"),
    (By.CSS_SELECTOR, "button[id*='-OK']"),
)

# Date filters — From/To inputs shown after choosing the "From / To" option
DATE_FROM_FIELDS = (
    (By.CSS_SELECTOR, "input[placeholder*='From']"),
    (By.XPATH, "//div[contains(@class,'sapMDDR')]//input[1]"),
    (By.XPATH, "//label[contains(., 'From') or contains(., 'Start')]/following::input[1]"),
    (By.CSS_SELECTOR, "input[id*='from' i]"),
)

DATE_TO_FIELDS = (
    (By.CSS_SELECTOR, "input[placeholder*='To']"),
    (By.XPATH, "//div[contains(@class,'sapMDDR')]//input[2]"),
    (By.XPATH, "//label[contains(., 'To') or contains(., 'End')]/following::input[1]"),
    (By.CSS_SELECTOR, "input[id*='to' i]"),
)

GO_BUTTONS = (
    (By.XPATH, "//bdi[contains(@id,'btnGo-BDI-content')]/ancestor::button"),
    (By.XPATH, "//bdi[normalize-space(text())='Go']/ancestor::button"),
    (By.XPATH, "//button[.//bdi[normalize-space(text())='Go']]"),
    (By.XPATH, "//button[contains(., 'Go')]"),
    (By.CSS_SELECTOR, "button[id*='Go' i]"),
)

# Sales Inquiry links in the List Report results table (each opens an Object Page)
SALES_INQUIRY_LINKS = (
    (By.XPATH, "//td[contains(@data-sap-ui-column,'listReport-SalesInquiry')]//a"),
    (By.XPATH, "//td[contains(@data-sap-ui-column,'SalesInquiry')]//a"),
)

# "Change Sales Inquiries" link on the Object Page (enters the editable detail view)
CHANGE_INQUIRY_LINKS = (
    (By.XPATH, "//a[.//span[normalize-space()='Change Sales Inquiries']]"),
    (By.XPATH, "//a[normalize-space()='Change Sales Inquiries']"),
)

# Results list rows
RESULT_ROWS = (
    (By.CSS_SELECTOR, "tr[data-sap-ui-rowindex]"),
    (By.CSS_SELECTOR, "[role='row'][aria-rowindex]"),
    (By.CSS_SELECTOR, "tbody tr"),
    (By.CSS_SELECTOR, ".sapUiTableTr"),
)

# Navigation
BACK_BUTTONS = (
    (By.CSS_SELECTOR, "[aria-label='Back']"),
    (By.XPATH, "//button[@title='Back']"),
    (By.XPATH, "//bdi[normalize-space(text())='Back']/ancestor::button"),
)

NEXT_PAGE_BUTTONS = (
    (By.CSS_SELECTOR, "[title='Next Page']"),
    (By.CSS_SELECTOR, "[aria-label*='Next']"),
    (By.XPATH, "//button[contains(@aria-label,'Next')]"),
)

# ---------------------------------------------------------------------------
# SAP GUI for HTML (WebGUI) — Change Sales Inquiries page.
# NOTE: element IDs like "M0:46:1::3:17" are dynamic per session; prefer
# title / text / action attributes over IDs.
# ---------------------------------------------------------------------------

# Anchor used to detect we are inside the WebGUI change view (and its iframe).
# The access key splits the label text ("C" + "ust. Reference"), so match a
# substring that avoids the first letter.
WEBGUI_ANCHORS = (
    (By.CSS_SELECTOR, "input[title='Customer Reference']"),
    (By.XPATH, "//label[contains(normalize-space(.), 'ust. Reference')]"),
    (By.XPATH, "//span[contains(@class,'lsDynproTextField__text') and contains(normalize-space(.), 'ust. Reference')]"),
)

# Label text fragments for WebGUI fields (access keys split the first letter).
WEBGUI_LABEL_FRAGMENTS: dict[str, tuple[str, ...]] = {
    "customer_ref": ("ust. Reference", "Customer Reference", "Cust. Reference"),
}

CUST_REFERENCE_LABELS = (
    (By.XPATH, "//label[contains(normalize-space(.), 'ust. Reference')]"),
    (By.XPATH, "//label[contains(normalize-space(.), 'Customer Reference')]"),
    (By.XPATH, "//span[contains(@class,'lsDynproTextField__text') and contains(normalize-space(.), 'ust. Reference')]/ancestor::label[1]"),
)

# Fallback input locators (title may differ from visible label text).
CUST_REFERENCE_INPUT = (
    (By.CSS_SELECTOR, "input[title='Customer Reference']"),
    (By.CSS_SELECTOR, "input[title='Cust. Reference']"),
)

# "Forward" scroll button that reveals additional tab-strip items
FORWARD_SCROLL_BUTTONS = (
    (By.CSS_SELECTOR, "span[action='SCROLL_TO_NEXT_ITEMS']"),
    (By.CSS_SELECTOR, "span[title='Forward']"),
    (By.CSS_SELECTOR, "span[id$='-next']"),
)

# "Custom Fields" tab in the tab strip
CUSTOM_FIELDS_TABS = (
    (By.XPATH, "//span[contains(@class,'lsTabStrip--item-text') and normalize-space(text())='Custom Fields']"),
    (By.XPATH, "//span[normalize-space(text())='Custom Fields']"),
)

# Stable WebGUI field locators (SID fragments survive dynamic element IDs).
WEBGUI_FIELD_INPUTS: dict[str, tuple[tuple, ...]] = {
    "customer_ref": (
        (By.CSS_SELECTOR, "input[title='Customer Reference']"),
    ),
    "customer_name": (
        (By.XPATH, "//label[contains(@lsdata,'txtKUAGV-TXTPA')]"),
        (By.XPATH, "//input[@title='Sold-to Party']/following::label[@title][1]"),
    ),
    "scope_of_work": (
        (By.XPATH, "//input[contains(@lsdata,'subSUBSCREEN_7') and contains(@lsdata,'LIST_FIELD_VALUE')]"),
        (By.CSS_SELECTOR, "input[title='Code']"),
    ),
    "inv_subject": (
        (By.XPATH, "//input[contains(@lsdata,'subSUBSCREEN_2') and contains(@lsdata,'NUMERICAL_TEXT_FIELD_VALUE')]"),
        (By.CSS_SELECTOR, "input[title='Numerical Text']"),
    ),
    "product_type": (
        (By.XPATH, "//input[contains(@lsdata,'subSUBSCREEN_20') and contains(@lsdata,'ASSOCIATION_FIELD_VALUE')]"),
        (By.CSS_SELECTOR, "input[title='Association']"),
    ),
    "closing_date": (
        (By.XPATH, "//input[contains(@lsdata,'subSUBSCREEN_4') and contains(@lsdata,'DATE_FIELD_VALUE')]"),
        (By.CSS_SELECTOR, "input[title='Date']"),
    ),
}

# Fields whose value lives on a label/title attribute rather than an input value.
WEBGUI_LABEL_VALUE_FIELDS = frozenset({"customer_name"})
