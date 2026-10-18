/* Real CSS solid geometry: six-sided buildings, polygonal cylinders and extruded silhouettes. */
(() => {
  'use strict';
  const colors={ivory:'#f4ead7',blue:'#9fbfce',sage:'#a6bbaa',coral:'#dbab94',gold:'#e9c779',purple:'#b9abc9',ink:'#62594f'};
  const faces='<i class="face top"></i><i class="face bottom"></i><i class="face south"></i><i class="face north"></i><i class="face east"></i><i class="face west"></i>';
  function box(w,d,h,x=0,y=0,z=0,color=colors.ivory,cls='') {
    return `<span class="solid ${cls}" style="--w:${w}px;--d:${d}px;--h:${h}px;--x:${x}px;--y:${y}px;--z:${z}px;--paint:${color}">${faces}</span>`;
  }
  function cylinder(r,h,x=0,y=0,z=0,color=colors.gold){
    let out=`<span class="cylinder" style="--r:${r}px;--h:${h}px;--x:${x}px;--y:${y}px;--z:${z}px;--paint:${color}"><i class="cap top"></i><i class="cap bottom"></i>`;
    for(let i=0;i<12;i++){const a=i*Math.PI/6;out+=`<i class="cylinder-side" style="width:${2*r*Math.tan(Math.PI/12)+.3}px;transform:translate3d(${-Math.sin(a)*r}px,${Math.cos(a)*r}px,${h/2}px) rotateZ(${i*30}deg) rotateX(90deg)"></i>`;}
    return out+'</span>';
  }
  function emblem(kind,color){
    const shapes={star:Array.from({length:10},(_,i)=>{const a=i*Math.PI/5-Math.PI/2,r=i%2?6:14;return [16+Math.cos(a)*r,16+Math.sin(a)*r]}),heart:[[16,28],[3,16],[2,10],[5,5],[11,4],[16,9],[21,4],[27,5],[30,10],[29,16]],shield:[[3,4],[16,1],[29,4],[27,21],[16,30],[5,21]]};
    const points=shapes[kind]||shapes.star,poly=points.map(p=>p.map(v=>v+'px').join(' ')).join(',');
    let out=`<span class="extrusion" style="--paint:${color}"><i class="profile front" style="clip-path:polygon(${poly})"></i><i class="profile back" style="clip-path:polygon(${poly})"></i>`;
    points.forEach((a,i)=>{const b=points[(i+1)%points.length],dx=b[0]-a[0],dy=b[1]-a[1];out+=`<i class="profile-edge" style="width:${Math.hypot(dx,dy)+.4}px;left:${a[0]-16}px;top:${a[1]-16}px;transform:rotateZ(${Math.atan2(dy,dx)}rad) rotateX(90deg)"></i>`;});
    return out+'</span>';
  }
  function house(color=colors.coral,tall=18){return box(24,21,tall,0,0,0,colors.ivory,'facade')+`<span class="roof-half" style="transform:translate3d(-7px,0,${tall+4}px) rotateY(-25deg)">${box(17,27,2,0,0,0,color,'roof')}</span><span class="roof-half" style="transform:translate3d(7px,0,${tall+4}px) rotateY(25deg)">${box(17,27,2,0,0,0,color,'roof')}</span>`+box(5,6,9,7,-3,tall+3,color);}
  function bank(){return box(30,24,3,0,0,0)+box(27,20,15,0,-3,3,colors.blue,'facade')+[-10,-3,4,11].map(x=>cylinder(2,17,x,10,3,colors.ivory)).join('')+box(33,27,4,0,0,20,colors.coral);}
  function coins(){return [[-8,-4,3],[5,4,2],[-6,9,1]].map(([x,y,n])=>Array.from({length:n},(_,i)=>cylinder(8,4,x,y,i*4,colors.gold)).join('')).join('');}
  function book(){return box(27,21,3,0,0,0,colors.purple)+box(24,19,7,0,0,3,colors.ivory,'pages')+box(27,21,3,0,0,10,colors.purple)+box(4,21,13,-12,0,0,colors.purple);}
  function gift(){return box(24,23,19,0,0,0,colors.coral)+box(27,26,4,0,0,19,colors.ivory)+box(4,26,1,0,0,23,colors.purple)+box(27,4,1,0,0,23,colors.purple)+box(4,1,19,0,12,0,colors.purple);}
  const roles={trader:['#bd8968','#708f87','#51483e'],teacher:['#e4b68a','#b8bd9d','#51483e'],nurse:['#c38e72','#e9e0d2','#e6ddcf','hijab'],engineer:['#9d7054','#a4bfc4','#55443b','helmet'],driver:['#b47d57','#a8b6c9','#51483e'],doctor:['#d1a27e','#e8e4db','#53483d'],accountant:['#d9ad88','#b6aec8','#5b5148'],grocer:['#d8ad8e','#c5b4a1','#c6c1b6'],farmer:['#ab7c57','#a6b59b','#726347','hat'],carpenter:['#c78e64','#c2a184','#51483e'],chef:['#d0a07b','#eee4d5','#e7ddcb','chef'],programmer:['#c89071','#b8abc9','#b5a2c3','hijab'],pharmacist:['#d6a17e','#e7dfcf','#d7b3a2','hijab'],pilot:['#d8aa85','#95a9bb','#5e6f80','hat']};
  function person(role='teacher',small=false){
    const [skin,shirt,hair,hat]=Object.prototype.hasOwnProperty.call(roles,role)?roles[role]:roles.teacher;
    let result=box(13,10,17,0,0,9,shirt,'torso')+box(5,7,10,-4,0,0,colors.ink)+box(5,7,10,4,0,0,colors.ink)+box(5,7,14,-9,0,11,shirt)+box(5,7,14,9,0,11,shirt)+box(5,7,4,-9,0,9,skin)+box(5,7,4,9,0,9,skin);
    result+=`<span class="character-head ${hat==='hijab'?'hijab':''}">`+[5.5,8,9.5,10,9.5,8,5.5].map((r,i)=>cylinder(r,2.5,0,0,27+i*2.5,hat==='hijab'?hair:skin)).join('')+`<i class="minifig-face" style="--skin:${skin}"></i></span>`;
    if(hat==='hijab')result+=box(20,13,4,0,0,25,hair);
    else result+=cylinder(8,3,0,0,43,hair);
    if(hat==='helmet'||hat==='hat')result+=box(23,19,2,0,0,44,hat==='helmet'?colors.gold:hair)+box(18,14,5,0,0,46,hat==='helmet'?colors.gold:hair);
    if(hat==='chef')result+=cylinder(11,8,0,0,43,colors.ivory)+cylinder(9,5,0,0,51,colors.ivory);
    if(['doctor','nurse','pharmacist'].includes(role))result+=box(3,1,9,3,5.5,14,colors.coral)+box(8,1,3,3,5.5,17,colors.coral);
    if(role==='programmer'||role==='accountant')result+=box(16,9,2,0,8,16,colors.blue)+box(16,2,11,0,12,18,colors.blue);
    return `<span class="toy-person ${small?'small-person':''}" style="--skin:${skin};--hair:${hair}">${result}</span>`;
  }
  const cache=new Map();
  function geometry(key){
    if(cache.has(key))return cache.get(key);
    let model;
    if(key.startsWith('player_'))model=person(key.slice(7));
    else if(key==='payday')model=coins();
    else if(key==='lm_bank'||key==='jamia')model=bank();
    else if(key==='lm_tower'||key==='biz')model=box(24,22,40,0,0,0,colors.blue,'facade')+box(18,16,8,0,0,40,colors.ivory,'facade');
    else if(key==='lm_airport')model=box(31,20,12,0,0,0,colors.blue,'facade')+box(8,8,30,10,-6,0,colors.ivory)+box(14,12,6,10,-6,30,colors.blue);
    else if(key==='lm_hospital')model=house(colors.blue,24)+box(4,1,12,0,11,8,colors.coral)+box(12,1,4,0,11,12,colors.coral);
    else if(['learn','quiz','lm_uni'].includes(key))model=book()+(key==='quiz'?cylinder(3,7,0,0,13,colors.ink)+cylinder(9,9,0,0,20,colors.gold)+cylinder(6,4,0,0,29,colors.gold):'');
    else if(key==='dream')model=cylinder(15,4,0,0,0)+box(7,7,9,0,0,4,colors.ivory)+emblem('star',colors.gold);
    else if(['family','child','fun'].includes(key))model=cylinder(15,3,0,0,0,colors.ivory)+emblem('heart',colors.coral);
    else if(key==='insure')model=cylinder(15,3,0,0,0,colors.ivory)+emblem('shield',colors.blue);
    else if(key==='charity')model=gift();
    else if(key==='order')model=box(26,23,21,0,0,0,'#d5b48c')+box(5,23,1,0,0,21,colors.ivory)+box(5,1,21,0,12,0,colors.ivory);
    else if(['lawsuit','auction','audit'].includes(key))model=cylinder(15,4,0,0,0,colors.ivory)+box(5,6,24,0,0,4,colors.ink)+box(24,13,9,0,0,25,colors.coral);
    else if(key==='partner')model='<span class="partner-one">'+person('engineer',true)+'</span><span class="partner-two">'+person('programmer',true)+'</span>';
    else if(['tax','doodad','layoff'].includes(key))model=book()+cylinder(7,4,7,5,13,colors.gold);
    else model=house(key==='souk'||key==='lm_cafe'?colors.coral:colors.blue,key==='lm_hotel'?28:18);
    cache.set(key,model);return model;
  }
  function mount(cells,retained=new Map()){
    for(const tile of cells.querySelectorAll('[data-tile]')){
      const key=tile.dataset.model||'deal';
      const kept=retained.get(`tile:${tile.dataset.tile}:${key}`);
      if(kept){tile.append(kept);continue;}
      const miniature=document.createElement('span');miniature.className='board-miniature';miniature.dataset.model=key;miniature.setAttribute('aria-hidden','true');
      miniature.innerHTML='<span class="miniature-shadow"></span><span class="miniature-body">'+geometry(key)+'</span>';
      tile.append(miniature);
    }
    for(const deck of cells.querySelectorAll('[data-deck]')){
      deck.classList.add('object-pedestal');
      const kept=retained.get('deck:'+deck.dataset.deck);
      if(kept){deck.append(kept);continue;}
      const miniature=document.createElement('span');miniature.className='board-miniature';miniature.setAttribute('aria-hidden','true');miniature.innerHTML='<span class="miniature-body">'+geometry({deal:'souk',family:'family',quiz:'quiz'}[deck.dataset.deck])+'</span>';deck.append(miniature);
    }
  }
  let size=135;
  try{const saved=Number(localStorage.getItem('darb-model-size'));if(saved>=100&&saved<=180)size=saved;}catch(_){}
  function setSize(value){size=Math.max(100,Math.min(180,Number(value)||135));document.getElementById('board').style.setProperty('--object-size',size/100);const control=document.querySelector('[data-model-size]');if(control)control.value=size;const output=document.querySelector('[data-model-size-output]');if(output)output.textContent=size+'٪';try{localStorage.setItem('darb-model-size',size)}catch(_){}window.DarbTabletop?.refresh();}
  document.querySelector('[data-model-size]')?.addEventListener('input',event=>setSize(event.target.value));
  setSize(size);
  window.DarbModels={mount,person,geometry,setSize};
})();
