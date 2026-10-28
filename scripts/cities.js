/* Setup preference selects the next match; rendering always follows the saved host board. */
(() => {
 'use strict';
 const cities=[
  ['architecture','مدينة المعمار','مجسمات واقعية، خشب دافئ وساحات حجرية.'],
  ['cartoon','مدينة الحكايات','مدينة كرتونية مرسومة بعمق وألوان مريحة.'],
  ['ivory','مدينة العاج','ماكيت معماري هادئ بتفاصيل عاجية ولمسات ذهبية.'],
  ['harbor','مدينة المرفأ','قنوات مائية وجسور وأحياء ساحلية.'],
  ['rings','مدينة المدار','تكوين دائري بمسارات متداخلة.'],
  ['paper','مدينة الورق','طبقات ورقية ومجسمات كرتونية ملموسة.'],
  ['strategy','مدينة الآفاق','منظور أعلى وتفاصيل منخفضة لسهولة القراءة.'],
  ['districts','مدينة الأحياء','أربعة أحياء متنوعة حول حديقة مشتركة.'],
  ['night','مدينة الأنوار','أجواء مسائية وإضاءة نوافذ دافئة.'],
  ['crystal','مدينة البلور','مجسمات على قواعد شفافة وطاولة خشبية فاتحة.']
 ];
 let routeOptions=null,matchId=null;
 const ready=new Set(cities.map(([id])=>id)),key='darb-city-view';
 let selected='architecture',preview=0,origin=null;
 try{const saved=localStorage.getItem(key);if(ready.has(saved))selected=saved;}catch(_){}
 const dialog=document.getElementById('city-picker'),list=document.getElementById('city-list'),apply=document.getElementById('city-apply');
 const name=()=>cities.find(([id])=>id===selected)?.[1]||'الطاولة السابقة';
 function updateLabels(){
  document.querySelectorAll('[data-city-name]').forEach(el=>el.textContent=name());
 }
 function activate(id){
  if(!ready.has(id))return;
  selected=id;document.documentElement.dataset.city=id;
  try{localStorage.setItem(key,id);}catch(_){}
  updateLabels();const board=document.getElementById('board');mount(board);window.DarbTabletopArt?.fitLabels(board);window.DarbTabletop?.refresh();window.DarbCamera?.labelsChanged();window.DarbCamera?.viewChanged();
 }
 function paintPreview(host,index){
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox',`${index%2*512} ${Math.floor(index/2)*288} 512 ${index>=8?384:288}`);
  svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
  const image=document.createElementNS(ns,'image');image.setAttribute('href','art/cities/concepts.webp');image.setAttribute('width','1024');image.setAttribute('height','1536');svg.append(image);host.replaceChildren(svg);
 }
 function showPreview(index){
  preview=index;const [id,title,description]=cities[index];
  paintPreview(document.getElementById('city-preview'),index);
  const spec=DarbCityScenes.create(id);
  document.getElementById('city-preview-title').textContent=title;
  document.getElementById('city-preview-description').textContent=description+' · '+spec.rat.length+' خانة لبناء الدخل، و'+spec.fast.length+' خانة لمرحلة الأحلام.';
  document.getElementById('city-status').textContent=ready.has(id)?'متاحة للعب الآن':'معاينة معتمدة · المدينة قيد التجهيز';
  apply.disabled=!ready.has(id);apply.textContent=ready.has(id)?'العب في هذه المدينة':'قيد التجهيز';
  for(const button of list.querySelectorAll('button'))button.setAttribute('aria-pressed',String(Number(button.dataset.cityIndex)===index));
 }
 function open(){
  origin=document.activeElement;
  const guide=document.getElementById('camera-guide');if(guide.open)guide.close();
  if(!list.children.length)for(const [index,[id,title]] of cities.entries()){
   const button=document.createElement('button');button.type='button';button.dataset.cityIndex=String(index);button.setAttribute('aria-pressed','false');
   const image=document.createElement('span');image.className='city-thumb';image.setAttribute('aria-hidden','true');paintPreview(image,index);
   const label=document.createElement('b');label.textContent=(index+1)+' · '+title;
   const state=document.createElement('small');state.textContent=ready.has(id)?'متاحة للعب':'معاينة';button.append(image,label,state);button.onclick=()=>showPreview(index);list.append(button);
  }
  showPreview(selected==='classic'?preview:cities.findIndex(([id])=>id===selected));if(!dialog.open)dialog.showModal();
 }
 function close(){dialog.close();if(origin?.isConnected&&!origin.closest('dialog:not([open])'))origin.focus({preventScroll:true});else document.getElementById('camera-help').focus({preventScroll:true});}
 apply.onclick=()=>{activate(cities[preview][0]);close();};
 document.getElementById('city-classic').onclick=()=>{activate('classic');close();};
 document.getElementById('city-random').onclick=()=>{const available=cities.filter(([id])=>ready.has(id));activate(available[Math.floor(Math.random()*available.length)][0]);close();};
 dialog.querySelector('[data-close-cities]').onclick=close;
 document.getElementById('choose-city-play').onclick=()=>{if(!matchId)open();};
 function mountSetup(anchor){
  const row=document.createElement('div');row.className='city-setup';
  const text=document.createElement('p');text.textContent='مدينتك: ';const value=document.createElement('b');value.dataset.cityName='';value.textContent=name();text.append(value);
  const button=document.createElement('button');button.type='button';button.id='choose-city-setup';button.textContent='اختر مدينتك';button.setAttribute('aria-haspopup','dialog');button.onclick=open;
  const note=document.createElement('small');note.textContent='المدينة تحدد الخانات والمهام للمباراة كلها؛ المبالغ الأساسية ثابتة. يتغير توزيع الأحداث وطول الدورة بين المدن.';
  row.append(text,button,note);anchor.before(row);
 }
 function mount(board,options){
  if(options)routeOptions=options;
  window.DarbCityRoutes?.apply(board,routeOptions?.boardId||'legacy',routeOptions);
 }

 activate(selected);
 window.DarbCities={open,mountSetup,name,mount,selection:()=>selected,setMatch(id){matchId=id;const button=document.getElementById('choose-city-play');button.disabled=!!id;button.setAttribute('aria-label',id==='legacy'?'مباراة محفوظة باللوحة السابقة':id?'مدينة المباراة ثابتة حتى النهاية':'اختر مدينة المباراة');document.querySelectorAll('#choose-city-play [data-city-name]').forEach(el=>el.textContent=id==='legacy'?'اللوحة السابقة':cities.find(([key])=>key===(id||selected))?.[1]||'');}};
})();
