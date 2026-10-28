/* Pre-rendered illustrated miniatures. One flat sprite per building/deck; no 3D mesh or render loop. */
(() => {
  'use strict';
  const board=document.getElementById('board');
  const keys=['cafe','mall','uni','hospital','hotel','bank','tower','airport'];
  const textMeasure=document.createElement('canvas').getContext('2d'),wordWidths=new Map();
  function fitLabels(cells){
    const tiles=cells.querySelectorAll('[data-tile]');if(!tiles.length)return;
    const available=Math.max(1,tiles[0].clientWidth-6);
    if(textMeasure){textMeasure.font='700 100px Tajawal';textMeasure.direction='rtl';}
    for(const label of cells.querySelectorAll('.tile-name')){
      let widest=0;
      for(const word of label.textContent.trim().split(/\s+/)){
        if(!wordWidths.has(word))wordWidths.set(word,textMeasure?textMeasure.measureText(word).width/100:word.length*.7);
        widest=Math.max(widest,wordWidths.get(word));
      }
      const limit=available/Math.max(.1,widest);
      label.style.setProperty('--tile-font-limit',limit+'px');label.dataset.minimumScale=String(12.5/limit);
    }
  }
  document.fonts?.ready.then(()=>{wordWidths.clear();fitLabels(board);window.DarbCamera?.labelsChanged();});
  function probe(file,cssClass){
    const image=new Image();
    image.onload=()=>{board.classList.add(cssClass);if(cssClass==='decks-ready')document.getElementById('board-deck-rack').classList.add(cssClass);};
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
      if(level){const badge=document.createElement('span');badge.className='landmark-level-art';badge.dataset.level=String(level);badge.style.setProperty('--lx',(level-1)*50+'%');badge.textContent=String(level);stand.append(badge);}
      if(tile.dataset.ownerColor){tile.classList.add('landmark-owned');tile.style.setProperty('--owner-color',tile.dataset.ownerColor);}
      const occupied=options.players.some(p=>p.pos===Number(tile.dataset.tile));
      tile.classList.toggle('landmark-occupied',occupied);
      tile.append(stand);
    }
    fitLabels(cells);
    for(const deck of document.querySelectorAll('#board-deck-rack [data-deck]')){
      if(deck.querySelector('.deck-sprite'))continue;
      const i={family:0,quiz:1,deal:2}[deck.dataset.deck];if(i===undefined)continue;
      deck.classList.add('has-deck-art');
      const art=document.createElement('span');art.className='deck-sprite';art.setAttribute('aria-hidden','true');art.style.setProperty('--dx',i*50+'%');deck.append(art);const hit=document.createElement('span');hit.className='miniature-hit';hit.setAttribute('aria-hidden','true');deck.append(hit);
    }
  }
  function decorateSymbol(symbol,info){
    symbol.querySelector('.inspector-art,.inspector-character')?.remove();symbol.classList.remove('has-inspector-art');
    if(info.portrait){const image=document.createElement('img');image.className='inspector-character';image.alt=info.subtitle;image.onload=()=>{if(image.isConnected)symbol.classList.add('has-inspector-art')};image.src=info.portrait;symbol.append(image);return;}
    const art=info.art;if(!art)return;
    const i=art.sheet==='landmark'?keys.indexOf(art.key):({family:0,quiz:1,deal:2}[art.key]);
    if(i===undefined||i<0||!board.classList.contains(art.sheet==='landmark'?'landmarks-ready':'decks-ready'))return;
    const image=document.createElement('span');image.className='inspector-art '+(art.sheet==='landmark'?'landmark-preview':'deck-preview');image.setAttribute('aria-hidden','true');
    image.style.setProperty('--sx',(art.sheet==='landmark'?i%4*100/3:i*50)+'%');image.style.setProperty('--sy',(art.sheet==='landmark'?Math.floor(i/4)*100:0)+'%');
    symbol.append(image);symbol.classList.add('has-inspector-art');
  }
  window.DarbTabletopArt={mount,decorateSymbol,fitLabels};
})();
