/* Drag, pinch, wheel and follow camera. Game state remains owned by the engine. */
(() => {
  'use strict';
  const stage = document.querySelector('.tabletop-stage');
  const board = document.getElementById('board');
  if (!stage || !board) return;
  const world = document.createElement('div');
  world.className = 'tabletop-camera-world';
  const ground = document.createElement('div');
  ground.className = 'tabletop-district';
  ground.setAttribute('aria-hidden', 'true');
  world.append(ground, board);
  stage.append(world);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const camera = {x:0, y:0, zoom:1, follow:true};
  let options = null, identity = null, lastTarget = null;
  let frame = 0, followUntil = 0, forceFollow = false;
  const pointers = new Map();
  let gesture = null;
  const inspector = document.getElementById('board-inspector');
  let inspectedReference=null, previewYaw=-35, previewScale=2.5;
  const preview=inspector.querySelector('.board-info-symbol');
  const rotate=document.createElement('button');rotate.type='button';rotate.className='inspect-model-rotate';rotate.textContent='تدوير المجسّم';
  inspector.querySelector('.board-info-top').append(rotate);
  function turnPreview(yaw){previewYaw=yaw;const solid=preview.querySelector('.inspect-model-world');if(solid)solid.style.transform=`rotateX(55deg) rotateZ(${yaw}deg) scale(${previewScale})`;}
  rotate.addEventListener('click',()=>turnPreview(previewYaw+45));
  let previewDrag=null;
  preview.addEventListener('pointerdown',e=>{previewDrag={x:e.clientX,yaw:previewYaw};preview.setPointerCapture(e.pointerId);});
  preview.addEventListener('pointermove',e=>{if(previewDrag)turnPreview(previewDrag.yaw+(e.clientX-previewDrag.x)*1.2)});
  preview.addEventListener('pointerup',()=>previewDrag=null);
  preview.addEventListener('pointercancel',()=>previewDrag=null);
  preview.addEventListener('lostpointercapture',()=>previewDrag=null);
  const focus=document.createElement('button');focus.type='button';focus.className='inspect-model-focus';focus.textContent='قرّب هذا المجسّم على الطاولة';
  inspector.append(focus);
  function elementFor(reference) {
    if (Number.isInteger(reference)) return board.querySelector(`[data-tile="${reference}"]`);
    if (String(reference).startsWith('player:')) return board.querySelector(`.character-pawn[data-player="${String(reference).slice(7)}"]`);
    return board.querySelector(`[data-deck="${reference}"]`);
  }
  focus.addEventListener('click', () => {
    const tile = elementFor(inspectedReference);
    inspector.close();
    if (!tile) return;
    stopFollow();
    zoomAt(2.4);
    const viewport = stage.getBoundingClientRect(), target = tile.getBoundingClientRect();
    camera.x += viewport.left + viewport.width/2 - target.left - target.width/2;
    camera.y += viewport.top + viewport.height*.58 - target.top - target.height/2;
    draw();
    tile.focus({preventScroll:true});
  });
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  function limit() {
    const w = stage.clientWidth, h = stage.clientHeight;
    const maxX = Math.max(w * .15, (w * camera.zoom * 1.05 - w) / 2 + w * .3);
    const maxY = Math.max(h * .12, (w * camera.zoom * .9 - h) / 2 + h * .28);
    camera.x = clamp(camera.x, -maxX, maxX);
    camera.y = clamp(camera.y, -maxY, maxY);
  }
  function draw() {
    limit();
    const width=stage.clientWidth, height=stage.clientHeight;
    if(width && height){
      stage.style.setProperty('--isometric-fit', String(.64*Math.min(1,height/(width*.8))));
      stage.style.setProperty('--top-fit', String(.88*Math.min(1,height/width)));
    }
    world.style.transform = `translate3d(${camera.x}px,${camera.y}px,0) scale(${camera.zoom})`;
    stage.dataset.zoom = String(Math.round(camera.zoom * 100));
    stage.dataset.follow = String(camera.follow);
    board.classList.toggle('camera-readable', camera.zoom >= 1.55);
    document.querySelector('[data-camera-zoom]').textContent = `${Math.round(camera.zoom * 100)}٪`;
    document.querySelector('[data-camera="follow"]').setAttribute('aria-pressed', String(camera.follow));
    document.querySelector('[data-camera="in"]').disabled = camera.zoom >= 3.19;
    document.querySelector('[data-camera="out"]').disabled = camera.zoom <= .751;
  }
  function stopFollow() {
    camera.follow = false;
    followUntil = 0;
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    draw();
  }
  function followTick() {
    frame = 0;
    if (!camera.follow || !options || !stage.clientWidth || performance.now() > followUntil) return;
    const pawn = board.querySelector(`.character-pawn[data-player="${options.currentId}"] .pawn-stand`);
    if (!pawn) return;
    const viewport = stage.getBoundingClientRect(), target = pawn.getBoundingClientRect();
    const x = target.left + target.width / 2, y = target.top + target.height / 2;
    const left = viewport.left + viewport.width * .23, right = viewport.left + viewport.width * .77;
    const top = viewport.top + viewport.height * .22, bottom = viewport.top + viewport.height * .78;
    const dx = forceFollow ? viewport.left + viewport.width / 2 - x : x < left ? left - x : x > right ? right - x : 0;
    const dy = forceFollow ? viewport.top + viewport.height * .52 - y : y < top ? top - y : y > bottom ? bottom - y : 0;
    if (Math.abs(dx) > .5 || Math.abs(dy) > .5) {
      const easing = reduced.matches ? 1 : .2;
      camera.x += dx * easing;
      camera.y += dy * easing;
      draw();
    }
    if (!reduced.matches) frame = requestAnimationFrame(followTick);
  }
  function startFollow(force = false) {
    if (!camera.follow || !stage.clientWidth) return;
    forceFollow = force;
    followUntil = performance.now() + (force ? 800 : 450);
    if (!frame) frame = requestAnimationFrame(followTick);
  }
  function reset() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    followUntil = 0;
    camera.x = camera.y = 0;
    camera.zoom = 1;
    camera.follow = true;
    draw();
  }
  function zoomAt(nextZoom, clientX, clientY) {
    const rect = stage.getBoundingClientRect();
    const x = (clientX ?? rect.left + rect.width / 2) - rect.left - rect.width / 2;
    const y = (clientY ?? rect.top + rect.height / 2) - rect.top - rect.height / 2;
    const next = clamp(nextZoom, .75, 3.2), factor = next / camera.zoom;
    camera.x = x - (x - camera.x) * factor;
    camera.y = y - (y - camera.y) * factor;
    camera.zoom = next;
    draw();
  }
  function inspect(reference) {
    if (!options || options.busy || document.querySelector('#modal.on')) return;
    const info = options.inspect?.(reference);
    if (!info) return;
    inspectedReference=reference;
    board.querySelectorAll('.is-inspected').forEach(tile=>tile.classList.remove('is-inspected'));
    const selected=elementFor(reference);selected?.classList.add('is-inspected');
    const body=selected?.querySelector('.miniature-body,.pawn-figure');
    if(body&&!reduced.matches)body.animate([{translate:'0 0 0'},{translate:'0 0 8px'},{translate:'0 0 0'}],{duration:240});
    inspector.querySelector('#board-info-title').textContent = info.title;
    inspector.querySelector('.board-info-subtitle').textContent = info.subtitle;
    inspector.querySelector('.board-info-description').textContent = info.description;
    inspector.querySelector('.board-info-symbol').style.background = info.color;
    inspector.querySelector('use').setAttribute('href', `icons/game-icons.svg#${info.icon}`);
    preview.querySelector('.inspect-model-world')?.remove();
    const model=document.createElement('span');model.className='inspect-model-world';model.innerHTML=window.DarbModels.geometry(info.model||'deal');preview.append(model);previewScale=String(info.model).startsWith('player_')?1.8:2.5;turnPreview(-35);
    preview.setAttribute('aria-label','مجسم '+info.title+'، اسحب لتدويره');
    const list = inspector.querySelector('dl');
    list.replaceChildren();
    for (const [label, value] of info.details || []) {
      const dt = document.createElement('dt'), dd = document.createElement('dd');
      dt.textContent = label;
      dd.textContent = value;
      list.append(dt, dd);
    }
    inspector.showModal();
  }
  const referenceFor = target => {
    const pawn=target.closest('.character-pawn');
    if(pawn)return 'player:'+pawn.dataset.player;
    const tile = target.closest('[data-tile]');
    if (tile) return Number(tile.dataset.tile);
    return target.closest('[data-deck]')?.dataset.deck ?? null;
  };
  stage.addEventListener('pointerdown', event => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    event.preventDefault();
    stage.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, {x:event.clientX, y:event.clientY});
    if (pointers.size === 1) {
      gesture = {startX:event.clientX, startY:event.clientY, lastX:event.clientX, lastY:event.clientY,
        moved:false, multi:false, reference:referenceFor(event.target)};
    } else if (gesture) {
      gesture.multi = true;
      const [a,b] = [...pointers.values()];
      gesture.distance = Math.hypot(a.x-b.x, a.y-b.y);
      gesture.midX = (a.x+b.x)/2;
      gesture.midY = (a.y+b.y)/2;
      stopFollow();
    }
  });
  stage.addEventListener('pointermove', event => {
    if (!pointers.has(event.pointerId) || !gesture) return;
    pointers.set(event.pointerId, {x:event.clientX, y:event.clientY});
    if (pointers.size >= 2) {
      const [a,b] = [...pointers.values()];
      const distance = Math.hypot(a.x-b.x, a.y-b.y), midX=(a.x+b.x)/2, midY=(a.y+b.y)/2;
      camera.x += midX - gesture.midX;
      camera.y += midY - gesture.midY;
      if (gesture.distance > 0) zoomAt(camera.zoom * distance / gesture.distance, midX, midY);
      gesture.distance = distance; gesture.midX = midX; gesture.midY = midY;
    } else {
      if (!gesture.moved && Math.hypot(event.clientX-gesture.startX,event.clientY-gesture.startY) > 6) {
        gesture.moved = true;
        stopFollow();
        stage.classList.add('is-dragging');
      }
      if (gesture.moved || gesture.multi) {
        camera.x += event.clientX-gesture.lastX;
        camera.y += event.clientY-gesture.lastY;
        draw();
      }
      gesture.lastX=event.clientX; gesture.lastY=event.clientY;
    }
  });
  function release(event) {
    if (!pointers.has(event.pointerId)) return;
    pointers.delete(event.pointerId);
    if (pointers.size && gesture) {
      const remaining = [...pointers.values()][0];
      gesture.lastX=remaining.x; gesture.lastY=remaining.y;
    } else {
      const reference = gesture && !gesture.moved && !gesture.multi && event.type !== 'pointercancel' ? gesture.reference : null;
      gesture = null;
      stage.classList.remove('is-dragging');
      if (reference !== null) inspect(reference);
    }
  }
  stage.addEventListener('pointerup', release);
  stage.addEventListener('pointercancel', release);
  stage.addEventListener('lostpointercapture', event => { if (pointers.has(event.pointerId)) release({...event, type:'pointercancel', pointerId:event.pointerId}); });
  stage.addEventListener('dragstart', event => event.preventDefault());
  stage.addEventListener('wheel', event => {
    event.preventDefault();
    stopFollow();
    const pixels = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? stage.clientHeight : 1);
    zoomAt(camera.zoom * Math.exp(-clamp(pixels, -200, 200) * .002), event.clientX, event.clientY);
  }, {passive:false});
  stage.addEventListener('keydown', event => {
    const reference = referenceFor(event.target);
    if ((event.key === 'Enter' || event.key === ' ') && reference !== null) {
      event.preventDefault(); inspect(reference); return;
    }
    if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','0'].includes(event.key)) {
      event.preventDefault();
      if (event.key === '0') { reset(); return; }
      stopFollow();
      if (event.key === '+' || event.key === '=') zoomAt(camera.zoom*1.25);
      else if (event.key === '-') zoomAt(camera.zoom/1.25);
      else {
        camera.x += event.key === 'ArrowLeft' ? 35 : event.key === 'ArrowRight' ? -35 : 0;
        camera.y += event.key === 'ArrowUp' ? 35 : event.key === 'ArrowDown' ? -35 : 0;
        draw();
      }
    }
  });
  document.querySelectorAll('[data-camera]').forEach(button => button.addEventListener('click', () => {
    const action = button.dataset.camera;
    if (action === 'reset') reset();
    else if (action === 'follow') {
      camera.follow = !camera.follow;
      if (camera.follow) startFollow(true); else stopFollow();
      draw();
    } else {
      stopFollow();
      zoomAt(camera.zoom * (action === 'in' ? 1.25 : .8));
    }
  }));
  inspector.querySelectorAll('[data-close-inspector]').forEach(button => button.addEventListener('click', () => inspector.close()));
  inspector.addEventListener('close',()=>{previewDrag=null;board.querySelectorAll('.is-inspected').forEach(tile=>tile.classList.remove('is-inspected'));});
  inspector.addEventListener('click', event => {
    const rect = inspector.getBoundingClientRect();
    if (event.target === inspector && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) inspector.close();
  });
  new ResizeObserver(() => draw()).observe(stage);
  draw();
  window.DarbCamera = {
    update(next) {
      options = next;
      const key = `${next.gameId}:${next.track}`;
      if (identity !== key) { identity=key; lastTarget=null; reset(); }
      if (next.busy && inspector.open) inspector.close();
      const pawn = next.players.find(p => p.id === next.currentId);
      const target = pawn ? `${pawn.id}:${pawn.pos}` : null;
      if (lastTarget !== null && target !== lastTarget && camera.follow) startFollow();
      lastTarget = target;
      draw();
    },
    viewChanged:reset
  };
})();
