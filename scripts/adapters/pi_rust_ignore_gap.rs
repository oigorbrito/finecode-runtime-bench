// Temporary test-only adapter injected into pinned Rust port's examples/tools.
// Never committed to or modified in the upstream Rust repository.
use std::sync::Arc;
use rpi_agent::types::TextContentOrImage;
use rpi_tools::{create_find_tool,create_grep_tool,ExecutionToolContext,OsExecutionEnv};
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main(){
 let root=std::env::args().nth(1).expect("root");
 let tool_name=std::env::args().nth(2).expect("tool");
 let pattern=std::env::args().nth(3).expect("pattern");
 let os=Arc::new(OsExecutionEnv::with_cwd(root.clone().into()));
 let env:Arc<dyn rpi_tools::ExecutionEnv>=os;
 let ctx=ExecutionToolContext::new(env,None);
 let tool=match tool_name.as_str(){
  "grep"=>create_grep_tool(&ctx,None),
  "find"=>create_find_tool(&ctx,None),
  _=>panic!("unknown tool")
 };
 let params=if tool_name=="grep"{
  serde_json::json!({"pattern":pattern,"path":root,"literal":true})
 }else{
  serde_json::json!({"pattern":pattern,"path":root})
 };
 let result=tool.execute("bench",params,CancellationToken::new(),Arc::new(|_|{})).await.expect("tool execute");
 for item in result.content{
  if let TextContentOrImage::Text(text)=item{
   print!("{}",text.text);
   break;
  }
 }
}
