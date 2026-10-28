"""Exercise native mouse/touch camera gestures and read-only board inspection."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from verify_tabletop import start_game

ROOT = Path(__file__).resolve().parents[1]

async def camera_state(page):
    return await page.locator('.tabletop-stage').evaluate('''stage => {
        const m=new DOMMatrix(stage.querySelector('.tabletop-camera-world').style.transform);
        return {zoom:Number(stage.dataset.zoom),follow:stage.dataset.follow,x:m.m41,y:m.m42};
    }''')

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        context = await browser.new_context(viewport={'width':1180,'height':820})
        page = await context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        await start_game(page)
        stage=page.locator('.tabletop-stage')
        before=await page.evaluate('JSON.stringify(__darb.G)')
        await page.locator('.tile.landmark').first.click()
        inspector=page.locator('#board-inspector')
        assert await inspector.is_visible()
        assert await inspector.locator('h2').inner_text() == 'مقهى الحي'
        assert 'الدفعة الأولى' in await inspector.locator('dl').inner_text()
        await page.keyboard.press('Escape')
        assert not await inspector.is_visible()
        # Keyboard inspection works independently of a tile's current projected size.
        await page.locator('[data-deck="family"]').focus()
        await page.keyboard.press('Enter')
        assert await inspector.locator('h2').inner_text() == 'بطاقات العائلة'
        await inspector.get_by_role('button',name='العودة إلى اللوحة').click()
        assert await page.evaluate('JSON.stringify(__darb.G)') == before
        await page.locator('[data-camera=in]').click()
        assert (await camera_state(page))['zoom'] == 125
        await page.locator('[data-camera=in]').click()
        assert await page.locator('#board').evaluate('(b)=>Math.abs(b.offsetWidth-b.offsetHeight)<2')
        rect=await stage.bounding_box()
        x=rect['x']+rect['width']/2;y=rect['y']+rect['height']/2
        start=await camera_state(page)
        await page.mouse.move(x,y);await page.mouse.down()
        await page.mouse.move(x+70,y+35,steps=8);await page.mouse.up()
        dragged=await camera_state(page)
        assert abs(dragged['x']-start['x'])>30 and dragged['follow']=='false', dragged
        assert not await inspector.is_visible(), 'Dragging must not open a tile'
        await page.mouse.move(x,y);await page.mouse.wheel(0,-100)
        await page.wait_for_timeout(120)
        assert (await camera_state(page))['zoom'] > dragged['zoom']
        visible=await stage.evaluate("""stage => {
            const r=stage.getBoundingClientRect();
            return [...stage.querySelectorAll('[data-tile]')].find(tile=>{
                const b=tile.getBoundingClientRect(),x=b.left+b.width/2,y=b.top+b.height/2;
                return x>r.left+12&&x<r.right-12&&y>r.top+12&&y<r.bottom-12&&
                    document.elementFromPoint(x,y)?.closest('[data-tile]')===tile;
            })?.dataset.tile;
        }""")
        assert visible is not None
        await page.locator(f'[data-tile="{visible}"]').click()
        assert await inspector.is_visible()
        await inspector.screenshot(path=str(ROOT/'brand/preview-tile-info.png'))
        await page.keyboard.press('Escape')
        assert await page.evaluate('JSON.stringify(__darb.G)') == before
        while await page.locator('[data-camera=in]').is_enabled():
            await page.locator('[data-camera=in]').click()
        assert (await camera_state(page))['zoom']==640
        assert await page.locator('#board').evaluate('(b)=>b.classList.contains("camera-readable")')
        while await page.locator('[data-camera=out]').is_enabled():
            await page.locator('[data-camera=out]').click()
        assert (await camera_state(page))['zoom']==75
        await page.locator('[data-camera=reset]').click()
        assert await camera_state(page)=={'zoom':100,'follow':'false','x':0,'y':0}
        await stage.focus();await page.keyboard.press('ArrowLeft')
        assert (await camera_state(page))['x']>0
        await page.keyboard.press('0')
        assert (await camera_state(page))['x']==0
        # Following is an explicit mode; the fitted overview does not pan by itself.
        await page.locator('[data-camera=follow]').click()
        # Actual gameplay keeps the existing pawn within the following viewport.
        await page.locator('#roll').click()
        await page.wait_for_function('__darb.G.players[0].pos>0')
        await page.wait_for_timeout(260)
        followed=await camera_state(page)
        # A fitted board can already keep the pawn in its readable region: no needless pan.
        pawn_box=await page.locator('.character-pawn[data-player="0"] .pawn-stand').bounding_box()
        stage_box=await stage.bounding_box()
        assert followed['follow']=='true',followed
        assert stage_box['x'] <= pawn_box['x']+pawn_box['width']/2 <= stage_box['x']+stage_box['width'],pawn_box
        assert stage_box['y'] <= pawn_box['y']+pawn_box['height']/2 <= stage_box['y']+stage_box['height'],pawn_box
        await page.wait_for_function('__darb.G.prompt !== null')
        # A pending game decision has priority over read-only inspection.
        await page.locator('[data-deck="family"]').evaluate('(el)=>{el.focus();el.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",bubbles:true}))}')
        assert not await inspector.is_visible()
        assert await page.locator('#modal.on').is_visible()
        mobile=await browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
        touch=await mobile.new_page()
        touch.on('pageerror',lambda e:errors.append(str(e)))
        await start_game(touch)
        target=touch.locator('.tabletop-stage')
        rect=await target.bounding_box();cx=rect['x']+rect['width']/2;cy=rect['y']+rect['height']/2
        cdp=await mobile.new_cdp_session(touch)
        async def event(kind,points):
            await cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'id':i,'x':x,'y':y,'radiusX':4,'radiusY':4} for i,x,y in points]})
        await event('touchStart',[(1,cx-35,cy),(2,cx+35,cy)])
        for gap in [45,55,65,75]:
            await event('touchMove',[(1,cx-gap,cy),(2,cx+gap,cy)])
        await event('touchEnd',[])
        pinched=await camera_state(touch)
        assert pinched['zoom']>170 and pinched['follow']=='false',pinched
        assert not await touch.locator('#board-inspector').is_visible()
        await touch.locator('[data-camera=reset]').click()
        await event('touchStart',[(1,cx,cy)])
        await event('touchMove',[(1,cx+60,cy+15)])
        await event('touchEnd',[])
        assert (await camera_state(touch))['x']>20
        await touch.locator('[data-camera=reset]').click()
        for width,height in [(360,800),(390,844),(768,1024),(1180,820)]:
            await touch.set_viewport_size({'width':width,'height':height})
            await touch.wait_for_timeout(100)
            assert await touch.evaluate('document.documentElement.scrollWidth<=innerWidth')
        await touch.set_viewport_size({'width':390,'height':844})
        await touch.locator('[data-camera=in]').click()
        await touch.locator('.tabletop-card').screenshot(path=str(ROOT/'brand/preview-camera-mobile.png'),style='.bar-actions,.react-fab,#toast{visibility:hidden!important}')
        assert not errors,errors
        print(json.dumps({'mouse_drag':'passed','wheel_zoom':'passed','zoom_limits':'75–640%',
                          'native_touch_pinch_and_pan':'passed','keyboard_camera':'passed','automatic_pawn_follow':'passed',
                          'read_only_landmark_and_deck_inspection':'passed','game_prompt_priority':'passed',
                          'responsive_sizes':4,'javascript_errors':errors},ensure_ascii=False,indent=2))
        await browser.close()

if __name__=='__main__':
    asyncio.run(asyncio.wait_for(verify(),timeout=110))
