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
const report={kind:"real_pinned_pi_tools_bounded_comparison",grep:[],find:[],knownGaps:[]};
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

 // Negative-control case: Pi honors gitignore; the bounded C# find-subset does not.
 // Explicitly preserve this as a KNOWN DIFFERENCE, not a parity pass.
 const ignoredRoot=path.join(dir,"ignored-repo");
 mkdirSync(ignoredRoot);
 const initialized=spawnSync("git",["init","--quiet",ignoredRoot],{timeout:10000});
 if(initialized.status!==0)throw Error("git init fixture failed: "+initialized.stderr.toString());
 writeFileSync(path.join(ignoredRoot,".gitignore"),"*.tmp\n");
 writeFileSync(path.join(ignoredRoot,"ignored.tmp"),"ignored fixture");
 const ignoredPi=await find.execute("id",{path:ignoredRoot,pattern:"*.tmp"});
 const expectedIgnore=ignoredPi.structuredContent??ignoredPi.content.find(x=>x.type==="text")?.text;
 const ignoredCSharp=spawnSync(path.resolve(exe),["find-subset",ignoredRoot,"*.tmp"],{timeout:10000});
 if(ignoredCSharp.error)throw ignoredCSharp.error;
 const observedIgnore=ignoredCSharp.stdout.toString("utf8");
 report.knownGaps.push({name:"gitignore-exclusion-not-implemented",
  pinnedPiOutput:expectedIgnore, csharpOutput:observedIgnore,
  expectedDivergence:expectedIgnore==="No files found matching pattern" && observedIgnore==="ignored.tmp" &&
    ignoredCSharp.status===0});
 // Genuine backend reuse: resolve the same fd executable used by Pi.
 // This measures a C# wrapper around fd, NOT an independent pure-C# engine.
 const {ensureTool}=await import(pathToFileURL(path.resolve("vendor/pi_ts/packages/coding-agent/dist/utils/tools-manager.js")).href);
 const fdPath=await ensureTool("fd");
 if(!fdPath)throw Error("Pi fd executable could not be resolved");
 report.fdDelegation=[];
 for(const [name,scenarioRoot,pattern] of [
  ["ignored-at-root",ignoredRoot,"*.tmp"],
  ["regular-repo-file",ignoredRoot,"*.gitignore"],
  ["recursive-basename",root,"*.cs"],
  ["one-file",root,"*.xyz"]
 ]){
   const tool=await find.execute("id",{path:scenarioRoot,pattern});
   const upstream=tool.structuredContent??tool.content.find(x=>x.type==="text")?.text;
   const run=spawnSync(path.resolve(exe),["find-fd-subset",scenarioRoot,pattern,fdPath],{timeout:10000});
   if(run.error)throw run.error;
   const observed=run.stdout.toString("utf8");
   report.fdDelegation.push({name,pass:run.status===0 && upstream===observed,upstream,observed,code:run.status});
 }

}finally{rmSync(dir,{recursive:true,force:true});}
const failures=[...report.grep,...report.find].filter(x=>!x.pass);
report.grepPass=report.grep.filter(x=>x.pass).length;
report.findPass=report.find.filter(x=>x.pass).length;
report.fdDelegationPass=report.fdDelegation.filter(x=>x.pass).length;
report.fail=failures.length+report.knownGaps.filter(x=>!x.expectedDivergence).length+report.fdDelegation.filter(x=>!x.pass).length;
writeFileSync(out,JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify({grepPass:report.grepPass,findPass:report.findPass,fdDelegationPass:report.fdDelegationPass,fdDelegation:report.fdDelegation,knownGaps:report.knownGaps,failures},null,2));
if(report.fail)process.exitCode=1;
