/* Illustrated presentation only. Never modifies game data, answer indices or save values. */
(() => {
  'use strict';
  const icons = ['dice','person','people','shop','ledger','globe','arrow','coin','case','leaf','receipt','heart','star','home','shield','book','gift','chart','bank','package','bulb','bell','coffee','building','plane','health','scale','smile','flag','download','menu','robot','family','graduate','calendar','gavel'];
  const newIcons=['investor','audit','jail','upgrade','bankrupt','jail-exit','rat-race','fast-track','mood-great','mood-good','mood-neutral','mood-worried','mood-exhausted','two-dice','more'];
  icons.push(...newIcons); // Existing 6x6 positions stay unchanged.
  const semanticIcons={'💹':'investor','🕵':'audit','🚔':'jail','🏗':'upgrade','🐀':'rat-race','🚀':'fast-track','😄':'mood-great','🙂':'mood-good','😐':'mood-neutral','😟':'mood-worried','😵':'mood-exhausted','☰':'more'};
  const groups = {
    dice:'🎲⚀⚁⚂⚃⚄⚅',person:'👤🧑👩🧔👧👦👴👵👨👰🧕',people:'👥🤝',shop:'🏪🏬🛒🛍',ledger:'📋🧮📐',globe:'🌍🌐',arrow:'🔁🔄🔺🔻👉⬆⬇↔⏭➕',coin:'💰💵💸🪙💳',case:'💼🧳',leaf:'🌱🌳🌴🌸',receipt:'🧾',heart:'❤❤️🤲',star:'★⭐🏅🏆🥇🥈🥉👑✨🎯',home:'🏠🏡🛖🏘',shield:'🛡🔒',book:'📚',gift:'🎁🎉🎊🎂🎈🧧',chart:'📈📉📊',bank:'🏦',package:'📦🧱',bulb:'💡🧠❓',bell:'🔔🔊🔇',coffee:'☕🍽🍳🍯🧁',building:'🏢🏨🏙🏫🕌',plane:'✈🚗🚚🚌🏖🏝🏞',health:'🏥⚕🩺💊🆘',scale:'⚖',smile:'😀😄😊🙂😐😟😵😂😮😭👏💪🔥🐣🐈🐯🐸🐼🦁🦄🦊',flag:'🏁',download:'📤📥📲📱💻📸🔌',menu:'☰',robot:'🤖🎮',family:'👶💍',graduate:'🎓🎒',calendar:'📅🌙',gavel:'🔨🛠',
  };
  const emoji = /(?:\p{Extended_Pictographic}|[☰★⚀-⚅])(?:\uFE0F|\p{Emoji_Modifier})?(?:\u200D\p{Extended_Pictographic}(?:\uFE0F|\p{Emoji_Modifier})?)*/gu;
  const iconFor = value => {
    if(value.includes('\u200D'))return value.includes('👩')&&value.includes('👨')?'family':'person';
    for(const [key, values] of Object.entries(groups))if(values.includes(value.replace(/\uFE0F/g,'')))return key;
    return /[✅❌⚠🚫🔴🟠🟡🟢]/u.test(value)?'status':'star';
  };
  const extraGroups=['😀😄😊🙂','😐','😟','😵','😂','😮','😭','👏','🔥','💪','🔊','🔇','🧴','🧵👗','🍯','🌸'];
  const status = {'✅':'✓','❌':'×','⚠':'!','🚫':'×','🔴':'●','🟠':'●','🟡':'●','🟢':'●'};
  const avatarValues=['🧑','👩','🧔','👧','👦','👴','👵','🦁','🐯','🦊','🐼','🦄','🐸','🚀','👑','🎩'];
  const avatarNames=['شخصية مرحة','شخصية مبدعة','شخصية طموحة','شخصية فضولية','شخصية متفائلة','شخصية خبيرة','شخصية حكيمة','شخصية اجتماعية','شخصية مبادرة','شخصية ذكية','شخصية هادئة','شخصية حالمة','شخصية نشيطة','المستكشف','القائد','صاحب القبعة'];
  function illustration(value,asAvatar=false) {
    const el=document.createElement('span'), name=iconFor(value);
    el.className='illustrated-icon';el.setAttribute('role','img');el.setAttribute('aria-label',value);
    if(['🥇','🥈','🥉'].includes(value))el.dataset.rank=String(['🥇','🥈','🥉'].indexOf(value)+1);
    const direction={'⬆':'↑','🔺':'↑','⬇':'↓','🔻':'↓','↔':'↔','▪':'—'}[value.replace(/\uFE0F/g,'')];
    if(direction){el.classList.add('identity-status','identity-direction');el.textContent=direction;el.dataset.direction=direction;return el;}
    const av=avatarValues.indexOf(value);
    if(asAvatar&&av>=0){el.classList.add('identity-avatar');el.style.setProperty('--ix',av%4*100/3+'%');el.style.setProperty('--iy',Math.floor(av/4)*100/3+'%');return el;}
    const semantic=semanticIcons[value.replace(/\uFE0F/g,'')];
    if(semantic){const i=newIcons.indexOf(semantic);el.classList.add('identity-additional');el.dataset.icon=semantic;el.style.setProperty('--ix',i%5*25+'%');el.style.setProperty('--iy',Math.floor(i/5)*50+'%');return el;}
    const extra=extraGroups.findIndex(group=>group.includes(value.replace(/\uFE0F/g,'')));
    if(extra>=0){el.classList.add('identity-extra');el.style.setProperty('--ix',extra%4*100/3+'%');el.style.setProperty('--iy',Math.floor(extra/4)*100/3+'%');return el;}
    const index=icons.indexOf(name);
    if(av>=0){el.classList.add('identity-avatar');el.style.setProperty('--ix',av%4*100/3+'%');el.style.setProperty('--iy',Math.floor(av/4)*100/3+'%');return el;}
    if(index<0){el.classList.add('identity-status');el.textContent=status[value.replace(/\uFE0F/g,'')]||'!';el.dataset.status=value;}
    else {el.dataset.icon=name;el.style.setProperty('--ix',(index%6)*20+'%');el.style.setProperty('--iy',Math.floor(index/6)*20+'%');}
    return el;
  }
  function hydrate(root) {
    if(!root || (root.nodeType!==1 && root.nodeType!==3))return;
    if(root.nodeType===1){const options=root.matches('option')?[root]:root.querySelectorAll('option');for(const option of options){emoji.lastIndex=0;if(emoji.test(option.textContent)){const original=option.value;emoji.lastIndex=0;const label=option.textContent.replace(emoji,'').trim();option.value=original;option.textContent=label||'شخصية';}}}
    if(root.nodeType===1 && root.matches('svg,script,style,textarea,option,input,.illustrated-icon,.identity-avatar,[contenteditable]'))return;
    const nodes=[];
    if(root.nodeType===3)nodes.push(root);
    else {const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);while(walker.nextNode())nodes.push(walker.currentNode);}
    for(const node of nodes){
      if(node.parentElement?.closest('svg,script,style,textarea,option,input,.illustrated-icon,.identity-avatar,[contenteditable]'))continue;
      const text=node.nodeValue;emoji.lastIndex=0;
      if(!emoji.test(text))continue;
      emoji.lastIndex=0;const frag=document.createDocumentFragment();let end=0;
      for(const match of text.matchAll(emoji)){
        frag.append(text.slice(end,match.index));frag.append(illustration(match[0],!!node.parentElement.closest('.av,.identity-avatar-value,.pwho')||node.parentElement.matches('.mini>span:first-child')));end=match.index+match[0].length;
      }
      frag.append(text.slice(end));node.replaceWith(frag);
    }
  }
  // Different emotional states retain a readable label instead of relying on an OS emoji.
  const families={
    offer:[0,'فرصة استثمارية','راجع الدفعة والدخل، ثم اختر ما يناسب خطتك.'],dealsize:[0,'الفرص','ابدأ بخيار يناسب ميزانيتك.'],market:[0,'عرض مستثمر','وازن بين ربح اليوم والدخل المستقبلي.'],
    family:[1,'بطاقات العائلة','قرارات صغيرة تصنع فرقاً في حياتك.'],life:[1,'قرارات الحياة','وازن بين المال والوقت والسعادة.'],yleisure:[1,'وقت لنفسك','اختر ما يلائم ميزانيتك وراحتك.'],fun:[1,'ترفيه وراحة','كل خيار يوضّح تكلفته وأثره على سعادتك.'],
    quiz:[2,'تحدّي المعرفة','اقرأ السؤال واختر إجابة واحدة.'],
    souk:[3,'سوق الحي','راجع الأسعار والمخزون قبل تنفيذ الصفقة.'],order:[3,'طلبات السوق','راجع الشروط والمكافأة قبل قبول الطلب.'],auction:[3,'المزاد','حدّد عرضك بما يناسب النقد المتاح.'],goodspick:[3,'شراء بضاعة','اختر السلعة التي تريد تداولها.'],qty:[3,'كمية البضاعة','حدّد الكمية المناسبة لميزانيتك.'],sellpick:[3,'بيع البضاعة','اختر من مخزونك ما تريد بيعه.'],tradeoffer:[3,'عرض تبادل','راجع البضاعة والثمن قبل الموافقة.'],tradebuyer:[3,'اختيار المشتري','اختر اللاعب الذي تريد عرض الصفقة عليه.'],tradeprice:[3,'تسعير الصفقة','حدّد السعر الذي تريد عرضه.'],
    dream:[4,'طموحك القادم','قارن التكلفة والنقاط ومتطلبات الشراء.'],
    loan:[5,'التمويل','راجع المبلغ والقسط قبل الالتزام.'],funloan:[5,'تمويل الترفيه','راجع تكلفة الاقتراض وأثرها على ميزانيتك.'],audit:[5,'مراجعة مالية','راجع التفاصيل قبل متابعة دورك.'],jail:[5,'إجراء مالي','اختر الطريقة الأنسب لمتابعة رحلتك.'],jamstart:[5,'الجمعية','التزام دوري يحتاج إلى تخطيط مسبق.'],jampick:[5,'الجمعية','اختر موعداً يناسب خطتك المالية.'],
    insure:[6,'حماية للمستقبل','راجع المدة والتغطية وتكلفة الاشتراك.'],charity:[6,'أثر طيّب','اختر المساهمة التي تناسب إمكاناتك.'],
    partner:[7,'شراكة وفرص','راجع حصتك والتزاماتك قبل الاتفاق.'],partnerpick:[7,'بناء شراكة','اختر شريكاً لفرصتك القادمة.'],duelpick:[7,'تحدٍّ بين اللاعبين','اختر اللاعب الذي تريد تحدّيه.'],
    learn:[8,'طوّر مهارتك','وازن بين تكلفة التعلّم وزيادة دخلك.']
  };
  function decorateCard(sheet,pr){
    let spec=families[pr.category||pr.kind];
    if(!spec){const t=pr.title||'';spec=/حلم|مبروك|فوز/.test(t)?[4,'خطوة في رحلتك','تابع ما تغيّر قبل إكمال دورك.']:/عائل|مولود/.test(t)?[1,'من الحياة','تفاصيل جديدة تؤثر على خطتك.']:/إجاب|سؤال/.test(t)?[2,'نتيجة التحدّي','تعلّم اليوم يفيدك في القرار القادم.']:[5,'ملخص القرار','راجع النتيجة ثم تابع رحلتك.'];}
    sheet.classList.add('decision-card');sheet.dataset.cardKind=pr.kind;
    const [art,label,caption]=spec,heading=sheet.querySelector('h2'),actions=sheet.querySelector(':scope > .row');
    const header=document.createElement('header');header.className='decision-heading';
    const image=document.createElement('span');image.className='card-illustration';image.setAttribute('aria-hidden','true');image.style.setProperty('--cx',(art%3)*50+'%');image.style.setProperty('--cy',Math.floor(art/3)*50+'%');
    const titles=document.createElement('div'),kicker=document.createElement('span');kicker.className='card-kicker';kicker.textContent=label;
    titles.append(kicker,heading);header.append(image,titles);
    const content=document.createElement('div');content.className='decision-content';
    for(const node of [...sheet.childNodes])if(node!==actions)content.append(node);
    const hint=document.createElement('p');hint.className='card-guidance';hint.textContent=caption;
    sheet.replaceChildren(header,hint,content,actions);
    actions.classList.add('decision-actions');actions.setAttribute('aria-label','خيارات القرار');
    [...actions.children].forEach((button,i)=>{
      button.dataset.choice=i;
      const label=button.textContent, split=label.indexOf(' — ');
      if(split>=0){const title=document.createElement('span'),effect=document.createElement('span');title.className='choice-title';effect.className='choice-effect';title.textContent=label.slice(0,split);effect.textContent=label.slice(split+3);button.replaceChildren(title,effect);}
    });
    hydrate(sheet);
  }
  window.DarbIdentity={decorateCard,hydrate,avatarNames};
  const observer=new MutationObserver(records=>{
    // Disconnect while replacing nodes so decorative nodes never trigger another pass.
    observer.disconnect();
    for(const record of records){if(record.type==='characterData')hydrate(record.target);else for(const node of record.addedNodes)hydrate(node);}
    observe();
  });
  function observe(){observer.observe(document.body,{childList:true,subtree:true,characterData:true});}
  hydrate(document.body);observe();
})();
