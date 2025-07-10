import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

load_dotenv()

EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")


async def select_category(
    page: Page,
    button_name: str,
    input: str,
):
    add_btn = page.get_by_role("button", name=button_name)  # ← unique aria-label
    await add_btn.wait_for(state="visible", timeout=10_000)
    await add_btn.click()

    # A. Grab the input you just pasted
    text_input = page.locator("#people-bar-graph-module-facet-search-input")

    # B. Type the cleaned-up location
    await text_input.fill(input)
    # 2️⃣  wait until the suggestions <ul> is visible
    suggestion_ul = page.locator("ul.artdeco-typeahead__results-list[role='listbox']")
    await suggestion_ul.wait_for(state="visible", timeout=10_000)

    # 3️⃣  click the *first* <li> inside that list
    first_li = suggestion_ul.locator("li.artdeco-typeahead__result").first
    await first_li.click()


async def get_job_data(page: Page):
    await page.wait_for_selector(
        ".job-details-jobs-unified-top-card__job-title",
        timeout=15_000,
    )

    title = (
        await page.locator(
            ".job-details-jobs-unified-top-card__job-title h1"
        ).inner_text()
    ).strip()
    company_name = (
        await page.locator(
            ".job-details-jobs-unified-top-card__company-name a"
        ).inner_text()
    ).strip()
    location = (
        (
            await page.locator(
                ".job-details-jobs-unified-top-card__tertiary-description-container"
                + " span"
            ).first.inner_text()
        )
        .split("·", 1)[0]
        .strip()
    )
    description = (await page.locator("#job-details").inner_text()).strip()

    job_data = {
        "title": title,
        "company": company_name,
        "location": location,
        "description": description,
    }

    return job_data


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

        kw_box = page.get_by_role("combobox", name="Search by title, skill, or company")
        await kw_box.wait_for(state="visible", timeout=10_000)

        # type “amazon” and commit the search
        await kw_box.fill("amazon")
        await page.keyboard.press("Enter")
        # if no card is selected, click the first one
        first_card = page.locator("ul.jobs-search__results-list li").first
        if await first_card.count() > 0:
            await first_card.click()
        # ── scrape the open job pane ──────────────────────────────────────
        job_data = await get_job_data(page)
        print(job_data["location"])
        # bundle into a dictionary and return it
        # return {
        #     "title": job_title,
        #     "company": company_name,
        #     "location": location,
        #     "description": description,
        # }
        # await page.wait_for_timeout(1_000_000)  # wait for the page to load
        await page.wait_for_selector(
            'div.job-details-jobs-unified-top-card__company-name a[href*="/company/"]',
            timeout=10_000,
        )

        await page.click(
            'div.job-details-jobs-unified-top-card__company-name a[href*="/company/"]'
        )

        # ── D.  Confirm you’re on the company page ───────────────────────
        await page.wait_for_url("**/company/**", timeout=15_000)

        people_link = page.locator(
            "a.org-page-navigation__item-anchor:has-text('People')"
        )

        await people_link.click()
        # ── click the “Add any location” button ──────────────────────────────
        await select_category(
            page,
            button_name="Add any location",
            input=job_data["location"],
        )
        await select_category(
            page,
            button_name="Add any school",
            input="UCSD",
        )
        await page.click('button[aria-label="Next"]')
        # wait until at least one bar that contains "Engineering" is in the DOM
        await page.wait_for_selector(
            "button.org-people-bar-graph-element:has-text('Engineering')",
            timeout=10_000,
        )
        eng_btn = page.locator(
            "button.org-people-bar-graph-element:has-text('Engineering')"
        ).first  # .first enforces strict-mode uniqueness
        await eng_btn.wait_for(state="visible")
        await eng_btn.click()
        # await select_category(
        #     page,
        #     button_name="Add any field of study",
        #     input="Computer Engineering",
        # )
        await page.wait_for_timeout(timeout=1_000_000)
        await browser.close()

        return job_data


job_data = asyncio.run(main())
title = job_data["title"]
company = job_data["company"]
location = job_data["location"]
description = job_data["description"]

# do whatever you need with them
print(title, company, location, sep=" | ")
print(description)
