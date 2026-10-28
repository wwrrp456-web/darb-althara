/* View-only layout, viewport and accessible dialogs. No engine state or storage. */
(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const wrap = $('.wrap'), modal = $('#modal'), sheet = $('#sheet');
  wrap.append($('#toast'), $('.bar-actions'));
  const header=$('.wrap > header');header.insertBefore($('#turn-readout'),header.querySelector('.sp'));
  $('#board-projects-open').onclick=()=>window.DarbCamera?.inspect('projects');
  const viewport = () => {
    const v = window.visualViewport;
    document.documentElement.style.setProperty('--viewport-height', `${v?.height || innerHeight}px`);
    document.documentElement.style.setProperty('--viewport-top', `${v?.offsetTop || 0}px`);
  };
  window.visualViewport?.addEventListener('resize', viewport);
  window.visualViewport?.addEventListener('scroll', viewport);
  window.addEventListener('resize', viewport); viewport();
  let current = null;
  $('#current-location').onclick = () => {if(current)window.DarbCamera?.inspect(current.position);};
  $('#board-players').onclick = () => window.DarbCamera?.inspect('players');
  $('#camera-help').onclick = () => $('#camera-guide').showModal();
  $('[data-close-guide]').onclick = () => $('#camera-guide').close();
  $('#table-view-select').onchange = e => window.DarbTabletop?.setView(e.target.value);
  window.DarbPlayLayout = {
    update(next) {
      current = next;
      const turn = $('#turn-readout'); turn.replaceChildren();
      const name = document.createElement('b'); name.textContent = `دور ${next.name}`;
      const status = document.createElement('small');
      status.textContent = next.sessionLabel || `الجولة ${next.round} · ${next.busy ? 'قرار جارٍ' : next.phase === 'await_roll' ? 'ارمِ النرد' : 'تابع الدور'}`;
      turn.append(name, status);
      const location = $('#current-location'); location.replaceChildren();
      const text = document.createElement('span'), label = document.createElement('small'), title = document.createElement('b');
      label.textContent = `خانة ${next.viewName}`; title.textContent = next.location;
      text.append(label, title); location.append(text);
      location.setAttribute('aria-label', `معلومات ${next.location}، خانة ${next.viewName}`);
      $('#board-players').textContent = `اللاعبون ${next.players}`;
    }
  };

  const focusables = root => [...root.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),summary,[tabindex="0"]')].filter(e => e.getClientRects().length && !e.inert);
  function trap(event, root) {
    if(event.key !== 'Tab')return;
    const nodes = focusables(root), first = nodes[0], last = nodes.at(-1), active = document.activeElement;
    if(!nodes.length){event.preventDefault();root.focus();return;}
    if(event.shiftKey && (active === first || !nodes.includes(active))){event.preventDefault();last.focus();}
    else if(!event.shiftKey && (active === last || !nodes.includes(active))){event.preventDefault();first.focus();}
  }
  modal.addEventListener('keydown', e => trap(e, sheet));
  let open = false, origin = null, returnQueued = 0;
  const inertBefore = new Map();
  function syncModal() {
    const now = modal.classList.contains('on');
    if(now){
      if(!open){
        origin = document.activeElement;
        document.querySelectorAll('dialog[open]').forEach(d=>d.close());
        for(const el of document.body.children){
          if(el === modal || el.tagName === 'SCRIPT' || el.tagName === 'DIALOG')continue;
          inertBefore.set(el, el.inert); el.inert = true;
        }
      }
      const title = sheet.querySelector('h2');
      if(title){title.id='modal-title';title.tabIndex=-1;}
      if(!open || !sheet.contains(document.activeElement)) (title || sheet).focus({preventScroll:true});
    } else if(open){
      for(const [el, previous] of inertBefore)el.inert=previous;
      inertBefore.clear();
      cancelAnimationFrame(returnQueued);
      returnQueued=requestAnimationFrame(()=>{
        if(modal.classList.contains('on') || $('dialog[open]'))return;
        const target=origin?.isConnected && !origin.disabled && !origin.inert ? origin : $('#roll:not(:disabled)') || $('#menuBtn');
        target?.focus({preventScroll:true});
      });
    }
    open=now;
  }
  new MutationObserver(syncModal).observe(modal,{attributes:true,attributeFilter:['class'],childList:true,subtree:true});
  document.querySelectorAll('dialog').forEach(dialog=>{
    new MutationObserver(()=>{
      if(dialog.open){const heading=dialog.querySelector('h2'); if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}}
    }).observe(dialog,{attributes:true,attributeFilter:['open']});
    dialog.addEventListener('keydown', e=>trap(e,dialog));
    dialog.addEventListener('close',()=>{
      if(modal.classList.contains('on') || $('dialog[open]'))return;
      // Native dialog may restore its own trigger; detached board nodes need a stable fallback.
      const stable=document.activeElement;
      if(!stable?.isConnected || stable === document.body || dialog.contains(stable))$('#current-location')?.focus({preventScroll:true});
    });
  });
})();
