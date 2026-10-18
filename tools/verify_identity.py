"""Functional identity check. Run with Python Playwright and system Chromium.
Start: python3 -m http.server 8000 --bind 127.0.0.1
Check: python3 tools/verify_identity.py --base-url http://localhost:8000
"""
import argparse
import asyncio
import json
from urllib.request import urlopen
from playwright.async_api import async_playwright

async def verify(base_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path='/usr/bin/chromium', headless=True,
            args=['--no-sandbox'])
        context = await browser.new_context(viewport={'width': 390, 'height': 844})
        page = await context.new_page()
        page.set_default_timeout(15000)
        errors, missing = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: missing.append(response.url) if response.status >= 400 else None)
        await page.goto(base_url + '/', wait_until='networkidle')
        await page.evaluate('document.fonts.ready')
        if await page.locator('#hClose').is_visible():
            await page.locator('#hClose').click()
        # Overflow checks cover a small phone, regular phone, tablet, and desktop.
        for width, height in [(360, 800), (390, 844), (768, 1024), (1180, 820), (1440, 1000)]:
            await page.set_viewport_size({'width': width, 'height': height})
            await page.wait_for_timeout(250)
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, height)
            assert await page.locator('#wNew').is_visible()
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.locator('#wHow').click()
        assert await page.locator('#hClose').is_visible()
        await page.locator('#hClose').click()
        await page.locator('#wNew').click()
        await page.locator('[data-i="0"] [data-k="profbtn"]').click()
        portraits = page.locator('.pcard img')
        assert await portraits.count() == 14
        for image in await portraits.all():
            assert await image.evaluate('(el) => el.complete && el.naturalWidth > 0 && getComputedStyle(el).backgroundImage.includes("characters-sheet.png")')
            assert await image.get_attribute('alt')
        await page.locator('.pcard[data-p="0"]').click()
        await page.locator('#sStart').click()
        await page.get_by_role('button', name='ابدأ المباراة 🎲', exact=True).click()
        # First-year budget contains actual gameplay choices before the first roll.
        for _ in range(15):
            await page.wait_for_timeout(200)
            if await page.locator('#roll').is_enabled():
                break
            buttons = page.locator('#modal.on #sheet button')
            if await buttons.count():
                await buttons.last.click()
        await page.wait_for_function('!document.querySelector("#roll").disabled')
        assert await page.evaluate('__darb.G.players.length') == 2
        assert await page.locator('#board .tile').count() == 48
        assert await page.locator('#board .tile .board-miniature').count() == 48
        assert await page.locator('#goodsCard .gcell img').count() == 6
        assert await page.locator('#board .character-pawn').count() == 2
        await page.locator('#roll').click()
        await page.wait_for_function('__darb.G.dice2 && !__darb.G.rolling')
        assert await page.evaluate('__darb.G.dice2.every(n => n >= 1 && n <= 6)')
        await page.reload(wait_until='networkidle')
        assert await page.evaluate('!!__darb.G && __darb.G.players.length === 2')
        # Inspect full financial card and both color schemes after transitions settle.
        await page.locator('#tabs [data-t="me"]').click()
        assert await page.locator('#who .portrait').is_visible()
        for scheme in ['light', 'dark']:
            await page.emulate_media(color_scheme=scheme)
            await page.wait_for_timeout(300)
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.emulate_media(color_scheme='light')
        await page.locator('#tabs [data-t="play"]').click()
        await page.evaluate('navigator.serviceWorker.ready.then(() => true)')
        await page.wait_for_function('navigator.serviceWorker.controller !== null')
        cached = await page.evaluate('''async () => {
            const keys = await caches.keys();
            const cache = await caches.open('darb-solid-miniatures-v8');
            return {keys, urls: (await cache.keys()).map(r => r.url)};
        }''')
        assert 'darb-solid-miniatures-v8' in cached['keys']
        for asset in ['styles/models.css', 'scripts/models.js', 'styles/illustrated.css', 'scripts/identity.js', 'art/identity/icons-sheet.png', 'art/identity/cards-sheet.png', 'art/identity/reactions-sheet.png', 'styles/identity.css', 'fonts/Tajawal-Regular.ttf', 'fonts/Tajawal-Bold.ttf',
                      'art/identity/world-sheet.png', 'art/identity/characters-sheet.png',
                      'art/identity/goods-sheet.png', 'icons/game-icons.svg',
                      'styles/tabletop.css', 'scripts/tabletop.js',
                      'art/identity/pawns-sheet.png', 'art/identity/tabletop-park.png',
                      'scripts/board-camera.js', 'art/identity/tabletop-city.png']:
            assert any(url.endswith(asset) for url in cached['urls']), asset
        await context.set_offline(True)
        await page.reload(wait_until='networkidle')
        assert await page.evaluate('!!__darb.G')
        assert await page.locator('#board .tile').count() == 48
        assert 'Tajawal' in await page.locator('body').evaluate('(el) => getComputedStyle(el).fontFamily')
        await context.set_offline(False)
        await page.goto(base_url + '/brand/', wait_until='networkidle')
        assert await page.locator('.character-grid img').count() == 14
        assert await page.locator('.icon-grid .ui-icon').count() == 32
        for link in await page.locator('a[download]').all():
            url = await link.evaluate('(el) => el.href')
            with urlopen(url) as response:
                assert response.status == 200, url
        assert not errors, errors
        assert not missing, missing
        print(json.dumps({'responsive_sizes': 5, 'profession_portraits': 14, 'goods': 6,
                          'board_tiles_and_3d_models': 48, 'ui_icon_library': 32,
                          'dice_roll': 'passed', 'save_reload': 'passed',
                          'offline_with_new_identity': 'passed', 'light_and_dark': 'passed',
                          'brand_downloads': 'passed', 'javascript_errors': errors,
                          'http_errors': missing}, ensure_ascii=False, indent=2))
        await browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://localhost:8000')
    arguments = parser.parse_args()
    asyncio.run(asyncio.wait_for(verify(arguments.base_url.rstrip('/')), timeout=100))
