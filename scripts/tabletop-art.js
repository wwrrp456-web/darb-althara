/* Pre-rendered illustrated miniatures. One flat sprite per building/deck; no 3D mesh or render loop. */
(() => {
  'use strict';
  const board=document.getElementById('board');
  const keys=['cafe','mall','uni','hospital','hotel','bank','tower','airport'];
  function probe(file,cssClass){
    const image=new Image();
    image.onload=()=>board.classList.add(cssClass);
    image.onerror=()=>board.classList.remove(cssClass); // Keep the original flat icons as fallback.
    image.src='art/identity/'+file;
  }
  probe('landmarks-sheet.png','landmarks-ready');
  probe('decks-sheet.png','decks-ready');
  function mount(cells,options){
    for(const tile of cells.querySelectorAll('[data-landmark]')){
      const i=keys.indexOf(tile.dataset.landmark);if(i<0)continue;
      tile.classList.add('landmark-has-art');
      const stand=document.createElement('span');stand.className='landmark-stand';stand.setAttribute('aria-hidden','true');
      const art=document.createElement('span');art.className='landmark-sprite';
      art.style.setProperty('--sx',(i%4)*100/3+'%');art.style.setProperty('--sy',Math.floor(i/4)*100+'%');
      stand.append(art);
      const level=Math.max(0,Math.min(3,Number(tile.dataset.level)||0));
      if(level){const badge=document.createElement('span');badge.className='landmark-level-art';badge.dataset.level=String(level);badge.style.setProperty('--lx',(level-1)*50+'%');stand.append(badge);}
      if(tile.dataset.ownerColor){tile.classList.add('landmark-owned');tile.style.setProperty('--owner-color',tile.dataset.ownerColor);}
      const occupied=options.players.some(p=>p.pos===Number(tile.dataset.tile));
      tile.classList.toggle('landmark-occupied',occupied);
      // Buildings sit toward the park edge of their tile, leaving the road to the pawns.
      const row=parseInt(tile.style.gridRow,10),col=parseInt(tile.style.gridColumn,10);
      const n=options.track==='fast'?6:13,offset=occupied?100:65;
      if(row===1)stand.style.top=(50+offset)+'%';
      else if(row===n)stand.style.top=(50-offset)+'%';
      else if(col===1)stand.style.left=(50+offset)+'%';
      else stand.style.left=(50-offset)+'%';
      tile.append(stand);
    }
    for(const deck of cells.querySelectorAll('[data-deck]')){
      const i={family:0,quiz:1,deal:2}[deck.dataset.deck];if(i===undefined)continue;
      deck.classList.add('has-deck-art');
      const art=document.createElement('span');art.className='deck-sprite';art.setAttribute('aria-hidden','true');art.style.setProperty('--dx',i*50+'%');deck.append(art);
    }
  }
  window.DarbTabletopArt={mount};
})();
