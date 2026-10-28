/* Physical routes map stable rule indices onto city coordinates; no match mutations. */
(() => {
 'use strict';
 const NS='http://www.w3.org/2000/svg';
 const outer=[[110,595],[530,595],[595,530],[595,110],[530,45],[110,45],[45,110],[45,530]];
 const modelOrder=['bank','uni','hospital','hotel','mall','cafe'];
 function sample(vertices,count){
  const lengths=vertices.map((p,i)=>Math.hypot(vertices[(i+1)%vertices.length][0]-p[0],vertices[(i+1)%vertices.length][1]-p[1]));
  const total=lengths.reduce((a,b)=>a+b,0);
  return Array.from({length:count},(_,i)=>{let distance=i*total/count,edge=0;while(distance>lengths[edge]&&edge<lengths.length-1)distance-=lengths[edge++];const p=vertices[edge],q=vertices[(edge+1)%vertices.length],t=distance/lengths[edge];return [p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t];});
 }
 function points(track,count){return track==='fast'?Array.from({length:count},(_,i)=>[320+145*Math.sin(i*2*Math.PI/count),320+145*Math.cos(i*2*Math.PI/count)]):sample(outer,count);}
 function element(tag,attributes){const e=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attributes))e.setAttribute(k,String(v));return e;}
 function modelArt(key){
  let index=modelOrder.indexOf(key),file='architecture-models.webp',width=1536,height=1024,x,y,size;
  if(index>=0){x=index%3*512+3;y=Math.floor(index/3)*512+3;size=506;}
  else{index=['tower','airport'].indexOf(key);if(index<0)return null;file='fast-models.webp';width=1774;height=887;x=index*887+3;y=3;size=881;}
  const svg=element('svg',{viewBox:`${x} ${y} ${size} ${size}`,'aria-hidden':'true',focusable:'false'});
  const image=element('image',{href:'art/cities/'+file,width,height});svg.append(image);return svg;
 }
 function decorateSymbol(symbol,info){
  if(document.documentElement.dataset.city!=='architecture'||info.art?.sheet!=='landmark')return false;
  const svg=modelArt(info.art.key);if(!svg)return false;
  svg.classList.add('inspector-art');svg.querySelector('image').addEventListener('error',()=>{svg.remove();symbol.classList.remove('has-inspector-art');},{once:true});symbol.append(svg);symbol.classList.add('has-inspector-art');return true;
 }
 function clear(board){
  board.querySelectorAll('.city-roads,.city-models,.city-route-hints').forEach(e=>e.remove());board.classList.remove('city-route-board');delete board.dataset.route;
  for(const tile of board.querySelectorAll('[data-route-original]')){tile.style.cssText=tile.dataset.routeOriginal;delete tile.dataset.routeOriginal;delete tile.dataset.routeX;delete tile.dataset.routeY;}
 }
 function apply(board,enabled,options){
  if(!board)return;clear(board);if(!enabled||!board.querySelector('[data-tile]'))return;
  board.classList.add('city-route-board');
  const tiles=[...board.querySelectorAll('[data-tile]')].sort((a,b)=>Number(a.dataset.tile)-Number(b.dataset.tile));
  const track=tiles.length===20?'fast':'rat',positions=points(track,tiles.length);board.dataset.route=track;
  const roads=element('svg',{viewBox:'0 0 640 640',class:'city-roads','aria-hidden':'true',focusable:'false'});
  for(const y of [180,240,300,360,420]){roads.append(element('ellipse',{cx:123,cy:y,rx:19,ry:22,fill:'#c7cdb5'}),element('circle',{cx:120,cy:y-3,r:10,fill:'#91a27c'}),element('circle',{cx:127,cy:y+5,r:7,fill:'#a4b38c'}));}
  const outerPath='M'+outer.map(p=>p.join(',')).join('L')+'Z';
  roads.append(element('path',{d:outerPath,class:'city-road-base'}),element('circle',{cx:320,cy:320,r:145,class:'city-fast-road'}));
  const models=document.createElement('div');models.className='city-models';
  function addModel(key,title,label,index,modelTrack,x,y,ownerColor,level){
   const vx=320-x,vy=320-y,distance=Math.hypot(vx,vy),offset=modelTrack==='fast'?-65:key==='mall'?55:70;
   const px=x+vx/distance*offset,py=y+vy/distance*offset;
   roads.append(element('path',{d:`M${x},${y}L${px},${py}`,class:'city-project-link'}));
   const button=document.createElement('button');button.type='button';button.className='city-model';button.dataset.cityProject=key;button.dataset.routeTile=String(index);button.dataset.projectRoute=modelTrack;
   button.style.cssText=`left:${px-35}px;top:${py-35}px;`;
   button.setAttribute('aria-label','معلومات '+title+'، مرتبط بالخانة '+(index+1));button.title=title;
   const fallback=document.createElement('span');fallback.className='city-model-placeholder';fallback.setAttribute('aria-hidden','true');fallback.textContent={bank:'🏦',uni:'🎓',hospital:'🏥',hotel:'🏨',mall:'🏬',cafe:'☕',tower:'🏢',airport:'✈️'}[key]||'🏛️';button.append(fallback);
   const art=modelArt(key);if(art){art.querySelector('image').addEventListener('load',()=>fallback.remove(),{once:true});art.querySelector('image').addEventListener('error',()=>art.remove(),{once:true});button.append(art);}
   const caption=document.createElement('span');caption.className='city-model-caption';caption.textContent=label;button.append(caption);
   if(ownerColor){button.style.setProperty('--city-owner',ownerColor);button.classList.add('city-model-owned');}
   if(Number(level)){const badge=document.createElement('span');badge.className='city-model-level';badge.textContent=String(level);button.append(badge);}
   models.append(button);
  }
  for(const [i,tile] of tiles.entries()){
   const [x,y]=positions[i],width=track==='fast'?42:38,height=30;
   tile.dataset.routeOriginal=tile.style.cssText;tile.dataset.routeX=String(x);tile.dataset.routeY=String(y);
   tile.style.cssText+=`;left:${x-width/2}px;top:${y-height/2}px;width:${width}px;height:${height}px;grid-area:auto;`;
   const key=tile.dataset.landmark;if(key)addModel(key,tile.title,tile.querySelector('.tile-name').textContent,Number(tile.dataset.tile),track,x,y,tile.dataset.ownerColor,tile.dataset.level);
  }
  const hints=document.createElement('div');hints.className='city-route-hints';
  const other=track==='rat'?'fast':'rat',tasks=options?.routes?.[other]||[],otherPoints=points(other,tasks.length);
  for(const [index,task] of tasks.entries()){
   const [x,y]=otherPoints[index],tile=document.createElement('div');tile.className='city-route-hint';tile.tabIndex=0;tile.setAttribute('role','button');tile.dataset.cityRoute=other;tile.dataset.routeIndex=String(index);
   tile.style.cssText=`left:${x-19}px;top:${y-14}px;background:var(${task.color});`;
   tile.title=task.title;tile.setAttribute('aria-label',task.title+'، الخانة '+(index+1)+' · '+(other==='fast'?'المسار السريع':'سباق الفئران')+'، للاطلاع');
   if(task.key.startsWith('lm_')){
    const info=options.inspectRoute?.(other,index),key=task.key.slice(3),owner=options.allPlayers?.find(p=>p.id===info?.owner?.id),level=info?.details?.find(([label])=>label==='مستوى التطوير')?.[1];
    addModel(key,task.title,task.title,index,other,x,y,owner?.color,level);
   }
   const icon=element('svg',{class:'city-task-symbol',viewBox:'0 0 24 24','aria-hidden':'true',focusable:'false'});icon.append(element('use',{href:'#gi-'+task.icon}));tile.append(icon);hints.append(tile);
  }
  board.append(roads,models,hints);
 }
 window.DarbCityRoutes={apply,points,decorateSymbol};
})();
