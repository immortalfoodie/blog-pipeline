import os
import sys
import time
import argparse
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─── CONFIG (set via environment variables or edit here) ─────────────────────
DEVTO_EMAIL    = os.getenv("DEVTO_EMAIL", "your_email@example.com")
DEVTO_PASSWORD = os.getenv("DEVTO_PASSWORD", "your_password")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key")
GEMINI_MODEL   = "gemini-2.0-flash"
BLOG_TOPIC     = os.getenv("BLOG_TOPIC", "Python automation tips for beginners")
# ─────────────────────────────────────────────────────────────────────────────


def generate_blog_content(topic: str) -> dict:
    """Return a static blog post (used when AI quota is exhausted)."""
    print(f"[Content] Using static blog content for topic: '{topic}'")
    title = f"Getting Started with {topic}"
    body = f"""## Introduction

This blog post covers: **{topic}**

## Why This Matters

Automation is transforming how developers work. By combining tools like Selenium, 
Jenkins, and Python, we can build powerful pipelines that save hours of manual effort.

## Key Takeaways

- Selenium handles browser automation reliably across platforms
- Jenkins provides scheduling and CI/CD pipeline management  
- Python ties everything together with clean, readable code
- End-to-end automation reduces human error and increases consistency

## Getting Started

1. Install the required dependencies
2. Configure your credentials securely via environment variables
3. Test locally before connecting to Jenkins
4. Use Jenkins parameters for flexible on-demand and scheduled runs

## Conclusion

Building automation pipelines is a valuable skill. Start small, test often, 
and iterate. Tools like Selenium and Jenkins make it accessible for everyone.

*Posted automatically via Selenium + Jenkins pipeline.*
"""
    return {"title": title, "body": body}

def get_driver(headless: bool = False) -> webdriver.Chrome:
    """Launch Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def login(driver: webdriver.Chrome):
    """Log in to Dev.to using email/password."""
    print("[Selenium] Navigating to Dev.to login page ...")
    driver.get("https://dev.to/enter")
    wait = WebDriverWait(driver, 40)

    email_selector = "input#email, input[type='email'], input[name='email'], input[name='user[email]']"
    password_selector = "input#password, input[type='password'], input[name='password'], input[name='user[password]']"

    def wait_for_login_inputs(timeout: int):
        local_wait = WebDriverWait(driver, timeout)
        email_input = local_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, email_selector)))
        password_input = local_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, password_selector)))
        return email_input, password_input

    # New Dev.to login usually shows email/password directly.
    try:
        email_field, pw_field = wait_for_login_inputs(timeout=8)
    except TimeoutException:
        print("[Selenium] Direct login form not visible. Trying email-login button fallback ...")
        email_trigger_xpath = (
            "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue with email') "
            "or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]"
            " | "
            "//a[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue with email') "
            "or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'email')]"
        )
        email_btn = wait.until(EC.element_to_be_clickable((By.XPATH, email_trigger_xpath)))
        driver.execute_script("arguments[0].click();", email_btn)
        time.sleep(1)
        email_field, pw_field = wait_for_login_inputs(timeout=15)

    email_field.clear()
    email_field.send_keys(DEVTO_EMAIL)

    pw_field.clear()
    pw_field.send_keys(DEVTO_PASSWORD)
    pw_field.send_keys(Keys.RETURN)

    # Confirm by leaving the sign-in page.
    wait.until(lambda d: "/enter" not in d.current_url and "/users/sign_in" not in d.current_url)
    print("[Selenium] Login successful!")


def create_new_post(driver: webdriver.Chrome, title: str, body: str):
    """Open the new post editor and fill in title + body."""
    print("[Selenium] Opening new post editor ...")
    driver.get("https://dev.to/new")
    wait = WebDriverWait(driver, 20)
    time.sleep(2)

    # Enter title
    title_field = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "textarea#article_title, input#article_title, [placeholder*='title' i]")
    ))
    title_field.click()
    title_field.clear()
    title_field.send_keys(title)
    time.sleep(1)

    # Enter body (click in the editor area and type)
    body_area = driver.find_element(
        By.CSS_SELECTOR, ".CodeMirror, #article_body_markdown, [data-testid='article-form-body']"
    )
    body_area.click()
    time.sleep(0.5)

    # Use JS to set CodeMirror content if it's a CodeMirror editor
    try:
        driver.execute_script("""
            var cm = document.querySelector('.CodeMirror').CodeMirror;
            cm.setValue(arguments[0]);
        """, body)
    except Exception:
        # Fallback: send_keys directly
        body_area.send_keys(body)

    time.sleep(1)
    print("[Selenium] Post content filled in.")


def preview_and_approve(driver: webdriver.Chrome) -> bool:
    """Show preview and ask user for manual approval."""
    print("\n" + "="*60)
    print("PREVIEW MODE: Blog post is ready in the browser.")
    print("Please review the content at:", driver.current_url)
    print("="*60)
    answer = input("\nApprove and publish? [yes/no]: ").strip().lower()
    return answer in ("yes", "y")


def publish_post(driver: webdriver.Chrome):
    """Click the Publish button on Dev.to."""
    wait = WebDriverWait(driver, 20)
    print("[Selenium] Publishing post ...")

    # Find and click Publish button
    publish_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Publish') and not(contains(text(),'Save'))]")
    ))
    publish_btn.click()
    time.sleep(3)
    print(f"[Selenium] Post published! Current URL: {driver.current_url}")


def run(mode: str = "auto", headless: bool = False):
    """Main pipeline runner."""
    # Step 1: Generate content via AI
    content = generate_blog_content(BLOG_TOPIC)

    # Step 2: Launch browser
    driver = get_driver(headless=headless)

    try:
        # Step 3: Log in
        login(driver)

        # Step 4: Create new post
        create_new_post(driver, content["title"], content["body"])

        # Step 5: Preview or auto-publish
        if mode == "preview":
            approved = preview_and_approve(driver)
            if approved:
                publish_post(driver)
            else:
                print("[Pipeline] Publishing cancelled by user.")
        else:
            publish_post(driver)

    finally:
        time.sleep(2)
        driver.quit()
        print("[Pipeline] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dev.to Blog Auto-Publisher")
    parser.add_argument(
        "--mode", choices=["auto", "preview"], default="auto",
        help="'auto' = publish directly, 'preview' = wait for manual approval"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run Chrome in headless mode (for Jenkins/server use)"
    )
    args = parser.parse_args()
    run(mode=args.mode, headless=args.headless)
