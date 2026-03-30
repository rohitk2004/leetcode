import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def login_leetcode(email, password):
    print(f"Attempting to log in to LeetCode with user ID: {email}")
    options = uc.ChromeOptions()
    # Not using headless mode to avoid cloudflare blocking
    driver = uc.Chrome(options=options)
    
    try:
        driver.get("https://leetcode.com/accounts/login/")
        
        wait = WebDriverWait(driver, 20)
        
        # Locating the email input
        email_input = wait.until(EC.presence_of_element_located((By.ID, "id_login")))
        email_input.clear()
        email_input.send_keys(email)
        print("Entered email.")
        
        # Locating the password input
        password_input = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
        password_input.clear()
        password_input.send_keys(password)
        print("Entered password.")
        
        time.sleep(1) # a small delay to mimic human behavior
        
        # Locating the signin button
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "signin_btn")))
        login_button.click()
        print("Clicked Sign In button. Waiting for page to load...")
        
        # We'll wait a significant time as LeetCode might have Captcha or Cloudflare checks
        time.sleep(15)
        
        # Check if we are still on the login page
        if "login" not in driver.current_url:
            print("Successfully logged in! You can now let the bot perform other tasks.")
        else:
            print("Login may have failed, or there is a Captcha to solve. Please check the browser.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Keep the connection open for a bit so you can see if you logged in explicitly or solve the Captcha
        time.sleep(20)
        print("Closing the browser.")
        driver.quit()

if __name__ == "__main__":
    EMAIL = "faxaw76745@exespay.com"
    PASSWORD = "Rohit@123321"
    
    login_leetcode(EMAIL, PASSWORD)
