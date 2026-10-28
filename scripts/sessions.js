/* Session settings and host-owned active time. No economic formulas. */
(() => {
  'use strict';
  const defaults=()=>({mode:'family',ending:'dreams',limit:null,guidance:'full',effects:'quick'});
  function settings(input={}) {
    const mode=input.mode==='extended'?'extended':'family';
    const ending=['dreams','rounds','time'].includes(input.ending)?input.ending:'dreams';
    const limit=ending==='dreams'?null:Number(input.limit);
    if(ending!=='dreams'&&(!Number.isInteger(limit)||limit<1||limit>(ending==='rounds'?200:240)))throw new Error('حد الجلسة غير صالح');
    return {mode,ending,limit,guidance:mode==='family'?'full':'brief',effects:mode==='family'?'quick':'normal'};
  }
  function clock(){return {elapsedMs:0,paused:false,endingRound:null};}
  function tick(game,delta){
    if(!game?.session||!game.clock||game.clock.paused||game.phase==='over')return;
    if(Number.isFinite(delta)&&delta>0)game.clock.elapsedMs+=delta;
    if(game.session.ending==='time'&&game.clock.elapsedMs>=game.session.limit*60000&&game.clock.endingRound==null)game.clock.endingRound=game.round;
  }
  function reasonAtBoundary(game,completedRound){
    if(!game.session)return null; // Legacy games keep their historical dream ending.
    if(game.session.ending==='rounds'&&completedRound>=game.session.limit)return 'rounds';
    if(game.session.ending==='time'&&game.clock?.endingRound!=null&&completedRound>=game.clock.endingRound)return 'time';
    return null;
  }
  function checkpointClock(game,safeRound){
    const copy={...game.clock};
    // Reload resumes this safe round, not an uncommitted later round/decision.
    if(copy.endingRound!=null)copy.endingRound=Math.min(copy.endingRound,safeRound);
    return copy;
  }
  function description(session){
    if(!session)return 'الأحلام · إعدادات المباراة السابقة';
    return `${session.mode==='family'?'عائلي':'موسع'} · ${session.ending==='rounds'?session.limit+' جولات':session.ending==='time'?session.limit+' دقيقة':'تحقيق الأحلام'}`;
  }
  const settlement='عند نهاية الحد تستكمل الجولة الحالية، ثم ينفذ الشراء الختامي الحالي لأكبر حلم متاح لمن في المسار السريع وسعادته 50 فأكثر. الترتيب: نقاط الأحلام، ثم أسبقية تحقيقها، ثم الفوز السابق، ثم المسار السريع، ثم نسبة الدخل التلقائي إلى المصاريف. التعادل التام يحتفظ بترتيب اللاعبين الحالي.';
  window.DarbSessions={defaults,settings,clock,tick,reasonAtBoundary,checkpointClock,description,settlement};
})();
