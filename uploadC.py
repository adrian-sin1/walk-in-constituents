from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from automation import (
    login, handle_disclaimer, click_create_new_constituent,
    fill_form, click_next_step, fill_details,
    select_intake_method, click_create_casework, click_home_button,
)

def get_first(row, keys, default=""):
    for k in keys:
        if k in row and str(row.get(k, "")).strip():
            return str(row.get(k, "")).strip()
    return default

def upload_to_council_connect(df, creds, driver_path):
    FIELD_MAP_STEP_1 = {
        "Name": "newConstituent.name",
        "Email": "newConstituent.contact_info.0.contact_data"
    }
    FORM_URL = "https://councilconnect.council.nyc.gov/casework/create"

    service = Service(driver_path)
    driver = webdriver.Edge(service=service)
    wait = WebDriverWait(driver, 30)

    def element_exists(drv, xpath):
        try:
            drv.find_element(By.XPATH, xpath)
            return True
        except NoSuchElementException:
            return False

    try:
        login(driver, wait, "https://councilconnect.council.nyc.gov/login", creds["username"], creds["password"])
        handle_disclaimer(driver, wait)

        for _, row in df.iterrows():
            first_name = get_first(row, ["First Name / 名", "First Name", "First"])
            last_name  = get_first(row, ["Last Name/ 姓", "Last Name", "Last"])
            full_name  = f"{first_name} {last_name}".strip()

            email   = get_first(row, ["Email / 电子邮件", "Email"])
            details = get_first(row, ["Issue - Case Notes", "Issue", "Case Notes"], default=".")

            if not full_name and not details:
                continue

            driver.get(FORM_URL)
            wait.until(lambda d: d.find_element(By.TAG_NAME, "form"))

            if not click_create_new_constituent(driver, wait):
                continue

            payload = {"Name": full_name}
            if email:
                payload["Email"] = email

            fill_form(driver, payload, FIELD_MAP_STEP_1)
            click_next_step(driver, wait)

            wait.until(lambda d: d.find_element(By.ID, "details"))
            if not details:
                details = "."
            if not fill_details(driver, wait, details):
                continue

            click_next_step(driver, wait)
            select_intake_method(driver, wait, "Walk in")

            now = datetime.now().strftime("%Y-%m-%dT%H:%M")
            opened_at_input = driver.find_element(By.ID, "opened_at")
            driver.execute_script("""
                const input = arguments[0];
                const value = arguments[1];
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(input, value);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, opened_at_input, now)

            click_next_step(driver, wait)
            click_next_step(driver, wait)

            if creds.get("auto_click"):
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Create Casework')]")))
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create Casework')]")))
                    click_create_casework(driver, wait)
                    time.sleep(3)
                    print(f"✅ Casework created for: {full_name}")
                except Exception as e:
                    print(f"❌ Auto-click failed for {full_name}: {e}")
                continue
            else:
                print("🛑 Please click 'Create Casework' manually in the browser...")
                while True:
                    if not element_exists(driver, "//button[contains(text(), 'Create Casework')]") and \
                       not element_exists(driver, "//button[contains(text(), 'Next Step')]"):
                        print(f"✅ Submitted: {full_name}")
                        break
                    if element_exists(driver, "//h2[contains(text(),'Create Casework')]"):
                        print(f"⏩ Skipped (back to Home): {full_name}")
                        time.sleep(2)
                        break
                    time.sleep(4)

    finally:
        driver.quit()
