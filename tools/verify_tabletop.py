"""Exercise real dice movement, persistent character pawns, board views and crowded tiles.
Requires the development server on localhost:8000, Python Playwright and system Chromium.
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]

async def complete_setup(page):
    await page.locator('#sStart').click()
    # Older release fixtures go straight to briefing; current releases use three steps.
    if await page.locator('#sSession').is_visible():
        await page.get_by_role('button',name='مراجعة الإعدادات',exact=True).click()
        await page.locator('#sLaunch').click()

async def start_game(page, eight=False):
    await page.goto('http://localhost:8000/', wait_until='networkidle')
    await page.locator('#wNew').click()
    await page.locator('[data-i="1"] [data-k="ctrl"]').select_option('local')
    await page.locator('[data-i="0"] [data-k="name"]').fill('محسن')
    await page.locator('[data-i="1"] [data-k="name"]').fill('مريم')
    for slot, profession in [(0, 0), (1, 11)]:
        await page.locator(f'[data-i="{slot}"] [data-k="profbtn"]').click()
        await page.locator(f'.pcard[data-p="{profession}"]').click()
    if eight:
        for _ in range(6):
            await page.locator('#sAdd').click()
    await complete_setup(page)
    await page.get_by_role('button', name='ابدأ المباراة 🎲', exact=True).click()
    for _ in range(15):
        await page.wait_for_timeout(200)
        if await page.locator('#roll').is_enabled():
            return
        buttons = page.locator('#modal.on #sheet button')
        if await buttons.count():
            await buttons.last.click()
    raise AssertionError('First turn did not become ready')

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        context = await browser.new_context(viewport={'width': 1180, 'height': 820})
        page = await context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        await start_game(page)
        assert await page.locator('.character-pawn').count() == 2
        assert await page.locator('.pawn-art[src$="#pawn_programmer"]').count() == 1
        assert await page.locator('.pawn-art[src$="#pawn_teacher"]').count() == 1
        assert await page.locator('.tabletop-deck').count() == 3
        assert await page.locator('#board').evaluate('(el) => getComputedStyle(el).transformStyle') == 'preserve-3d'
        # Seed opposite edges so the actual dice roll crosses the final/first tile boundary.
        await page.evaluate('''() => {
            __darb.G.players[0].pos=47;
            __darb.G.players[1].pos=20;
            document.querySelector('.chip-p[data-pid="0"]').click();
        }''')
        await page.wait_for_timeout(220)
        for width, height in [(360,800),(390,844),(768,1024),(1180,820)]:
            await page.set_viewport_size({'width':width,'height':height})
            await page.wait_for_timeout(220)
            await page.locator('[data-camera=reset]').click()
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            for pawn in await page.locator('.character-pawn').all():
                tile = int(await pawn.get_attribute('data-position'))
                assert await page.locator(f'[data-tile="{tile}"]').count() == 1
                assert await pawn.locator('img').evaluate('(el) => el.complete && el.naturalWidth > 0')
            if width == 390:
                await page.screenshot(path=str(ROOT/'brand/preview-tabletop-mobile.png'), full_page=True)
            if width == 1180:
                await page.locator('.tabletop-card').screenshot(path=str(ROOT/'brand/preview-tabletop.png'), style='.bar-actions,.react-fab,#toast{visibility:hidden!important}')
        for view in ['top', 'perspective']:
            await page.locator(f'[data-table-view="{view}"]').click()
            assert await page.locator('.tabletop-stage').get_attribute('data-view') == view
            assert await page.locator(f'[data-table-view="{view}"]').get_attribute('aria-pressed') == 'true'
        await page.evaluate('''() => {
            window.__pawnNode=document.querySelector('.character-pawn[data-player="0"]');
            window.__pawnSteps=[47];window.__pawnAnimations=0;window.__pawnTravel=0;
            window.__pawnObserver=new MutationObserver(() => {
                const node=window.__pawnNode;
                const pos=Number(node.dataset.position);
                if(pos!==__pawnSteps.at(-1)){
                    __pawnSteps.push(pos);
                    if(node.querySelector('img').getAnimations().length) __pawnAnimations++;
                    if(node.getAnimations().some(a=>a.transitionProperty==='transform')) __pawnTravel++;
                }
            });
            __pawnObserver.observe(__pawnNode,{attributes:true,attributeFilter:['data-position']});
        }''')
        await page.locator('#roll').click()
        await page.wait_for_function('__darb.G.dice2 && !__darb.G.rolling')
        dice = await page.evaluate('__darb.G.dice2.reduce((a,b)=>a+b,0)')
        await page.wait_for_function('(d) => __darb.G.players[0].pos === (47+d)%48', arg=dice)
        await page.wait_for_timeout(180)
        result = await page.evaluate('''() => ({
            steps:__pawnSteps, animations:__pawnAnimations, travel:__pawnTravel,
            sameNode:__pawnNode===document.querySelector('.character-pawn[data-player="0"]'),
            pawnPosition:Number(__pawnNode.dataset.position), gamePosition:__darb.G.players[0].pos
        })''')
        assert result['steps'] == [47] + [i % 48 for i in range(48, 48+dice)], result
        assert result['sameNode'] and result['animations'] > 0 and result['travel'] > 0, result
        assert result['pawnPosition'] == result['gamePosition']
        # Wait for the physical CSS transition, not a fixed wall-clock under browser load.
        await page.wait_for_function("""() => {
            const node=document.querySelector('.character-pawn[data-player="0"]');
            return !node.getAnimations().some(a=>a.playState==='running');
        }""")
        assert await page.locator('.character-pawn[data-player="0"]').evaluate('''(node) => {
            const tile=document.querySelector(`[data-tile="${node.dataset.position}"]`);
            const m=new DOMMatrix(getComputedStyle(node).transform);
            return Math.abs(m.m41-(tile.offsetLeft+tile.offsetWidth/2))<1 &&
                   Math.abs(m.m42-(tile.offsetTop+tile.offsetHeight*.65))<1;
        }''')
        # Rendering fixtures cover the shorter fast track without changing the engine's rules.
        await page.evaluate('''() => {
            __pawnObserver.disconnect();
            __darb.G.players[0].fast=true;__darb.G.players[0].pos=19;
            document.querySelector('.chip-p[data-pid="0"]').click();
        }''')
        assert await page.locator('#board .tile').count() == 20
        assert await page.locator('.character-pawn').count() == 1
        assert await page.locator('.character-pawn').get_attribute('data-position') == '19'
        await page.emulate_media(reduced_motion='reduce')
        await page.evaluate('''() => {
            __darb.G.players[0].pos=0;
            document.querySelector('.chip-p[data-pid="0"]').click();
        }''')
        assert await page.locator('.character-pawn').evaluate('(el) => el.getAnimations().filter(a=>a.playState==="running").length') == 0
        crowded = await browser.new_context(viewport={'width':390,'height':844})
        crowded_page = await crowded.new_page()
        crowded_page.on('pageerror', lambda error: errors.append(str(error)))
        await start_game(crowded_page, eight=True)
        assert await crowded_page.locator('.character-pawn').count() == 8
        positions = await crowded_page.locator('.character-pawn').evaluate_all('(nodes) => nodes.map(n=>n.style.transform)')
        assert len(set(positions)) == 8, positions
        assert await crowded_page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors, errors
        print(json.dumps({'real_dice_steps':dice,'wraparound_movement':'passed','persistent_pawn_nodes':'passed',
                          'selected_characters_including_hijabi':'passed','view_modes':2,'responsive_sizes':4,
                          'fast_track_20_tiles':'passed','eight_pawns_same_tile':'passed','reduced_motion':'passed',
                          'javascript_errors':errors}, ensure_ascii=False, indent=2))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(asyncio.wait_for(verify(), timeout=100))
