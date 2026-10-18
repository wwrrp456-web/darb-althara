/* Persistent character pawns on a CSS 3D tabletop. Presentation only: no game rules. */
(() => {
  'use strict';
  let state = null;
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const professionKeys = new Set(['trader','teacher','nurse','engineer','driver','doctor','accountant','grocer','farmer','carpenter','chef','programmer','pharmacist','pilot']);

  function positionPawns(animate = false) {
    if (!state || !state.board.isConnected || !state.board.clientWidth) return;
    const {board, layer, players, currentId, duration, tiles} = state;
    board.classList.toggle('names', board.clientWidth >= 560);
    board.style.setProperty('--mini-fit', String(Math.max(.45,Math.min(1.25,board.clientWidth / (tiles.size===20?6:13) / 34))));
    board.style.setProperty('--figure-scale', String(Math.max(.65,Math.min(1.1,board.clientWidth / 600))));
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
        pawn.innerHTML = '<span class="pawn-shadow"></span><span class="pawn-base"></span><span class="pawn-stand"><img class="pawn-art" alt=""><span class="pawn-number"></span></span>';
        layer.append(pawn);
      }
      const role = professionKeys.has(p.pk) ? p.pk : 'trader';
      let figure=pawn.querySelector('.pawn-figure');
      if(!figure){figure=document.createElement('span');figure.className='pawn-figure';figure.setAttribute('aria-hidden','true');pawn.querySelector('.pawn-stand').append(figure);}
      if(pawn.dataset.role!==role)figure.innerHTML=window.DarbModels.person(role);
      const image = pawn.querySelector('.pawn-art');
      const src = `art/identity/clear.svg#pawn_${role}`;
      if (image.getAttribute('src') !== src) image.setAttribute('src', src);
      image.alt = `قطعة ${p.name} · ${p.prof}`;
      pawn.title = `${p.name} · ${p.prof} · الخانة ${p.pos + 1}`;
      pawn.setAttribute('role','button');pawn.tabIndex=0;pawn.setAttribute('aria-label','بيانات '+p.name+'، '+p.prof);
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
        figure.getAnimations().forEach(a => a.cancel());
        figure.animate([
          {translate:'0 0 0'},
          {translate:'0 0 7px',offset:.5},
          {translate:'0 0 0'}
        ], {duration, easing:'ease-in-out'});
      }
    }
    for (const pawn of layer.children) if (!keep.has(pawn.dataset.player)) pawn.remove();
  }

  function setView(view) {
    const stage = document.querySelector('.tabletop-stage');
    if (!stage) return;
    stage.dataset.view = view === 'top' ? 'top' : 'perspective';
    document.querySelectorAll('[data-table-view]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.tableView === stage.dataset.view));
    });
    try { localStorage.setItem('darb-table-view', stage.dataset.view); } catch (_) {}
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
    const retained = new Map();
    if (sameBoard) for (const item of cells.querySelectorAll('[data-tile],[data-deck]')) {
      const object = item.querySelector(':scope > .board-miniature');
      if (object) retained.set(item.hasAttribute('data-tile') ? `tile:${item.dataset.tile}:${item.dataset.model}` : `deck:${item.dataset.deck}`, object);
    }
    cells.innerHTML = html;
    window.DarbModels.mount(cells, retained);
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
  window.DarbTabletop = {paint, refresh: () => requestAnimationFrame(() => positionPawns(false))};
})();
