import logging

from playwright.async_api import async_playwright, Page

from models import BeanData

logger = logging.getLogger(__name__)

BEANCONQUEROR_URL = "https://beanconqueror.com/create/"


async def fill_form(bean: BeanData):
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(BEANCONQUEROR_URL, wait_until="networkidle", timeout=30000)

    await _dismiss_cookie_banner(page)
    await _fill_general(page, bean)
    await _fill_roast(page, bean)
    await _fill_bean_details(page, bean)
    await _fill_varieties(page, bean)
    await _fill_notes(page, bean)

    await page.evaluate("document.querySelector('#beanForm').scrollIntoView()")
    logger.info("Form filled for '%s'. Browser remains open.", bean.coffee_name)


async def fill_and_submit(bean: BeanData) -> str:
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(BEANCONQUEROR_URL, wait_until="networkidle", timeout=30000)

    await _dismiss_cookie_banner(page)
    await _fill_general(page, bean)
    await _fill_roast(page, bean)
    await _fill_bean_details(page, bean)
    await _fill_varieties(page, bean)
    await _fill_notes(page, bean)

    await page.click('button[type="submit"]')
    await page.wait_for_selector("#resultsArea:not(.hidden)", timeout=10000)

    link = await page.inner_text("#generatedLinkDisplay")
    logger.info("Generated import link for '%s'", bean.coffee_name)
    return link


async def _dismiss_cookie_banner(page: Page):
    try:
        btn = page.locator("#cookieRejectAll")
        if await btn.is_visible(timeout=2000):
            await btn.click()
    except Exception:
        pass


async def _fill_general(page: Page, bean: BeanData):
    await _fill_input(page, 'input[name="coffeeName"]', bean.coffee_name)
    if bean.roaster:
        await _fill_input(page, 'input[name="roaster"]', bean.roaster)
    if bean.roasting_date:
        await _fill_input(page, 'input[name="roastingDate"]', bean.roasting_date)
    if bean.website:
        await _fill_input(page, 'input[name="website"]', bean.website)


async def _fill_roast(page: Page, bean: BeanData):
    if bean.bean_roasting_type:
        await _select_option(page, 'select[name="beanRoastingType"]', bean.bean_roasting_type.value)
    if bean.roast:
        await _select_option(page, 'select[name="roast"]', bean.roast.value)
    if bean.roast_custom:
        await _fill_input(page, 'input[name="roastCustom"]', bean.roast_custom)
    if bean.degree_of_roast is not None:
        await _fill_input(page, 'input[name="degreeOfRoast"]', str(bean.degree_of_roast))
    if bean.bean_mix:
        await _select_option(page, 'select[name="beanMix"]', bean.bean_mix.value)


async def _fill_bean_details(page: Page, bean: BeanData):
    if bean.weight is not None:
        await _fill_input(page, 'input[name="weight"]', str(bean.weight))
    if bean.cost is not None:
        await _fill_input(page, 'input[name="cost"]', str(bean.cost))
    if bean.ean_article:
        await _fill_input(page, 'input[name="eanArticle"]', bean.ean_article)
    if bean.flavour_profile:
        await _fill_input(page, 'input[name="flavourProfile"]', bean.flavour_profile)
    if bean.cupping_points:
        await _fill_input(page, 'input[name="cuppingPoints"]', bean.cupping_points)
    if bean.decaffeinated:
        await page.check('input[name="decaffeinated"]')


async def _fill_varieties(page: Page, bean: BeanData):
    if not bean.varieties:
        return

    for i, variety in enumerate(bean.varieties):
        if i > 0:
            await page.click("#addVarietyBtn")
            await page.wait_for_timeout(300)

        items = page.locator(".variety-item")
        item = items.nth(i)

        if variety.country:
            await item.locator('[name="variety_country"]').fill(variety.country)
        if variety.region:
            await item.locator('[name="variety_region"]').fill(variety.region)
        if variety.farm:
            await item.locator('[name="variety_farm"]').fill(variety.farm)
        if variety.farmer:
            await item.locator('[name="variety_farmer"]').fill(variety.farmer)
        if variety.variety:
            await item.locator('[name="variety_variety"]').fill(variety.variety)
        if variety.processing:
            await item.locator('[name="variety_processing"]').fill(variety.processing)
        if variety.elevation:
            await item.locator('[name="variety_elevation"]').fill(variety.elevation)
        if variety.harvest_time:
            await item.locator('[name="variety_harvestTime"]').fill(variety.harvest_time)
        if variety.certification:
            await item.locator('[name="variety_certification"]').fill(variety.certification)
        if variety.percentage is not None:
            await item.locator('[name="variety_percentage"]').fill(str(variety.percentage))


async def _fill_notes(page: Page, bean: BeanData):
    if bean.notes:
        await _fill_input(page, 'textarea[name="notes"]', bean.notes)


async def _fill_input(page: Page, selector: str, value: str):
    await page.fill(selector, "")
    await page.fill(selector, value)


async def _select_option(page: Page, selector: str, value: str):
    await page.select_option(selector, value)
