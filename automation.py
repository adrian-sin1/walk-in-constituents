import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login(driver, wait, login_url, username, password):
    driver.get(login_url)
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    wait.until(EC.url_changes(login_url))
    print("✅ Logged in")

def handle_disclaimer(driver, wait):
    print("⏳ Checking for disclaimer popup...")
    locators = [
        "//button[contains(text(),'Accept')]",
        "//button[contains(text(),'I Agree')]",
        "//button[contains(text(),'Continue')]",
        "//button[contains(text(),'OK')]",
        "//div[@aria-label='Disclaimer']//button"
    ]
    for xpath in locators:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            time.sleep(0.5)
            btn.click()
            print(f"✅ Clicked disclaimer button: {xpath}")
            return
        except:
            continue

    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            driver.switch_to.frame(frame)
            for xpath in locators:
                try:
                    btn = driver.find_element(By.XPATH, xpath)
                    btn.click()
                    driver.switch_to.default_content()
                    print("✅ Dismissed disclaimer in iframe")
                    return
                except:
                    continue
            driver.switch_to.default_content()
    except Exception as e:
        print(f"⚠️ Error checking iframes: {e}")
    print("ℹ️ No disclaimer popup found")

def click_create_casework_from_home(driver, wait):
    try:
        print("⏳ Looking for 'Create Casework' on Home screen...")
        button = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//h2[contains(text(),'Create Casework')]/ancestor::div[contains(@class,'css-1vg19me')]"
        )))
        time.sleep(1)
        button.click()
        print("✅ Clicked 'Create Casework' on Home screen.")
        return True
    except Exception as e:
        print(f"❌ Failed to click 'Create Casework' from Home: {e}")
        return False

def click_create_new_constituent(driver, wait):
    try:
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Create New Constituent')]"))
        ).click()
        print("✅ Clicked 'Create New Constituent'")
    except Exception as e:
        print(f"❌ Could not click 'Create New Constituent': {e}")
        return False

    time.sleep(1)
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "newConstituent.name")))
        print("✅ Form appeared")
        return True
    except Exception as e:
        print(f"❌ Form did not appear: {e}")
        return False

def fill_form(driver, row, field_map):
    for col, field_id in field_map.items():
        value = row.get(col, "")
        if pd.isna(value) or not value:
            continue
        try:
            field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, field_id)))
            field.clear()
            time.sleep(0.2)
            field.send_keys(str(value))
            print(f"✅ Filled '{col}'")
        except Exception as e:
            print(f"⚠️ Could not fill '{col}' in field '{field_id}': {e}")

def fill_details(driver, wait, body):
    try:
        wait.until(EC.presence_of_element_located((By.ID, "details")))
        time.sleep(1)

        script = """
        const textarea = document.getElementById('details');
        if (textarea) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeInputValueSetter.call(textarea, arguments[0]);
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """
        driver.execute_script(script, body)

        print("✅ Filled 'Details' with line breaks")
        return True

    except Exception as e:
        print(f"❌ Failed to fill 'Details': {e}")
        return False

def click_next_step(driver, wait):
    try:
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-pejez8')))
        time.sleep(0.5)
        next_btn.click()
        print("➡️ Clicked 'Next Step'")
    except Exception as e:
        print(f"⚠️ Could not click 'Next Step': {e}")

def select_intake_method(driver, wait, method_value="Emailed"):
    try:
        print(f"🔍 Selecting Intake Method: {method_value}")
        select_element = wait.until(EC.element_to_be_clickable((By.ID, "intake_method")))
        select_element.click()
        time.sleep(0.5)
        script = f"""
        var select = document.getElementById('intake_method');
        select.value = '{method_value}';
        var event = new Event('change', {{ bubbles: true }});
        select.dispatchEvent(event);
        """
        driver.execute_script(script)
        print("✅ Intake Method selected")
    except Exception as e:
        print(f"❌ Failed to select Intake Method: {e}")

def click_create_casework(driver, wait):
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Create Casework')]")
        ))
        btn.click()
        print("✅ Clicked 'Create Casework'")
    except Exception as e:
        print(f"❌ Could not click 'Create Casework': {e}")



    
def click_create_casework_from_home(driver, wait):
    try:
        print("⏳ Looking for 'Create Casework' button on Home screen...")
        button = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//h2[contains(text(),'Create Casework')]/ancestor::div[contains(@class,'css-1vgl9me')]"
        )))
        button.click()
        print("✅ Clicked 'Create Casework' on Home screen.")
        return True
    except Exception as e:
        print(f"❌ Failed to click 'Create Casework' from Home screen: {e}")
        return False
    
def click_home_button(driver, wait):
    try:
        print("⏮ Trying to click Home button...")

        # Use a slightly longer explicit wait
        short_wait = WebDriverWait(driver, 15)
        home_button = short_wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Home']"))
        )

        # Click via JavaScript
        driver.execute_script("arguments[0].click();", home_button)
        print("✅ Clicked Home button")

        # Wait for a known element on the Home page
        wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(),'Create Casework')]")))
        print("✅ Home page loaded")
        return True

    except Exception as e:
        print("❌ Could not click Home button:")
        print(f"   → {type(e).__name__}: {e}")
        return False