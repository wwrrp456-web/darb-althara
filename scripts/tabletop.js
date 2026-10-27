/* Persistent character pawns on a CSS 3D tabletop. Presentation only: no game rules. */
(() => {
  'use strict';
  let state = null;
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const professionKeys = new Set(['trader','teacher','nurse','engineer','driver','doctor','accountant','grocer','farmer','carpenter','chef','programmer','pharmacist','pilot']);

  function positionPawns(animate = false) {
    if (!state || !state.board.isConnected || !state.board.clientWidth) return;
    const {board, layer, players, currentId, duration, tiles} = state;
    board.style.setProperty('--pawn-size', `${Math.max(48, Math.min(90, board.clientWidth * .16))}px`);
    const countByTile = new Map();
    for (const p of players) {
      const key = p.pos;
      if (!countByTile.has(key)) countByTile.set(key, []);
      countByTile.get(key).push(p.id);
    }
    const keep = new Set();
    for (const p of players) {
      const tile = tiles.get(p.pos);
      if (!tile) continue;
      keep.add(String(p.id));
      let pawn = layer.querySelector(`[data-player="${p.id}"]`);
      const fresh = !pawn;
      if (fresh) {
        pawn = document.createElement('div');
        pawn.className = 'character-pawn';
        pawn.dataset.player = String(p.id);
        pawn.innerHTML = '<span class="pawn-shadow"></span><span class="pawn-base"></span><span class="pawn-stand"><img class="pawn-art" alt=""><span class="pawn-number"></span><span class="miniature-hit" aria-hidden="true"></span></span>';
        layer.append(pawn);
      }
      const role = professionKeys.has(p.pk) ? p.pk : 'trader';
      const image = pawn.querySelector('.pawn-art');
      const src = `art/identity/clear.svg#pawn_${role}`;
      if (image.getAttribute('src') !== src) image.setAttribute('src', src);
      image.alt = `قطعة ${p.name} · ${p.prof}`;
      pawn.title = `${p.name} · ${p.prof} · الخانة ${p.pos + 1}`;
      pawn.tabIndex=0;pawn.setAttribute("role","button");pawn.setAttribute("aria-label","بيانات "+p.name+"، "+p.prof);
      pawn.classList.toggle('current', p.id === currentId);
      pawn.style.setProperty('--pawn-color', /^#[0-9a-f]{6}$/i.test(p.color) ? p.color : '#16614c');
      pawn.querySelector('.pawn-number').textContent = String(p.id + 1);
      const group = countByTile.get(p.pos);
      const index = group.indexOf(p.id);
      // Fan co-located pieces into two rows, including a full eight-player start.
      const columns = Math.min(group.length, 4);
      const row = Math.floor(index / 4);
      const rowSize = Math.min(group.length - row * 4, 4);
      const spread = Math.min(15, tile.offsetWidth * .48);
      const x = tile.offsetLeft + tile.offsetWidth / 2 + ((index % columns) - (rowSize - 1) / 2) * spread;
      const y = tile.offsetTop + tile.offsetHeight * .65 + row * Math.min(14, tile.offsetHeight * .5);
      const moved = !fresh && pawn.dataset.position !== String(p.pos);
      pawn.style.transitionDuration = animate && !fresh && !reducedMotion.matches ? `${duration}ms` : '0ms';
      pawn.style.transform = `translate3d(${x}px,${y}px,8px)`;
      pawn.style.zIndex = String(Math.round(y) + (p.id === currentId ? 10 : 0));
      pawn.dataset.position = String(p.pos);
      pawn.dataset.role = role;
      if (animate && moved && !reducedMotion.matches) {
        image.getAnimations().forEach(a => a.cancel());
        image.animate([
          {transform:'translateY(0) rotate(-2deg)'},
          {transform:'translateY(-7px) rotate(2deg)',offset:.5},
          {transform:'translateY(0) rotate(0)'}
        ], {duration, easing:'ease-in-out'});
      }
    }
    for (const pawn of layer.querySelectorAll('.character-pawn')) if (!keep.has(pawn.dataset.player)) pawn.remove();
    const groups=new Set();
    for(const [position,ids] of countByTile){
      const leader=ids.includes(currentId)?currentId:ids[0];
      for(const id of ids){
        const pawn=layer.querySelector(`.character-pawn[data-player="${id}"]`);
        pawn.classList.toggle('clustered',ids.length>1);pawn.classList.toggle('cluster-lead',ids.length>1&&id===leader);
        pawn.tabIndex=ids.length>1?-1:0;
        if(ids.length>1)pawn.setAttribute('aria-hidden','true');else pawn.removeAttribute('aria-hidden');
      }
      if(ids.length<2)continue;
      groups.add(String(position));
      let group=layer.querySelector(`.pawn-cluster[data-position="${position}"]`);
      if(!group){group=document.createElement('div');group.className='pawn-cluster';group.setAttribute('aria-hidden','true');group.dataset.position=String(position);layer.append(group);}
      group.textContent=String(ids.length);
      group.title=ids.length+' لاعبون؛ اختر من زر اللاعبين أسفل اللوحة';
      const tile=tiles.get(position),x=tile.offsetLeft+tile.offsetWidth*.9,y=tile.offsetTop+tile.offsetHeight*.95;
      group.style.transform=`translate3d(${x}px,${y}px,12px) translate(-50%,-100%) rotateZ(calc(-1 * var(--table-yaw))) rotateX(calc(-1 * var(--table-tilt)))`;
    }
    for(const group of layer.querySelectorAll('.pawn-cluster'))if(!groups.has(group.dataset.position))group.remove();
  }

  function setView(view) {
    const stage = document.querySelector('.tabletop-stage');
    if (!stage) return;
    stage.dataset.view = view === 'top' ? 'top' : 'perspective';
    document.querySelectorAll('[data-table-view]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.tableView === stage.dataset.view));
    });
    try { localStorage.setItem('darb-table-view', stage.dataset.view); } catch (_) {}
    const select=document.getElementById("table-view-select");if(select)select.value=stage.dataset.view;
    window.DarbCamera?.viewChanged();
  }

  function paint(board, html, options) {
    let cells = board.querySelector(':scope > .board-cells');
    if (!cells) {
      cells = document.createElement('div');
      cells.className = 'board-cells';
      const layer = document.createElement('div');
      layer.className = 'pawn-layer';
      const edge = document.createElement('div');
      edge.className = 'tabletop-front-edge';
      edge.setAttribute('aria-hidden', 'true');
      const rightEdge = document.createElement('div');
      rightEdge.className = 'tabletop-right-edge';
      rightEdge.setAttribute('aria-hidden', 'true');
      board.replaceChildren(cells, edge, rightEdge, layer);
    }
    const layer = board.querySelector(':scope > .pawn-layer');
    const identity = `${options.gameId}:${options.track}`;
    const sameBoard = state && state.identity === identity;
    if (!sameBoard) layer.replaceChildren();
    // Replace only surface content. Pawn nodes stay connected to preserve their motion.
    cells.innerHTML = html;
    window.DarbTabletopArt.mount(cells,options);
    // Finalize illustrated labels before measuring cells for pawn coordinates.
    window.DarbIdentity?.hydrate(cells);
    const tiles = new Map([...cells.querySelectorAll('[data-tile]')].map(tile => [Number(tile.dataset.tile), tile]));
    state = {...options, board, layer, tiles, identity};
    positionPawns(Boolean(sameBoard));
    window.DarbCamera?.update(options);
  }

  const resize = new ResizeObserver(() => positionPawns(false));
  const board = document.getElementById('board');
  if (board) resize.observe(board);
  document.querySelectorAll('[data-table-view]').forEach(button => {
    button.addEventListener('click', () => setView(button.dataset.tableView));
  });
  let initialView = 'perspective';
  try { initialView = localStorage.getItem('darb-table-view') || initialView; } catch (_) {}
  setView(initialView);
  window.DarbTabletop = {paint, setView, refresh: () => requestAnimationFrame(() => positionPawns(false))};
})();
