import http.server, json, sys, time
OUT=sys.argv[2]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        body=json.dumps({"object":"list","data":[{"id":"qwen3.8-t02:latest","object":"model"}]}).encode()
        self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); raw=self.rfile.read(n)
        with open(OUT,"a") as f: f.write(json.dumps({"path":self.path,"len":n,"body":json.loads(raw)})+"\n")
        req=json.loads(raw)
        if req.get("stream"):
            self.send_response(200); self.send_header("Content-Type","text/event-stream"); self.end_headers()
            for ch in [{"role":"assistant","content":"ok"},{}]:
                d={"id":"x","object":"chat.completion.chunk","created":int(time.time()),"model":req.get("model"),"choices":[{"index":0,"delta":ch,"finish_reason":None if ch else "stop"}]}
                self.wfile.write(b"data: "+json.dumps(d).encode()+b"\n\n")
            self.wfile.write(b'data: {"id":"x","object":"chat.completion.chunk","choices":[],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}\n\n')
            self.wfile.write(b"data: [DONE]\n\n")
        else:
            body=json.dumps({"id":"x","object":"chat.completion","created":0,"model":req.get("model"),"choices":[{"index":0,"message":{"role":"assistant","content":"ok"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
http.server.ThreadingHTTPServer(("127.0.0.1",int(sys.argv[1])),H).serve_forever()
