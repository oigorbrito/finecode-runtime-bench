// Replay deterministic model decisions through the ORIGINAL pinned Go Agent loop.
// Test-only adapter copied into CI checkout; no upstream source modifications.
package main
import (
 "bufio"
 "context"
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 "strings"
 "time"
 "github.com/sky-valley/pi/agent"
 "github.com/sky-valley/pi/ai"
 "github.com/sky-valley/pi/coding"
)
type Req struct{Filename string `json:"filename"`}
type Result struct{OK bool `json:"ok"`; Elapsed float64 `json:"elapsed_ms"`;Turns int `json:"turns"`;ToolResults int `json:"tool_results"`;Messages int `json:"messages"`;FinalText string `json:"final_text"`;PromptSeen bool `json:"model_system_prompt_seen"`;Events []string `json:"events"`;Error string `json:"error,omitempty"`}
func main(){
 root,err:=filepath.Abs(os.Args[1]);if err!=nil{panic(err)}
 var tools []agent.AgentTool
 for _,name:=range []string{"write","edit","read","grep"}{
  tool,e:=coding.CreateTool(name,root);if e!=nil{panic(e)};tools=append(tools,tool)
 }
 scan:=bufio.NewScanner(os.Stdin);out:=bufio.NewWriter(os.Stdout);defer out.Flush()
 for scan.Scan(){
  var q Req
  var reply Result
  if e:=json.Unmarshal(scan.Bytes(),&q);e!=nil{reply.Error=e.Error()}else{
   filename:=filepath.Join(root,q.Filename)
   calls:=[]ai.ToolCall{
    {ID:"c1",Name:"write",Arguments:map[string]any{"path":filename,"content":"def calculate(n):\n    return n + 1\n"}},
    {ID:"c2",Name:"edit",Arguments:map[string]any{"path":filename,"edits":[]any{map[string]any{"oldText":"return n + 1","newText":"return n * 2"}}}},
    {ID:"c3",Name:"read",Arguments:map[string]any{"path":filename,"offset":float64(1),"limit":float64(2)}},
    {ID:"c4",Name:"grep",Arguments:map[string]any{"path":filename,"pattern":"return n * 2","literal":true}},
   }
   idx:=0
   stream:=func(ctx context.Context,model *ai.Model,req ai.Context,opts *ai.SimpleStreamOptions)*ai.AssistantMessageEventStream{
    reply.PromptSeen = reply.PromptSeen || strings.Contains(req.SystemPrompt,"Offline deterministic coding task.")
    var msg *ai.AssistantMessage
    if idx<len(calls){msg=&ai.AssistantMessage{Content:ai.ContentList{calls[idx]},StopReason:ai.StopToolUse,Model:"replay"}}else{
     msg=&ai.AssistantMessage{Content:ai.ContentList{ai.TextContent{Text:"task finished"}},StopReason:ai.StopStop,Model:"replay"}
    }
    idx++
    result:=ai.NewAssistantMessageEventStream()
    go func(){result.Push(ai.AssistantMessageEvent{Type:ai.EventStart,Partial:&ai.AssistantMessage{}})
     result.Push(ai.AssistantMessageEvent{Type:ai.EventDone,Reason:msg.StopReason,Message:msg});result.End()}()
    return result
   }
   a:=agent.NewAgent(agent.AgentOptions{
    InitialState:&agent.AgentState{SystemPrompt:"Offline deterministic coding task.",Model:&ai.Model{ID:"replay",Name:"replay",Api:"replay",Provider:"replay"},Tools:tools},
    StreamFn:stream,
    ToolExecution:agent.ToolSequential,
   })
   reply.Events=[]string{}
   a.Subscribe(func(ctx context.Context,e agent.AgentEvent)error{
    reply.Events=append(reply.Events,string(e.Type))
    if e.Type==agent.EvToolExecutionEnd{reply.ToolResults++}
    return nil
   })
   t:=time.Now()
   e:=a.Prompt(context.Background(),"Repair Python calculate and verify it")
   reply.Elapsed=float64(time.Since(t).Nanoseconds())/1e6
   reply.Turns=idx;reply.Messages=len(a.State().Messages)
   content,readErr:=os.ReadFile(filename)
   reply.FinalText=string(content)
   reply.OK=e==nil&&readErr==nil&&reply.FinalText=="def calculate(n):\n    return n * 2\n"
   if e!=nil{reply.Error=e.Error()}else if readErr!=nil{reply.Error=readErr.Error()}
  }
  data,e:=json.Marshal(reply);if e!=nil{panic(e)}
  fmt.Fprintln(out,string(data));if e:=out.Flush();e!=nil{panic(e)}
 }
 if err:=scan.Err();err!=nil{panic(err)}
}
