const techMeta={
  cognee:{name:'Cognee',role:'Persistent graph memory + agent memory'},
  brightdata:{name:'Bright Data',role:'Live web perception'},
  strands:{name:'AWS Strands',role:'Reasoning orchestration'},
  local_model:{name:'Local Qwen / vLLM',role:'Sovereign inference'},
  docker:{name:'Docker Sandboxes',role:'Safe action execution'},
  inneros_mcp:{name:'InnerOS / Ralphi MCP',role:'Optional system connector'}
};

const connectorMeta=[
  ['cognee_agent_memory','Cognee ↔ Strands','Direct shared memory tools'],
  ['cognee_mcp','Cognee MCP','Shared memory for external agents'],
  ['inneros_mcp','Ralphi MCP','System memory + tools'],
  ['github','GitHub','Projects + code'],
  ['gmail','Gmail','Messages + signals'],
  ['calendar','Calendar','Time + commitments'],
  ['drive','Drive / Notion','Documents + knowledge'],
  ['infra','Infrastructure','Servers + operations']
];

const fabricOrder=['personal_brain','brightdata','strands','cognee_mcp','codex','cursor','antigravity','ralphi','gmail'];

let statuses={};
let seq=0;

function $(id){return document.getElementById(id)}
function now(){return new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}

function techCard(key,state){
  const m=techMeta[key];
  const cls=state==='ready'||state==='connected'||state==='configured'?'ready':'';
  return '<div class="tech-card '+cls+'" data-card="'+key+'"><span class="dot"></span><div><b>'+m.name+'</b><small>'+m.role+'</small></div><em>'+state.replaceAll('_',' ')+'</em></div>';
}

function renderFabric(fabric){
  if(!fabric)return;
  $('fabricDataset').textContent=fabric.dataset||'dataset';
  const surfaces=fabric.surfaces||[];
  const byKey=Object.fromEntries(surfaces.map(x=>[x.key,x]));
  const ordered=fabricOrder.map(k=>byKey[k]).filter(Boolean);
  $('fabricMatrix').innerHTML=ordered.map(surface=>{
    const state=surface.state||'unknown';
    const cls=['ready','configured'].includes(state)?'ready':state==='pending_auth'?'pending':'optional';
    return '<div class="fabric-row '+cls+'"><span>'+escapeHtml(surface.label)+'</span><b>'+escapeHtml(state.replaceAll('_',' '))+'</b><small>'+escapeHtml(surface.transport)+'</small></div>';
  }).join('');
}

function renderStatus(s){
  statuses=s||{};
  const coreKeys=['cognee','brightdata','strands','local_model','docker'];
  $('techStack').innerHTML=coreKeys.map(k=>techCard(k,(s[k]||{}).state||'unknown')).join('');
  const coreReady=coreKeys.every(k=>['ready','configured','connected'].includes((s[k]||{}).state));
  $('coreBadge').textContent=coreReady?'CORE READY':'CHECK SYSTEMS';
  $('coreBadge').classList.toggle('ready',coreReady);
  $('systemSummary').textContent=coreReady?'core brain operational':'partial readiness';

  const mcp=(s.inneros_mcp||{}).state||'bridge_pending';
  const agentMemory=(s.cognee_agent_memory||{}).state||'dependency_pending';
  const cogneeMcp=((s.connectors||{}).cognee_mcp_surface)||'not_reported';
  $('connectors').innerHTML=connectorMeta.map(([key,name,role])=>{
    let live=false;
    let state='optional';
    if(key==='cognee_agent_memory'){
      live=agentMemory==='ready';
      state=live?'DIRECT':'pending';
    }else if(key==='cognee_mcp'){
      live=cogneeMcp==='registered_platform_capability';
      state=live?'REGISTERED':'optional';
    }else if(key==='inneros_mcp'){
      live=mcp==='connected';
      state=live?'available':'optional';
    }else{
      live=mcp==='connected';
      state=live?'via MCP':'optional';
    }
    return '<div class="connector '+(live?'connected':'degraded')+'"><b>'+name+'</b><span>'+role+' · '+state+'</span></div>';
  }).join('');

  Object.entries(s).forEach(([key,val])=>{
    const reg=$('region-'+key); if(!reg) return;
    reg.classList.toggle('complete',['ready','configured','connected'].includes(val.state));
  });
  renderFabric(s.memory_fabric);
}

async function loadStatus(){
  try{const r=await fetch('/api/status',{cache:'no-store'});renderStatus(await r.json())}
  catch(e){$('systemSummary').textContent='status endpoint unavailable'}
}

function setStage(stage,tech,state,msg){
  seq++;
  document.querySelectorAll('.region').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.flow-bar>div').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.neural-map path').forEach(x=>x.classList.remove('flowing'));

  const reg=$('region-'+tech);
  if(reg){reg.classList.remove('complete','error');reg.classList.add(state==='error'?'error':state==='complete'?'complete':'active')}
  const step=document.querySelector('[data-step="'+stage+'"]'); if(step)step.classList.add('active');
  const pathMap={observe:'path-observe',remember:'path-memory',reason:'path-reason',act:'path-action',learn:'path-learn'};
  const path=$(pathMap[stage]); if(path)path.classList.add('flowing');

  $('cognitiveState').textContent='COGNITIVE STATE · '+stage.toUpperCase();
  $('modePill').textContent=(state==='active'?'PROCESSING':'STAGE COMPLETE');
  $('brainMain').textContent=stage.toUpperCase();
  addEvent(tech,state,msg);
}

function addEvent(tech,state,msg){
  const m=techMeta[tech]||{name:tech};
  const a=document.createElement('article');
  a.className='event '+state;
  a.innerHTML='<span>'+String(seq).padStart(2,'0')+'</span><div><b>'+m.name+'</b><small>'+escapeHtml(msg)+'</small></div>';
  $('eventStream').prepend(a);
  while($('eventStream').children.length>14)$('eventStream').lastElementChild.remove();
}

function escapeHtml(v){const d=document.createElement('div');d.textContent=v??'';return d.innerHTML}

function resetBrain(){
  document.querySelectorAll('.region').forEach(x=>x.classList.remove('active','error'));
  document.querySelectorAll('.flow-bar>div').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.neural-map path').forEach(x=>x.classList.remove('flowing'));
  $('cognitiveState').textContent='COGNITIVE STATE · IDLE';
  $('modePill').textContent='WAITING FOR INPUT';
  $('brainMain').textContent='READY';
}

async function runBrain(act){
  const prompt=$('prompt').value.trim();if(!prompt)return;
  $('thinkBtn').disabled=true;$('actBtn').disabled=true;
  $('answer').textContent='Live cognitive trace running…';
  $('eventStream').innerHTML='';
  $('metrics').innerHTML='<span>MEM …</span><span>WEB …</span><span>ACTIONS …</span>';
  seq=0;

  const es=new EventSource('/api/brain/stream?prompt='+encodeURIComponent(prompt)+'&act='+(act?'true':'false'));
  es.onmessage=(evt)=>{
    const data=JSON.parse(evt.data);
    if(data.type==='stage'){
      setStage(data.stage,data.technology,data.state,data.message);
    }else if(data.type==='result'){
      const replay=(data.web_hits||[]).some(x=>x.metadata&&x.metadata.verified_replay);
      $('answer').textContent=data.answer;
      $('metrics').innerHTML='<span>MEM '+(data.memory_hits||[]).length+'</span><span>WEB '+(data.web_hits||[]).length+(replay?' REPLAY':' LIVE')+'</span><span>ACTIONS '+(data.actions||[]).length+'</span>';
      $('evidenceSummary').textContent=replay?'Live provider timed out; showing clearly labeled verified replay.':'Memory, web and execution evidence verified from backend.';
      $('brainMain').textContent='LEARNED';
    }else if(data.type==='error'){
      addEvent('inneros_mcp','error',data.message);
      $('answer').textContent='ERROR: '+data.message;
    }else if(data.type==='done'){
      es.close();$('thinkBtn').disabled=false;$('actBtn').disabled=false;
      setTimeout(resetBrain,1800);loadStatus();
    }
  };
  es.onerror=()=>{es.close();$('thinkBtn').disabled=false;$('actBtn').disabled=false;$('answer').textContent='Stream interrupted. Core brain may still be running; retry once.'};
}

$('thinkBtn').addEventListener('click',()=>runBrain(false));
$('actBtn').addEventListener('click',()=>runBrain(true));
document.querySelectorAll('[data-prompt]').forEach(b=>b.addEventListener('click',()=>{$('prompt').value=b.dataset.prompt}));
loadStatus();
setInterval(loadStatus,15000);
