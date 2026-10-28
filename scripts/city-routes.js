/* Live game indices follow the roads in each approved city illustration. */
(() => {
 'use strict';
 const NS='http://www.w3.org/2000/svg',scale=1.25;
 function el(tag,attrs){const node=document.createElementNS(NS,tag);for(const [key,value]of Object.entries(attrs))node.setAttribute(key,String(value));return node;}
 function artwork(def,region=def.crop){const svg=el('svg',{viewBox:region.join(' '),'aria-hidden':'true',focusable:'false'});svg.append(el('image',{href:'art/cities/playable-cities.webp',width:1024,height:1536}));return svg;}
 function definition(id=document.documentElement.dataset.city){return window.DarbCityScenes.defs.find(d=>d.id===id);}
 function points(track,count,id=document.documentElement.dataset.city){return window.DarbCityScenes.points(id,track).map(([x,y])=>[x*scale,y*scale]);}
 function clear(board){
  const controls=board.closest('.tabletop-card')?.querySelector('.tabletop-controls'),tray=controls?.querySelector('.city-dice');
  if(tray){const hud=tray.querySelector('.tabletop-hud'),center=board.querySelector('.center');if(center&&!center.querySelector('.tabletop-hud')&&hud)center.append(hud);tray.remove();}
  board.querySelectorAll('.city-scene-art,.city-models,.city-route-hints,.city-scene-decks').forEach(e=>e.remove());
  board.classList.remove('city-route-board','city-reference-board');delete board.dataset.route;delete board.dataset.scene;
  for(const tile of board.querySelectorAll('[data-route-original]')){tile.style.cssText=tile.dataset.routeOriginal;delete tile.dataset.routeOriginal;delete tile.dataset.routeX;delete tile.dataset.routeY;}
 }
 function decorateSymbol(symbol,info){
  const d=definition(),r=d?.models[info.art?.key];if(!d||info.art?.sheet!=='landmark'||!r)return false;
  const svg=artwork(d,[d.crop[0]+r[0],d.crop[1]+r[1],r[2],r[3]]);svg.classList.add('inspector-art');symbol.append(svg);symbol.classList.add('has-inspector-art');return true;
 }
 function apply(board,id,options){
  if(!board)return;clear(board);const d=definition(id);if(!d||!options||!board.querySelector('[data-tile]'))return;
  board.classList.add('city-route-board','city-reference-board');board.dataset.scene=id;board.style.setProperty('--city-height',d.height*scale+'px');
  const tiles=[...board.querySelectorAll('[data-tile]')].sort((a,b)=>Number(a.dataset.tile)-Number(b.dataset.tile)),track=options.track,positions=points(track,tiles.length,id);board.dataset.route=track;
  const photo=artwork(d);photo.classList.add('city-scene-art');photo.querySelector('image').addEventListener('error',()=>clear(board),{once:true});board.append(photo);
  for(const [i,tile]of tiles.entries()){
   const [x,y]=positions[i];tile.dataset.routeOriginal=tile.style.cssText;tile.dataset.routeX=String(x);tile.dataset.routeY=String(y);
   tile.style.cssText+=`;left:${x-11}px;top:${y-8}px;width:22px;height:16px;grid-area:auto;`;
  }
  const other=track==='rat'?'fast':'rat',tasks=d.sharedRoad?[]:options.routes[other],otherPoints=points(other,tasks.length,id),hints=document.createElement('div');hints.className='city-route-hints';
  for(const [index,task]of tasks.entries()){
   const [x,y]=otherPoints[index],tile=document.createElement('div');tile.className='city-route-hint';tile.tabIndex=0;tile.setAttribute('role','button');tile.dataset.cityRoute=other;tile.dataset.routeIndex=String(index);tile.style.cssText=`left:${x-11}px;top:${y-8}px;`;
   tile.title=task.title;tile.setAttribute('aria-label',task.title+'، الخانة '+(index+1)+' · '+(other==='fast'?'المسار السريع':'سباق الفئران'));
   const icon=el('svg',{class:'city-task-symbol',viewBox:'0 0 24 24','aria-hidden':'true',focusable:'false'});icon.append(el('use',{href:'#gi-'+task.icon}));tile.append(icon);hints.append(tile);
  }
  const models=document.createElement('div');models.className='city-models';
  for(const [key,r]of Object.entries(d.models)){
   const index=options.routes.rat.findIndex(task=>task.key==='lm_'+key);if(index<0)continue;
   const info=options.inspectRoute('rat',index),owner=options.allPlayers.find(p=>p.id===info.owner?.id),level=Number(info.details.find(([label])=>label==='مستوى التطوير')?.[1])||0;
   const button=document.createElement('button');button.type='button';button.className='city-model';button.dataset.cityProject=key;button.dataset.projectRoute='rat';button.dataset.routeTile=String(index);button.title=info.title;button.setAttribute('aria-label','معلومات '+info.title);
   button.style.cssText=`left:${r[0]*scale}px;top:${r[1]*scale}px;width:${r[2]*scale}px;height:${r[3]*scale}px;`;
   if(owner){button.classList.add('city-model-owned');button.style.setProperty('--city-owner',owner.color);}
   if(level){const badge=document.createElement('span');badge.className='city-model-level';badge.textContent=String(level);button.append(badge);}
   models.append(button);
  }
  const decks=document.createElement('div');decks.className='city-scene-decks';
  const locations=id==='rings'?[[80,17],[410,25],[21,216],[444,211]]:[[91,12],[420,12],[18,d.height-95],[432,d.height-95]];
  for(const [i,type]of ['quiz','family','deal','projects'].entries()){
   const button=document.createElement('button');button.type='button';button.dataset.deck=type;button.className='city-scene-deck';button.style.cssText=`left:${locations[i][0]*scale}px;top:${locations[i][1]*scale}px;width:60px;height:55px;`;button.setAttribute('aria-label',{quiz:'معلومات رزمة الأسئلة',family:'معلومات رزمة العائلة',deal:'معلومات رزمة الفرص',projects:'استعراض مشاريع المسار'}[type]);decks.append(button);
  }
  board.append(models,hints,decks);
  const hud=board.querySelector('.tabletop-hud'),controls=board.closest('.tabletop-card').querySelector('.tabletop-controls');
  if(hud){const tray=document.createElement('div');tray.className='city-dice';tray.append(hud);controls.append(tray);}
 }
 window.DarbCityRoutes={apply,points,decorateSymbol};
})();
