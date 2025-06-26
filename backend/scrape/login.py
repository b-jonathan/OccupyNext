import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

load_dotenv()

EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/login", timeout=60_000)
        # 2. Fill credentials
        await page.fill('input[name="session_key"]', EMAIL)
        await page.fill('input[name="session_password"]', PASSWORD)

        # 3. Submit
        await page.click('button[type="submit"]')

        # 4. Wait for successful login signal (your avatar shows up)
        await page.wait_for_selector("img.global-nav__me-photo", timeout=60_000)

        await page.click('a[href*="/jobs/"]')

        try:
            show_all_link = page.locator('a:has-text("Show all")')
            await show_all_link.wait_for(timeout=30_000)  # fails if link never loads
            print(" Jobs page loaded!")
        except PlaywrightTimeout:
            print(" Jobs page took too long; check if a captcha popped up.")

        await page.click('a:has-text("Show all")')

        await page.wait_for_selector(
            'div.job-details-jobs-unified-top-card__company-name a[href*="/company/"]',
            timeout=10_000,
        )

        await page.click(
            'div.job-details-jobs-unified-top-card__company-name a[href*="/company/"]'
        )

        # ── D.  Confirm you’re on the company page ───────────────────────
        await page.wait_for_url("**/company/**", timeout=15_000)

        people_link = page.locator('a:has-text("People")')
        await people_link.click()
        await page.wait_for_timeout(30_000)  # 30 s idle
        await browser.close()


asyncio.run(main())
