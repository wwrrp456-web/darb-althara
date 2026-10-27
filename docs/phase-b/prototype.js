/* Review prototype only. No imports from the game engine, storage or service worker. */
(() => {
'use strict';
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const ar = n => n.toLocaleString('ar-SA');
const asset = path => window.REVIEW_ASSETS?.[path] || path;
const params = new URLSearchParams(location.search);
const state = {logo:['a','b','c'].includes(params.get('logo'))?params.get('logo'):'a',count:params.get('players')==='8'?8:2,mode:'family',ending:'dreams',limit:12,phase:0,chosen:null,zoom:1,x:0,y:0};
const people=[{name:'محسن',job:'معلّم',art:'teacher',cash:15000},{name:'مريم',job:'مبرمجة',art:'programmer',cash:5500},{name:'ليلى',job:'ممرّضة',art:'nurse',cash:3500},{name:'آدم',job:'مهندس',art:'engineer',cash:4200},{name:'سامي',job:'سائق',art:'driver',cash:2200},{name:'نور',job:'صاحبة بقالة',art:'grocer',cash:3800},{name:'لينا',job:'صاحبة مطعم',art:'chef',cash:3000},{name:'سارة',job:'صيدلانية',art:'pharmacist',cash:5000}];
const concepts=[{id:'a',code:'أ',name:'درب النجمة',story:'بوابة مفتوحة، ودرب ينتهي بنجمة. يربط هدف اللعبة برحلة مفهومة من أول نظرة.',strength:'الأقرب إلى معنى الرحلة والهدف. التوصية الأولية.',risk:'تمييزه عن شعار اللعبة السابق يحتاج ضبطاً نهائياً للكتابة والنسب.'},{id:'b',code:'ب',name:'بذرة الفرص',story:'بذرة ذهبية تتحول إلى ورقتين؛ النمو نتيجة قرارات صغيرة متراكمة.',strength:'هادئ ومناسب للعائلة؛ أقل اعتماداً على رموز المال.',risk:'قد يُقرأ كعلامة بيئية؛ اختبر ارتباطه باللعبة قبل اعتماده.'},{id:'c',code:'ج',name:'أفق الحلم',story:'شراع ذهبي يتحرك نحو أفق جديد. الاستقلال رحلة تختار فيها وجهتك.',strength:'شخصية مختلفة وواضحة، ومساحة لقصص مغامرة متعددة الثقافات.',risk:'قد يوحي بالسفر أكثر من المال؛ يحتاج اختبار المعنى مع الجمهور.'}];
function esc(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function renderConcepts(){
 $('#concept-grid').innerHTML=concepts.map(c=>`<article class="concept-card ${state.logo===c.id?'selected':''}"><div class="concept-id"><b>المقترح ${c.code}</b><span>${state.logo===c.id?'قيد المعاينة':'للمقارنة'}</span></div><img class="concept-mark" src="${asset(`marks/${c.id}-mark.svg`)}" alt="رمز ${c.name}"><img class="concept-wordmark" src="${asset(`marks/${c.id}-wordmark.svg`)}" alt="درب الثراء — صياغة ${c.name}"><h2>${c.name}</h2><p>${c.story}</p><div class="application-row"><img class="icon-32" src="${asset(`marks/${c.id}-mark.svg`)}" alt="رمز ${c.name} بحجم ٣٢ بكسلاً"><span>٣٢px بالحجم الفعلي<br>وأيقونة تطبيق تجريبية</span><img class="app-icon" src="${asset(`marks/${c.id}-mark.svg`)}" alt="أيقونة تطبيق ${c.name}"></div><div class="dark-sample"><img src="${asset(`marks/${c.id}-light.svg`)}" alt="شعار ${c.name} على خلفية داكنة"></div><p class="helper"><b>${c.strength}</b><br>${c.risk}</p><button class="${state.logo===c.id?'primary':'quiet'}" data-concept="${c.id}" aria-pressed="${state.logo===c.id}">${state.logo===c.id?'هذا الاتجاه في المعاينة':'عاين هذا الاتجاه'}</button></article>`).join('');
}
function selectLogo(id){state.logo=id;$$('.brand-lockup').forEach(e=>e.src=asset(`marks/${id}-lockup.svg`));$('.hero-mark').src=asset(`marks/${id}-mark.svg`);const center=$('.map-center img');if(center)center.src=asset(`marks/${id}-mark.svg`);renderConcepts();}
function renderPlayers(){
 $('#player-count').value=state.count;
 $('#player-editor').innerHTML=people.slice(0,state.count).map((p,i)=>`<div class="player-row"><span class="portrait ${p.art}" aria-hidden="true"></span><label><small>اسم اللاعب ${ar(i+1)}</small><input data-player-name="${i}" maxlength="14" value="${esc(p.name)}" aria-label="اسم اللاعب ${ar(i+1)}"></label><span>${p.job}</span></div>`).join('');
 $('#review-players').innerHTML=people.slice(0,state.count).map(p=>`<div class="player-row"><span class="portrait ${p.art}" aria-hidden="true"></span><span class="player-meta"><b>${esc(p.name)}</b><small>${p.job}</small></span></div>`).join('');
 $('#panel-players').innerHTML=people.slice(0,state.count).map((p,i)=>`<button class="panel-player ${i===0?'current':''}" data-person="${i}"><span class="portrait ${p.art}" aria-hidden="true"></span><span><b>${ar(i+1)} · ${esc(p.name)}</b><small>${p.job}</small></span></button>`).join('');
 $('.turn-person b').innerHTML=`دور ${esc(people[0].name)} <span class="turn-number">١</span>`;$('#panel-count').textContent=state.count===2?'لاعبان':'٨ لاعبين';$('#crowd-count').textContent=`${ar(state.count)} هنا`;
 $('#crowd-button').setAttribute('aria-label',`اختيار لاعب من ${ar(state.count)} لاعبين في الخانة`);
 $('#crowd-list').innerHTML=people.slice(0,state.count).map((p,i)=>`<button class="crowd-player" data-person="${i}"><span class="portrait ${p.art}" aria-hidden="true"></span><span><b>${ar(i+1)} · ${esc(p.name)}</b><small>${p.job}</small></span></button>`).join('');
 $('#portrait-player-strip').innerHTML=people.slice(0,state.count).map((p,i)=>`<button class="strip-player quiet" data-person="${i}"><span class="portrait ${p.art}" aria-hidden="true"></span><span>${ar(i+1)} · ${esc(p.name)}</span></button>`).join('');
 const badge=$('.map-cluster');if(badge)badge.textContent=ar(state.count);
}
function endingText(){return state.ending==='dreams'?'تحقيق الأحلام':state.ending==='rounds'?`${ar(state.limit)} جولة`:`${ar(state.limit)} دقيقة`}
function updateEnding(){
 state.ending=$('input[name=ending]:checked').value;
 $('.limit-field').hidden=state.ending==='dreams';$('#limit-label').textContent=state.ending==='time'?'الوقت بالدقائق':'عدد الجولات';
 $('#ending-limit').max=state.ending==='time'?240:99;
 $('#ending-explanation').textContent=state.ending==='dreams'?'تحقيق الأحلام وفق نظام اللعبة الحالي.':state.ending==='rounds'?'تكتمل الجولة المحددة بأدوار متساوية، ثم تستخدم تسوية اللعبة الحالية.':'بعد انتهاء الوقت تُستكمل الجولة الحالية ويُحسم القرار الجاري، ثم تستخدم تسوية اللعبة الحالية.';
}
function renderSettings(){
 state.mode=$('input[name=mode]:checked').value;
 state.ending=$('input[name=ending]:checked').value;
 state.limit=Math.max(1,Math.min(state.ending==='time'?240:99,Number($('#ending-limit').value)||12));$('#ending-limit').value=state.limit;
 $('#settings-summary').innerHTML=`<div><dt>اللاعبون</dt><dd>${ar(state.count)}</dd></div><div><dt>النمط</dt><dd>${state.mode==='family'?'عائلي':'موسع'}</dd></div><div><dt>النهاية</dt><dd>${endingText()}</dd></div><div><dt>الإرشاد</dt><dd>${state.mode==='family'?'خطوة بخطوة':'عند الطلب'}</dd></div>`;
 renderPlayers();
}
function show(screen){
 if(!document.getElementById(screen)?.classList.contains('screen'))screen='home';
 $$('.screen').forEach(e=>e.hidden=e.id!==screen);
 document.body.dataset.screen=screen;
 const target=document.getElementById(screen);target.scrollTop=0;
 if(screen==='summary')renderSettings();
 if(screen==='play'){renderPlayers();requestAnimationFrame(fit);}
 if(screen==='end')$('#end-reason').textContent=state.ending==='dreams'?'معاينة اكتمال أهداف الأحلام.':`معاينة نهاية ${endingText()} بعد استكمال الجولة الأخيرة؛ النتيجة أدناه توضيحية.`;
 const heading=target.querySelector('h1');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}else if(screen==='play')$('#roll-demo').focus({preventScroll:true});
}
function openDialog(id,trigger=document.activeElement){const d=document.getElementById(id);d.returnFocus=trigger;d.showModal();(d.id==='decision-dialog'?$('#decision-title'):d.querySelector('button,input'))?.focus({preventScroll:true});}
function info(title,body,trigger=document.activeElement){$('#info-title').textContent=title;$('#info-body').innerHTML=body;openDialog('info-dialog',trigger);}
$$('dialog').forEach(d=>{
 d.addEventListener('close',()=>{if(!$('dialog[open]'))d.returnFocus?.focus({preventScroll:true});});
 d.addEventListener('keydown',e=>{
  if(e.key!=='Tab')return;
  const nodes=[...d.querySelectorAll('button:not(:disabled),input,select,summary,a[href],[tabindex="0"]')].filter(el=>el.getClientRects().length);
  if(!nodes.length){e.preventDefault();return;}
  const first=nodes[0],last=nodes.at(-1),active=document.activeElement;
  if(e.shiftKey&&(active===first||!nodes.includes(active))){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&(active===last||!nodes.includes(active))){e.preventDefault();first.focus();}
 });
});
function playerInfo(i,trigger){const p=people[i];info(`${p.name} · ${p.job}`,`<div class="player-row"><span class="portrait ${p.art}" aria-hidden="true"></span><p>اللاعب ${ar(i+1)} • خارج السجن</p></div><dl><div><dt>النقد (عينة)</dt><dd>${ar(i===0&&state.chosen===true?3000:p.cash)}</dd></div><div><dt>الدخل التلقائي (عينة)</dt><dd>${ar(i===0&&state.chosen===true?450:0)}</dd></div><div><dt>الحالة</dt><dd>على خانة مقهى الحي</dd></div></dl><p class="helper">للاطّلاع فقط. الاسم والصورة والرقم ترافق اللون دائماً.</p>`,trigger);}
function tileInfo(){info('مقهى الحي',`<div class="decision-art" aria-hidden="true"><i class="landmark cafe"></i></div><p>الزائر +٤ سعادة. بيانات نموذجية للمعلم من تعريفه الحالي.</p><dl><div><dt>السعر / الدفعة</dt><dd>٤٠٬٠٠٠ / ١٢٬٠٠٠</dd></div><div><dt>الدخل الأساسي / الحالي</dt><dd>٤٥٠ / ٤٥٠</dd></div><div><dt>إيجار الزائر</dt><dd>٩٠٠</dd></div><div><dt>المستوى</dt><dd>٠</dd></div><div><dt>تكلفة التطوير التالي</dt><dd>٦٬٠٠٠</dd></div><div><dt>المالك في هذه العينة</dt><dd>${state.chosen===true?'محسن':'متاح للشراء'}</dd></div></dl><p class="helper">هذه نافذة معلومات. الشراء لا يحدث من الاستعراض.</p>`);}
function phase(n,text){state.phase=n;$$('.turn-steps li').forEach((e,i)=>e.classList.toggle('active',i===n));$('#phase-label').textContent=text;}
function outcome(accepted){
 state.chosen=accepted;$('#decision-dialog').close();phase(4,'شاهد أثر قرارك');$('#gap-value').innerHTML=accepted?'١٬١٨٠ <span>شهرياً</span>':'١٬٦٣٠ <span>شهرياً</span>';$('#goal-progress').style.width=accepted?'28%':'0';
 $('#turn-message').textContent=accepted?'نتيجة العينة: −١٢٬٠٠٠ نقد • +٤٥٠ دخل شهري.':'احتفظت بالنقد. لا يتغير دخلك في هذه العينة.';
 info(accepted?'خطوة نحو دخل مستمر':'مساحة للفرصة التالية',`<div class="outcome-card"><h3>قبل ← بعد</h3><div class="result-pair"><span>النقد</span><b>١٥٬٠٠٠ ← ${accepted?'٣٬٠٠٠':'١٥٬٠٠٠'}</b></div><div class="result-pair"><span>الدخل التلقائي</span><b>٠ ← ${accepted?'٤٥٠':'٠'}</b></div><div class="result-pair"><span>فجوة الهدف</span><b>١٬٦٣٠ ← ${accepted?'١٬١٨٠':'١٬٦٣٠'}</b></div></div><p class="helper">مقارنة لسيناريو عرض، وليست نتيجة مباراة فعلية.</p><button class="quiet full" id="outcome-end">معاينة نهاية الجلسة ←</button>`,$('#roll-demo'));
 $('#roll-demo').disabled=false;$('#roll-demo').innerHTML='تابع الدور <span aria-hidden="true">←</span>';
}
function resetDemo(){state.chosen=null;phase(0,'استعد لخطوتك التالية');state.zoom=1;state.x=state.y=0;$('#gap-value').innerHTML='١٬٦٣٠ <span>شهرياً</span>';$('#goal-progress').style.width='0';$('#turn-message').textContent='الهدف: ابنِ دخلاً تلقائياً يغطي مصاريفك.';$('#roll-demo').disabled=false;$('#roll-demo').innerHTML='ارمِ النرد <span class="roll-dice" aria-hidden="true"></span>';}
const tileKinds=['pay','opportunity','plain','family','plain','opportunity'];
function buildBoard(){
 let html='<div class="map-center"><img src="'+asset('marks/'+state.logo+'-mark.svg')+'" alt=""><b>فرصة تجمعنا</b><span>كل خطوة تقرّبك</span><div class="dice-pair"><i>⚂</i><i>⚁</i></div></div>';
 const cells=[];for(let c=1;c<=13;c++)cells.push([1,c]);for(let r=2;r<=13;r++)cells.push([r,13]);for(let c=12;c>=1;c--)cells.push([13,c]);for(let r=12;r>=2;r--)cells.push([r,1]);
 const buildings={4:'cafe',10:'mall',16:'uni',22:'hospital',28:'hotel',34:'bank',40:'tower',46:'airport'};
 cells.forEach(([r,c],i)=>{let kind=tileKinds[i%6];html+=`<div class="map-tile ${kind}" style="grid-area:${r}/${c}">${buildings[i]?`<span class="map-building"><i class="landmark ${buildings[i]}"></i></span>`:kind==='pay'?'✦':kind==='opportunity'?'↗':'<i class="tile-dot"></i>'}</div>`});
 html+=`<div class="map-cluster">${ar(state.count)}</div>`;$('#board-map').innerHTML=html;
}
function drawCamera(){state.x=Math.max(-160,Math.min(160,state.x));state.y=Math.max(-140,Math.min(140,state.y));$('#board-world').style.transform=`translate(${state.x}px,${state.y}px) scale(${state.zoom})`;$('#scene-tag').textContent=`سباق الفئران · ${state.zoom===1&&state.x===0&&state.y===0?'نظرة عامة':'تحريك يدوي'}`;}
function fit(){const s=$('#board-stage');if(!s.clientHeight)return;$('#board-map').style.setProperty('--fit',Math.min((s.clientWidth-22)/590,(s.clientHeight-36)/495));drawCamera();}
function zoom(delta){state.zoom=Math.max(.75,Math.min(3.2,state.zoom+delta));drawCamera();}
const stage=$('#board-stage');let drag=null;
stage.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;drag={x:e.clientX,y:e.clientY,sx:state.x,sy:state.y};stage.setPointerCapture(e.pointerId);});
stage.addEventListener('pointermove',e=>{if(!drag)return;state.x=drag.sx+e.clientX-drag.x;state.y=drag.sy+e.clientY-drag.y;drawCamera();});
['pointerup','pointercancel'].forEach(type=>stage.addEventListener(type,()=>drag=null));
stage.addEventListener('keydown',e=>{if(e.target.closest('button'))return;const moves={ArrowLeft:[20,0],ArrowRight:[-20,0],ArrowUp:[0,20],ArrowDown:[0,-20]};if(moves[e.key]){e.preventDefault();state.x+=moves[e.key][0];state.y+=moves[e.key][1];drawCamera();}else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(.25)}else if(e.key==='-'){e.preventDefault();zoom(-.25)}else if(e.key==='0'){state.x=state.y=0;state.zoom=1;drawCamera();}});
new ResizeObserver(fit).observe(stage);
$('#zoom-in').onclick=()=>zoom(.25);$('#zoom-out').onclick=()=>zoom(-.25);$('#fit-board').onclick=()=>{state.zoom=1;state.x=state.y=0;drawCamera();};
$('#player-count').onchange=e=>{state.count=Number(e.target.value);renderPlayers()};
$('#player-editor').addEventListener('input',e=>{if(e.target.matches('[data-player-name]'))people[Number(e.target.dataset.playerName)].name=e.target.value.trim()||'لاعب';});
$$('input[name=ending]').forEach(e=>e.onchange=updateEnding);
$('#review-settings').onclick=()=>{renderSettings();show('summary')};
$('#start-demo').onclick=()=>{resetDemo();show('play')};
$('#replay').onclick=()=>{resetDemo();show('play')};
$('#current-tile').onclick=tileInfo;
$('#crowd-button').onclick=()=>openDialog('crowd-dialog');
$('#decision-dialog').addEventListener('cancel',e=>{e.preventDefault();$('#turn-message').textContent='أكمل القرار باختيار صريح؛ لن يُقطع الدور.';});
$('#accept-demo').onclick=()=>outcome(true);$('#decline-demo').onclick=()=>outcome(false);
$('#roll-demo').onclick=()=>{if(state.phase===4){resetDemo();return}if(state.phase!==0)return;phase(1,'رمية نموذجية: ٣ + ٢');$('#roll-demo').disabled=true;$('#turn-message').textContent='التحرك إلى فرصة المقهى في سيناريو العرض.';const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;setTimeout(()=>{phase(2,'وصلت إلى فرصة جديدة');setTimeout(()=>{phase(3,'اختر بعد قراءة الأثر');openDialog('decision-dialog',$('#roll-demo'));},reduced?0:350);},reduced?0:350);};
$('#goal-details').onclick=()=>info('هدفك التالي',`<p>لخروج محسن من سباق الفئران يجب أن يغطي دخله التلقائي مصاريفه.</p><dl><div><dt>مصاريف العينة</dt><dd>١٬٦٣٠ شهرياً</dd></div><div><dt>الدخل التلقائي</dt><dd>${state.chosen===true?'٤٥٠':'٠'}</dd></div><div><dt>الفجوة المتبقية</dt><dd>${state.chosen===true?'١٬١٨٠':'١٬٦٣٠'}</dd></div></dl><p>اشترِ دخلاً، واحتفظ بسيولة لقراراتك القادمة.</p>`);
$('#finance-button').onclick=()=>playerInfo(0,document.activeElement);
$('#end-scenario').onclick=()=>show('end');
$('#more-button').onclick=()=>info('خيارات الجلسة',`<div class="system-chips"><span>التجارة</span><span>المزادات</span><span>الشراكات</span><span>الجمعية</span><span>التأمين</span><span>الدورات</span></div><p class="helper">كلها متاحة في النمطين عند التطبيق؛ هذه قائمة عرض وليست أنظمة منفذة هنا.</p><button class="quiet full" id="change-count">${state.count===2?'جرّب تزاحم ٨ لاعبين':'ارجع إلى لاعبين'}</button><button class="quiet full" id="show-end">معاينة نهاية الجلسة ←</button>`);
$('#market-button').onclick=()=>info('سوق الحي',`<p>عينة عرض لثلاث بضائع. لا يتم شراء أو بيع في نموذج التصميم.</p><dl><div><dt>التمور</dt><dd>١٢٠</dd></div><div><dt>القهوة</dt><dd>٢٠٠</dd></div><div><dt>العسل</dt><dd>٢٥٠</dd></div></dl>`);
const help=()=>info('خطوتك التالية، واضحة',`<p>استعد ← ارمِ ← تحرك ← قرر ← شاهد النتيجة.</p><p>تفاصيل اللاعبين والخانات متاحة عند الطلب. نافذة المعلومات لا تشتري أو تبيع. القرار المالي يوضح النقد والدخل والمصاريف والسعادة قبل اختيارك.</p><p class="helper">يمكنك استخدام Tab وEnter، وإغلاق المعلومات بـEscape، وتحريك اللوحة بالأسهم والتكبير بـ+ و− وإعادتها بـ0. تقريب بإصبعين وتتبع فعلي واختبارات هاتف حقيقي ضمن المرحلة ج.</p>`);
$('#tour').onclick=help;$('#guide-button').onclick=help;$('#rules-info').onclick=help;
document.addEventListener('click',e=>{
 const go=e.target.closest('[data-go]');if(go){show(go.dataset.go);return}
 const concept=e.target.closest('[data-concept]');if(concept){selectLogo(concept.dataset.concept);$(`[data-concept="${concept.dataset.concept}"]`).focus();return}
 const close=e.target.closest('[data-close]');if(close){document.getElementById(close.dataset.close).close();return}
 const person=e.target.closest('[data-person]');if(person){const crowd=$('#crowd-dialog').open;if(crowd)$('#crowd-dialog').close();playerInfo(Number(person.dataset.person),crowd?$('#crowd-button'):person);return}
 if(e.target.closest('#change-count')){$('#info-dialog').close();state.count=state.count===2?8:2;renderPlayers();return}
 if(e.target.closest('#show-end,#outcome-end')){$('#info-dialog').close();show('end');return}
});
buildBoard();renderPlayers();renderSettings();updateEnding();selectLogo(state.logo);show(params.get('screen')||'home');
// Read-only hook for repeatable review checks; never exposes or imports game state.
Object.defineProperty(window,'prototypeSnapshot',{value:()=>Object.freeze({count:state.count,logo:state.logo,ending:state.ending,limit:state.limit,chosen:state.chosen,phase:state.phase}),writable:false});
})();
