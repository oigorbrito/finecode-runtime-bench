import {pathToFileURL} from "node:url";
import path from "node:path";
const [tool, root, target, arg, extra] = process.argv.slice(2);
if(!tool||!root||!target)throw Error("usage: pi_cold_tool.mjs tool root path argument [extra]");
const folder=path.resolve("vendor/pi_ts/packages/coding-agent/dist/core/tools");
const names={read:"read",grep:"grep",find:"find"};
if(!names[tool])throw Error("unsupported tool");
const mod=await import(pathToFileURL(path.join(folder,names[tool]+".js")).href);
const factory={read:mod.createReadToolDefinition,grep:mod.createGrepToolDefinition,find:mod.createFindToolDefinition}[tool];
const pi=factory(root);
const input={path:target};
if(tool==="grep"){input.pattern=arg;input.literal=true;}
if(tool==="find"){input.pattern=arg;}
if(tool==="read"){input.offset=Number(arg);input.limit=Number(extra);}
const result=await pi.execute("runtime-bench",input);
const output=result.structuredContent??result.content.find(item=>item.type==="text")?.text;
if(typeof output!=="string")throw Error("unexpected Pi tool envelope");
process.stdout.write(output);
