/* Explicit artwork viewports: generated sheets are not equal-cell grids.
   Source pixels are untouched. Nested SVG viewports contain one complete drawing
   with safe padding, and the browser shares the original image download/texture. */
(() => {
 'use strict';
 const NS='http://www.w3.org/2000/svg';
 const imageRoot=new URL('../art/identity/',document.currentScript.src);
 const names=['dice','person','people','shop','ledger','globe','arrow','coin','case','leaf','receipt','heart','star','home','shield','book','gift','chart','bank','package','bulb','bell','coffee','building','plane','health','scale','smile','flag','download','menu','robot','family','graduate','calendar','gavel'];
 const extraNames=['investor','audit','jail','upgrade','bankrupt','jail-exit','rat-race','fast-track','mood-great','mood-good','mood-neutral','mood-worried','mood-exhausted','two-dice','more'];
 const sheets={
  icons:{file:'icons-sheet.png',width:1254,height:1254,regions:[
   [18,50,184,198],[210,27,184,222],[396,36,234,212],[632,43,200,204],[838,72,210,177],[1057,32,190,220],
   [15,265,205,175],[220,265,197,181],[424,265,192,179],[635,267,196,172],[837,267,197,184],[1049,267,194,172],
   [20,443,178,200],[202,454,223,192],[434,450,179,190],[623,449,212,201],[844,449,194,197],[1047,449,191,194],
   [8,649,216,200],[232,660,194,186],[436,644,183,205],[636,662,197,183],[834,643,207,205],[1038,646,213,204],
   [8,852,216,174],[228,847,193,171],[433,847,184,181],[636,853,188,177],[843,849,194,179],[1049,854,191,176],
   [22,1041,184,173],[225,1022,173,201],[421,1023,205,200],[626,1040,211,183],[840,1025,203,190],[1044,1029,200,195]
  ]},
  extra:{file:'icons-extra-sheet.png',width:1250,height:750,regions:[
   [16,17,220,230],[263,40,235,202],[533,35,184,207],[766,20,221,224],[1008,32,235,220],
   [17,270,220,213],[263,279,240,203],[514,265,224,220],[763,278,216,205],[1009,281,225,202],
   [17,499,220,224],[267,499,220,224],[517,499,220,224],[767,498,216,229],[1008,498,225,230]
  ]},
  reactions:{file:'reactions-sheet.png',width:1254,height:1254,regions:[
   [55,59,257,256],[350,59,260,256],[640,59,263,256],[940,59,265,256],
   [50,336,263,265],[348,336,263,257],[640,336,263,260],[943,334,257,275],
   [65,614,230,271],[346,608,265,280],[647,642,260,249],[960,638,242,252],
   [39,905,287,293],[325,922,300,260],[638,901,268,294],[925,909,305,291]
  ]},
  cards:{file:'cards-sheet.png',width:1254,height:1254,regions:Array.from({length:9},(_,i)=>[i%3*418+4,Math.floor(i/3)*418+4,410,410])},
  cardExtra:{file:'cards-extra-sheet.png',width:1024,height:1024,regions:[[3,3,507,492],[516,3,505,492],[3,503,507,518],[516,503,505,518]]},
  goods:{file:'goods-sheet.png',width:1536,height:1024,regions:[[20,65,495,440],[540,10,480,500],[1110,25,400,485],[25,540,490,430],[555,525,465,475],[1025,570,490,405]]},
  avatars:{file:'characters-sheet.png',width:1254,height:1254,regions:Array.from({length:16},(_,i)=>[i%4*313.5+1,Math.floor(i/4)*313.5+1,311.5,311.5])}
 };
 function paint(host,sheetName,index,padding=6){
  const sheet=sheets[sheetName],region=sheet?.regions[index];if(!region||!host)return;
  const key=sheetName+':'+index+':'+padding;
  if(host.dataset.spriteRegion===key&&host.querySelector(':scope > .sprite-viewport'))return;
  host.querySelector(':scope > .sprite-viewport')?.remove();
  const outer=document.createElementNS(NS,'svg');outer.setAttribute('viewBox','0 0 100 100');outer.setAttribute('aria-hidden','true');outer.setAttribute('focusable','false');outer.classList.add('sprite-viewport');
  const available=100-2*padding,scale=available/Math.max(region[2],region[3]);
  const width=region[2]*scale,height=region[3]*scale;
  const crop=document.createElementNS(NS,'svg');crop.setAttribute('x',String((100-width)/2));crop.setAttribute('y',String((100-height)/2));crop.setAttribute('width',String(width));crop.setAttribute('height',String(height));crop.setAttribute('viewBox',region.join(' '));crop.setAttribute('preserveAspectRatio','none');crop.setAttribute('overflow','hidden');
  const image=document.createElementNS(NS,'image');image.setAttribute('href',new URL(sheet.file,imageRoot).href);image.setAttribute('width',String(sheet.width));image.setAttribute('height',String(sheet.height));image.setAttribute('aria-hidden','true');
  crop.append(image);outer.append(crop);
  if(host.namespaceURI===NS)host.setAttribute('viewBox','0 0 100 100');
  host.classList.add('sprite-framed');host.dataset.spriteRegion=key;host.append(outer);
 }
 function percentageIndex(el,columns,rows){return Math.round(parseFloat(el.style.getPropertyValue('--ix')||'0')/100*(columns-1))+columns*Math.round(parseFloat(el.style.getPropertyValue('--iy')||'0')/100*(rows-1));}
 function hydrate(root){
  if(root.nodeType!==1)return;
  const selector='.ui-icon,.illustrated-icon,.goods-art[data-goods]';
  const nodes=[...(root.matches(selector)?[root]:[]),...root.querySelectorAll(selector)];
  for(const el of nodes){
   if(el.matches('.identity-status'))continue;
   if(el.matches('.goods-art')){paint(el,'goods',['dates','coffee','perfume','fabric','honey','saffron'].indexOf(el.dataset.goods));continue;}
   if(el.matches('.identity-avatar')){paint(el,'avatars',percentageIndex(el,4,4),0);continue;}
   if(el.matches('.identity-extra')){paint(el,'reactions',percentageIndex(el,4,4));continue;}
   let name=el.dataset.icon||el.querySelector('use')?.getAttribute('href')?.split('#').pop().replace(/^gi-/,'');
   if(name==='menu')name='more';
   if(extraNames.includes(name))paint(el,'extra',extraNames.indexOf(name));
   else if(names.includes(name))paint(el,'icons',names.indexOf(name));
  }
 }
 window.DarbSprites={paint,hydrate,sheets,names,extraNames};
})();
