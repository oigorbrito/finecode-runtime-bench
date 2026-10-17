// Offline benchmark adapter for the pinned Go port.
// Copied into vendor/pi_go/cmd/finecode-bench at CI time, never committed upstream.
package main

import (
 "bufio"
 "context"
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 "github.com/sky-valley/pi/coding"
 "github.com/sky-valley/pi/agent"
 "github.com/sky-valley/pi/ai"
)
type Request struct{ Tool string `json:"tool"`; Path string `json:"path"`; Pattern string `json:"pattern"`; Content string `json:"content"`; Edits []map[string]string `json:"edits"`; Offset int `json:"offset"`; Limit int `json:"limit"` }
type Reply struct{ Text string `json:"text,omitempty"`; Error string `json:"error,omitempty"` }
func main(){
 root,err:=filepath.Abs(os.Args[1]);if err!=nil{panic(err)}
 tools:=map[string]agent.AgentTool{}
 for _,name:=range []string{"read","grep","write","edit"}{t,e:=coding.CreateTool(name,root);if e!=nil{panic(e)};tools[name]=t}
 scanner:=bufio.NewScanner(os.Stdin);scanner.Buffer(make([]byte,4096),1024*1024)
 out:=bufio.NewWriter(os.Stdout);defer out.Flush()
 for scanner.Scan(){
  var req Request
  resp:=Reply{}
  if e:=json.Unmarshal(scanner.Bytes(),&req);e!=nil{resp.Error=e.Error()}else{
   tool,ok:=tools[req.Tool]
   if !ok{resp.Error="unsupported tool"}else{
    args:=map[string]any{"path":req.Path}
    if req.Tool=="read"{args["offset"]=float64(req.Offset);args["limit"]=float64(req.Limit)}
    if req.Tool=="grep"{args["pattern"]=req.Pattern;args["literal"]=true}
    if req.Tool=="write"{args["content"]=req.Content}
    if req.Tool=="edit"{edits:=make([]any,0,len(req.Edits));for _,e:=range req.Edits{edits=append(edits,map[string]any{"oldText":e["oldText"],"newText":e["newText"]})};args["edits"]=edits}
    result,e:=tool.Execute(context.Background(),"bench",args,func(agent.AgentToolResult){})
    if e!=nil{resp.Error=e.Error()}else{
     for _,c:=range result.Content{if txt,ok:=c.(ai.TextContent);ok{resp.Text=txt.Text;break}}
    }
   }
  }
  line,e:=json.Marshal(resp);if e!=nil{panic(e)}
  fmt.Fprintln(out,string(line));if e:=out.Flush();e!=nil{panic(e)}
 }
 if err:=scanner.Err();err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}
}
