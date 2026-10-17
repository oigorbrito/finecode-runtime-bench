// Persistent in-process pinned original Pi tool execution protocol.
import { createInterface } from "node:readline";
import path from "node:path";
import { pathToFileURL } from "node:url";
const root=path.resolve(process.argv[2]);
const folder=path.resolve("vendor/pi_ts/packages/coding-agent/dist/core/tools");
const [{createReadToolDefinition},{createGrepToolDefinition}]=await Promise.all([
 import(pathToFileURL(path.join(folder,"read.js")).href),
 import(pathToFileURL(path.join(folder,"grep.js")).href)
]);
const tools={read:createReadToolDefinition(root),grep:createGrepToolDefinition(root)};
for await (const line of createInterface({input:process.stdin,crlfDelay:Infinity})){
 let reply={};
 try{
  const q=JSON.parse(line);const tool=tools[q.tool];if(!tool)throw Error("unsupported tool");
  const input={path:q.path};
  if(q.tool==="read"){input.offset=q.offset;input.limit=q.limit}
  if(q.tool==="grep"){input.pattern=q.pattern;input.literal=true}
  const result=await tool.execute("bench",input);
  reply.text=result.structuredContent??result.content.find(c=>c.type==="text")?.text;
 }catch(e){reply.error=String(e?.message??e)}
 process.stdout.write(JSON.stringify(reply)+"\n");
}
