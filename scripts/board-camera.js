/* Drag, pinch, wheel and follow camera. Game state remains owned by the engine. */
(() => {
  'use strict';
  const stage = document.querySelector('.tabletop-stage');
  const board = document.getElementById('board');
  if (!stage || !board) return;
  const world = document.createElement('div');
  world.className = 'tabletop-camera-world';
  world.append(board);
  stage.append(world);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const camera = {x:0, y:0, zoom:1, follow:false};
  let options = null, identity = null, lastTarget = null,labels=[];
  let frame = 0, followUntil = 0, forceFollow = false;
  const pointers = new Map();
  let gesture = null;
  const inspector = document.getElementById('board-inspector');
  let inspectedReference=null;
  let fit=1, footprint={width:640,height:640};
  const crowd=document.getElementById("board-crowd"),projects=document.getElementById("board-projects");
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  function measureFit() {
    const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h)return;
    const tilt=stage.dataset.view==='top'?0:Math.acos(clamp((h-56)/Math.max(1,w-56),Math.cos(52*Math.PI/180),Math.cos(24*Math.PI/180)))*180/Math.PI;
    stage.style.setProperty('--table-tilt',tilt+'deg');
    const saved=world.style.transform;world.style.transform='none';
    const viewport=stage.getBoundingClientRect(),cx=viewport.left+w/2,cy=viewport.top+h/2;
    const pad=28;fit=1;
    // Measure the browser's actual perspective projection, only on resize/view changes.
    for(let i=0;i<3;i++){
      stage.style.setProperty('--table-scale',String(fit));
      const r=board.getBoundingClientRect();
      const factor=Math.min((w/2-pad)/Math.max(cx-r.left,r.right-cx,1),(h/2-pad)/Math.max(cy-r.top,r.bottom-cy,1));
      fit*=Math.max(.01,factor);
    }
    stage.style.setProperty('--table-scale',String(fit));
    const r=board.getBoundingClientRect();footprint={width:r.width,height:r.height};
    world.style.transform=saved;
    stage.dataset.fit=String(fit);
  }
  function limit() {
    // Retain at least one touch target of the measured surface inside the viewport.
    const maxX=Math.max(0,(footprint.width*camera.zoom+stage.clientWidth)/2-48);
    const maxY=Math.max(0,(footprint.height*camera.zoom+stage.clientHeight)/2-48);
    camera.x=clamp(camera.x,-maxX,maxX);camera.y=clamp(camera.y,-maxY,maxY);
  }
  function draw() {
    limit();
    world.style.transform = `translate3d(${camera.x}px,${camera.y}px,0) scale(${camera.zoom})`;
    stage.dataset.zoom = String(Math.round(camera.zoom * 100));
    stage.dataset.follow = String(camera.follow);
    const readable=fit*camera.zoom*(640/(options?.track==='fast'?6:13))>=44;
    for(const label of labels)label.parentElement.classList.toggle('label-readable',readable&&fit*camera.zoom>=Number(label.dataset.minimumScale||Infinity));
    board.classList.toggle('camera-readable',readable);board.classList.toggle('names',readable);
    document.querySelector('[data-camera-zoom]').textContent = `${Math.round(camera.zoom * 100)}٪`;
    document.querySelector('[data-camera="follow"]').setAttribute('aria-pressed', String(camera.follow));
    document.querySelector('[data-camera="in"]').disabled = camera.zoom >= 6.39;
    document.querySelector('[data-camera="out"]').disabled = camera.zoom <= .751;
  }
  function updateHitTargets() {
    const scale=Math.max(.01,fit*camera.zoom);
    stage.style.setProperty('--mini-hit-size',`${Math.ceil(56/scale)}px`);
    stage.style.setProperty('--projected-scale',String(scale));
    stage.style.setProperty('--pawn-size',`${Math.min(80,48/scale)}px`);

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
    camera.follow = false;
    measureFit();
    updateHitTargets();
    draw();
  }
  function zoomAt(nextZoom, clientX, clientY) {
    const rect = stage.getBoundingClientRect();
    const x = (clientX ?? rect.left + rect.width / 2) - rect.left - rect.width / 2;
    const y = (clientY ?? rect.top + rect.height / 2) - rect.top - rect.height / 2;
    const next = clamp(nextZoom, .75, 6.4), factor = next / camera.zoom;
    camera.x = x - (x - camera.x) * factor;
    camera.y = y - (y - camera.y) * factor;
    camera.zoom = next;
    updateHitTargets();
    draw();
  }
  function inspect(reference) {
    if(reference==='projects'){
      if(!options||options.busy||document.querySelector('#modal.on'))return;
      const list=document.getElementById('project-list');if(!projects.open)list.replaceChildren();
      for(const tile of board.querySelectorAll('[data-landmark]')){
        const key=tile.dataset.landmark,info=options.inspect?.('lm_'+key);if(!info)continue;
        let button=list.querySelector(`[data-project="${key}"]`);
        if(!button){
          button=document.createElement('button');button.type='button';button.dataset.project=key;
          const thumb=document.createElement('span');thumb.className='project-thumb';thumb.setAttribute('aria-hidden','true');
          const label=document.createElement('span'),title=document.createElement('b'),meta=document.createElement('small');meta.className='project-meta';label.append(title,meta);button.append(thumb,label);
          button.onclick=()=>{projects.close();document.getElementById('board-projects-open').focus();inspect('lm_'+key);};list.append(button);
        }
        const signature=JSON.stringify([info.title,info.owner,(info.details||[]).filter(([key])=>['المالك','مستوى التطوير'].includes(key))]);
        if(button.dataset.info!==signature){
          button.dataset.info=signature;button.querySelector('b').textContent=info.title;
          const meta=button.querySelector('.project-meta');meta.replaceChildren();
          for(const [key,value] of info.details||[]){if(!['المالك','مستوى التطوير'].includes(key)||key==='مستوى التطوير'&&!info.owner)continue;const tag=document.createElement('span');tag.textContent=key==='المالك'?(value==='متاح للشراء'?value:'المالك: '+value):'المستوى '+value;meta.append(tag);}
        }
        const thumb=button.querySelector('.project-thumb');if(!thumb.querySelector('.inspector-art'))window.DarbTabletopArt?.decorateSymbol(thumb,info);
      }
      if(!projects.open)projects.showModal();return;
    }
    if(typeof reference==='string'&&(reference==='players'||reference.startsWith('group:'))){
      if(!options||options.busy||document.querySelector('#modal.on'))return;
      const people=reference==='players'?(options.allPlayers||options.players):options.players.filter(p=>p.pos===Number(reference.slice(6)));
      const list=document.getElementById('crowd-list');list.replaceChildren();
      document.getElementById('crowd-title').textContent=reference==='players'?'اللاعبون':'اللاعبون في هذه الخانة';
      for(const p of people){
        const button=document.createElement('button');button.type='button';button.dataset.player=String(p.id);
        const image=document.createElement('img');image.src=`art/identity/clear.svg#${p.pk}`;image.alt='';
        const label=document.createElement('span'),name=document.createElement('b'),job=document.createElement('small');
        name.textContent=`${p.id+1} · ${p.name}`;job.textContent=p.prof;label.append(name,job);button.append(image,label);
        button.onclick=()=>{crowd.close();inspect('player:'+p.id)};list.append(button);
      }
      if(!crowd.open)crowd.showModal();return;
    }
    if (!options || options.busy || document.querySelector('#modal.on')) return;
    const info = options.inspect?.(reference);
    if (!info) return;
    inspectedReference=reference;
    const view=document.getElementById('view-player-board');
    view.hidden=!(typeof reference==='string'&&reference.startsWith('player:'));
    view.onclick=()=>{inspector.close();options?.viewPlayer?.(Number(String(reference).slice(7)))};
    inspector.querySelector('#board-info-title').textContent = info.title;
    inspector.querySelector('.board-info-subtitle').textContent = info.subtitle;
    inspector.querySelector('.board-info-description').textContent = info.description;
    inspector.querySelector('.board-info-symbol').style.background = info.color;
    inspector.querySelector('use').setAttribute('href', `#gi-${info.icon}`);
    inspector.querySelector('.ui-icon').dataset.icon=info.icon;
    window.DarbSprites?.hydrate(inspector.querySelector('.ui-icon'));
    window.DarbTabletopArt.decorateSymbol(inspector.querySelector('.board-info-symbol'),info);
    const list = inspector.querySelector('dl');
    list.replaceChildren();
    for (const [label, value] of info.details || []) {
      const dt = document.createElement('dt'), dd = document.createElement('dd');
      dt.textContent = label;
      if(label==='المالك'&&info.owner){const avatar=document.createElement('span');avatar.className='identity-avatar-value';avatar.textContent=info.owner.avatar;dd.append(avatar,document.createTextNode(' '+info.owner.name));}
      else dd.textContent = value;
      list.append(dt, dd);
    }
    if(!inspector.open)inspector.showModal();
  }
  const referenceFor = target => {
    const group=target.closest('.pawn-cluster');if(group)return 'group:'+group.dataset.position;
    const pawn=target.closest('.character-pawn');if(pawn)return 'player:'+pawn.dataset.player;
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
  projects.querySelector('[data-close-projects]').onclick=()=>projects.close();
  for(const button of document.querySelectorAll('#board-deck-rack [data-deck]')){
    button.onclick=()=>inspect(button.dataset.deck);
    button.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();inspect(button.dataset.deck);}});
  }
  crowd.querySelector('[data-close-crowd]').onclick=()=>crowd.close();
  inspector.querySelectorAll('[data-close-inspector]').forEach(button => button.addEventListener('click', () => inspector.close()));
  inspector.addEventListener('click', event => {
    const rect = inspector.getBoundingClientRect();
    if (event.target === inspector && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) inspector.close();
  });
  new ResizeObserver(() => {measureFit();updateHitTargets();draw();if(camera.follow)startFollow();}).observe(stage);
  measureFit();
  updateHitTargets();
  draw();
  window.DarbCamera = {
    update(next) {
      options = next;labels=[...board.querySelectorAll('.tile-name')];
      const key = `${next.gameId}:${next.track}`;
      if (identity !== key) { if(projects.open)projects.close();identity=key; lastTarget=null; reset(); }
      if(next.busy&&crowd.open)crowd.close();
      if(next.busy&&projects.open)projects.close();
      else if(projects.open)inspect('projects');
      if (next.busy && inspector.open) inspector.close();
      else if(inspector.open&&inspectedReference!==null)inspect(inspectedReference);
      const pawn = next.players.find(p => p.id === next.currentId);
      const target = pawn ? `${pawn.id}:${pawn.pos}` : null;
      if (lastTarget !== null && target !== lastTarget && camera.follow) startFollow();
      lastTarget = target;
      draw();
    },
    inspect,
    labelsChanged(){labels=[...board.querySelectorAll('.tile-name')];draw();},
    viewChanged:reset
  };
})();
