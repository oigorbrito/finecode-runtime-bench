// Offline replay of an actual pinned Pi Agent loop; Node and Bun execute the SAME source.
import path from "node:path";
import fs from "node:fs";
import {pathToFileURL} from "node:url";
import {createInterface} from "node:readline";
const root=path.resolve(process.argv[2]);
const dist=path.resolve("vendor/pi_ts/packages");
const agentMod=await import(pathToFileURL(path.join(dist,"agent/dist/agent.js")).href);
const streamMod=await import("@earendil-works/pi-ai/compat").catch(async()=>import(pathToFileURL(path.join(dist,"ai/dist/index.js")).href));
const {Agent}=agentMod;
const {createAssistantMessageEventStream}=streamMod;
const toolsDir=path.join(dist,"coding-agent/dist/core/tools");
const tools=[];
for(const name of ["write","edit","read","grep"]){
 const mod=await import(pathToFileURL(path.join(toolsDir,name+".js")).href);
 tools.push(mod[{"write":"createWriteToolDefinition","edit":"createEditToolDefinition","read":"createReadToolDefinition","grep":"createGrepToolDefinition"}[name]](root));
}
const usage={input:0,output:0,cacheRead:0,cacheWrite:0,totalTokens:0,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}};
for await(const line of createInterface({input:process.stdin,crlfDelay:Infinity})){
 let report={};
 try{
  const q=JSON.parse(line);
  const filepath=path.join(root,q.filename);
  const scripted=[
   ["write",{path:filepath,content:"def calculate(n):\n    return n + 1\n"}],
   ["edit",{path:filepath,edits:[{oldText:"return n + 1",newText:"return n * 2"}]}],
   ["read",{path:filepath,offset:1,limit:2}],
   ["grep",{path:filepath,pattern:"return n * 2",literal:true}]
  ];
  let idx=0,events=[], toolResults=0, promptSeen=false, modelContexts=[];
  const streamFn=(_model,context)=>{
   promptSeen ||= context.messages.some(m=>m.role==="system" && String(m.content).includes("Offline deterministic coding task."));
   modelContexts.push({roles:context.messages.map(m=>m.role),system_prompt:context.messages.find(m=>m.role==="system")?.content??null});
   const stream=createAssistantMessageEventStream();
   queueMicrotask(()=>{
    const next=scripted[idx++];
    const content=next?[{type:"toolCall",id:"c"+idx,name:next[0],arguments:next[1]}]:[{type:"text",text:"task finished"}];
    const msg={role:"assistant",content,api:"openai-responses",provider:"openai",model:"replay",
      usage,stopReason:next?"toolUse":"stop",timestamp:Date.now()};
    stream.push({type:"done",reason:msg.stopReason,message:msg});
   });
   return stream;
  };
  const agent=new Agent({initialState:{tools,systemPrompt:"Offline deterministic coding task."},streamFn});
  agent.subscribe(ev=>{events.push(ev.type);if(ev.type==="tool_execution_end")toolResults++});
  const t=performance.now();
  await agent.prompt("Repair the Python calculate function and verify it.");
  const elapsed=performance.now()-t;
  const final=fs.readFileSync(filepath,"utf8");
  report={ok:final==="def calculate(n):\n    return n * 2\n",elapsed_ms:elapsed,
   turns:idx,tool_results:toolResults,messages:agent.state.messages.length,message_roles:agent.state.messages.map(m=>m.role),
   final_text:final,model_system_prompt_seen:promptSeen,model_contexts:modelContexts,events};
 }catch(e){report={error:String(e?.stack??e)}}
 process.stdout.write(JSON.stringify(report)+"\n");
}
