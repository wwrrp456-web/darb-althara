const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const context={window:{}};vm.createContext(context);vm.runInContext(fs.readFileSync('scripts/sessions.js','utf8'),context);
const S=context.window.DarbSessions;
assert.equal(S.settings().ending,'dreams');
for(const ending of ['rounds','time'])for(const limit of [0,-1,1.5,Infinity,NaN,'bad',1000])assert.throws(()=>S.settings({ending,limit}));
for(const mode of ['family','extended'])for(const ending of ['dreams','rounds','time']){
 const session=S.settings({mode,ending,limit:2});const g={session,clock:S.clock(),round:1,phase:'await_roll'};
 S.tick(g,60000);assert.equal(g.clock.elapsedMs,60000);assert.equal(S.reasonAtBoundary(g,1),null);
 g.clock.paused=true;S.tick(g,90000);assert.equal(g.clock.elapsedMs,60000);
 g.clock.paused=false;S.tick(g,60000);
 if(ending==='time'){assert.equal(g.clock.endingRound,1);assert.equal(S.reasonAtBoundary(g,1),'time');}
 if(ending==='rounds')assert.equal(S.reasonAtBoundary(g,2),'rounds');
 if(ending==='dreams')assert.equal(S.reasonAtBoundary(g,100),null);
 g.phase='over';S.tick(g,1000);assert.equal(g.clock.elapsedMs,120000);
}
assert.equal(S.reasonAtBoundary({session:null},999),null);
const later={clock:{elapsedMs:60001,paused:false,endingRound:2}};
assert.equal(S.checkpointClock(later,1).endingRound,1);assert.equal(later.clock.endingRound,2);
console.log(JSON.stringify({settings_bounds:'passed',both_modes_three_endings:'passed',pause_and_finished_clock:'passed',legacy_dreams:'passed',safe_round_clock_checkpoint:'passed'}));
