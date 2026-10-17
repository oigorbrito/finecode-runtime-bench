import {mkdtempSync,writeFileSync,rmSync,mkdirSync} from "node:fs";
import {tmpdir} from "node:os";
import path from "node:path";
import {pathToFileURL} from "node:url";
import {spawnSync} from "node:child_process";
const [exe,out]=process.argv.slice(2);
if(!exe||!out)throw Error("missing binary/output");
const basedir=path.resolve("vendor/pi_ts/packages/coding-agent/dist/core/tools");
const {createGrepToolDefinition}=await import(pathToFileURL(path.join(basedir,"grep.js")).href);
const {createFindToolDefinition}=await import(pathToFileURL(path.join(basedir,"find.js")).href);
const dir=mkdtempSync(path.join(tmpdir(),"finecode-direct-tools-"));
const report={kind:"real_pinned_pi_tools_bounded_comparison",grep:[],find:[]};
function check(group,name,expected,argv){
 const run=spawnSync(path.resolve(exe),argv,{timeout:10000});
 if(run.error)throw run.error;
 const observed=run.stdout.toString("utf8");
 report[group].push({name,pass:run.status===0&&expected===observed,expected,observed,code:run.status});
}
try{
 const file=path.join(dir,"single.txt");
 writeFileSync(file,"alpha\nTODO first\nmiddle\nTODO last\n");
 const grep=createGrepToolDefinition(dir);
 for(const [name,pattern,literal,ignoreCase] of [
  ["positive","TODO",true,false],
  ["absent","NOTFOUND",true,false],
  ["case-sensitive","todo",true,false],
  ["single","alpha",true,false],
  ["literal-ignore-case","todo",true,true],
  ["regex-anchored","^TODO",false,false],
  ["regex-class","TODO [a-z]+",false,false],
  ["regex-alternation","TODO (first|last)",false,false]
 ]){
  const pi=await grep.execute("id",{path:file,pattern,literal,ignoreCase});
  const argv=["grep-subset",file,pattern,literal?"literal":"regex"];
  if(ignoreCase)argv.push("ignore-case");
  check("grep",name,pi.structuredContent??pi.content.find(x=>x.type==="text")?.text,argv);
 }
 const root=path.join(dir,"find-root");
 mkdirSync(root);writeFileSync(path.join(root,"unique.xyz"),"data");writeFileSync(path.join(root,"another.txt"),"data");
 const nested=path.join(root,"src");mkdirSync(nested);writeFileSync(path.join(nested,"only.cs"),"namespace Test {}");
 const find=createFindToolDefinition(dir);
 for(const [name,pattern] of [["specific","*.xyz"],["none","*.absent"],["text","*.txt"],["recursive-csharp","*.cs"],["recursive-no-hit","*.go"]]){
  const pi=await find.execute("id",{path:root,pattern});
  check("find",name,pi.structuredContent??pi.content.find(x=>x.type==="text")?.text,["find-subset",root,pattern]);
 }
}finally{rmSync(dir,{recursive:true,force:true});}
const failures=[...report.grep,...report.find].filter(x=>!x.pass);
report.grepPass=report.grep.filter(x=>x.pass).length;
report.findPass=report.find.filter(x=>x.pass).length;
report.fail=failures.length;
writeFileSync(out,JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify({grepPass:report.grepPass,findPass:report.findPass,failures},null,2));
if(failures.length)process.exitCode=1;
