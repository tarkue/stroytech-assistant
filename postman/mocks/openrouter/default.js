// Local subset of the published Chat Completions contract; never calls upstream.
const http = require('http');
let scenario = 'success';
const text = 'При работе на скале требуется гидромолот.';
const rule = {id:'r1',title:'Скала',conditions:[{field:'soil',op:'eq',value:'rock'}],
  effects:[{kind:'require',value:'Гидромолот'}],source:'input',
  entities:[{text:'скале',type:'soil'}],intent:'requirement',evidence:text,status:'pending'};
http.createServer(async (req,res) => {
  const send = (code,value) => {res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
  if (req.url.startsWith('/__control/')) {
    scenario = req.url.split('/').pop(); return send(200,{scenario});
  }
  if (req.method !== 'POST' || req.url !== '/api/v1/chat/completions') return send(501,{error:{message:'Not modeled'}});
  const body = req.body;
  if (req.headers.authorization !== 'Bearer synthetic-local-only' ||
      !req.headers['content-type']?.startsWith('application/json') ||
      !body || typeof body.model !== 'string' || body.stream !== false ||
      !Array.isArray(body.messages) || body.messages[0]?.role !== 'user' ||
      typeof body.messages[0]?.content !== 'string') return send(400,{error:{message:'Contract violation'}});
  if (/^http(401|402|429|500)$/.test(scenario)) {
    const code = Number(scenario.slice(4)); return send(code,{error:{code,message:'Synthetic provider failure'}});
  }
  if (scenario === 'timeout') await new Promise(resolve => setTimeout(resolve,1500));
  if (scenario === 'bad-envelope') return send(200,{choices:[]});
  let content = body.messages[0].content.startsWith('FILTER:') ? JSON.stringify({text}) : JSON.stringify({rules:[rule]});
  if (scenario === 'bad-content') content = 'not JSON';
  if (scenario === 'empty-content') content = '';
  return send(200,{id:'gen-local',object:'chat.completion',created:0,model:body.model,
    choices:[{index:0,message:{role:'assistant',content},finish_reason:'stop'}]});
}).listen(process.env.PORT);
