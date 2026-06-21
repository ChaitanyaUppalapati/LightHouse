"""Local web chat UI for Lighthouse — a browser front-end over the same pipeline.

A self-contained FastAPI app: open the page, paste a suspicious email, and chat with
Lighthouse in the browser. It runs the exact pipeline the ASI:One agent uses
(classify -> propose -> gate -> execute) and handles the human-gate approval inline
(Approve / Deny buttons). Handy as a DEMO_MODE backup and to demo before the agent is
connected to ASI:One (which is the *native* UI).

    AGENT_MAILBOX=0 DEMO_MODE=1 python -m uvicorn pipeline.chat_web:app --port 8200
    # then open http://localhost:8200
"""

import os
import sys

os.environ.setdefault("AGENT_MAILBOX", "0")  # we don't run the uAgent here

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import pipeline.asi_agent as agent  # noqa: E402  (reuse _run_pipeline / _resolve_pending)

app = FastAPI(title="Lighthouse chat")


class ChatIn(BaseModel):
    text: str
    session: str = "web"


@app.post("/chat")
def chat(body: ChatIn) -> dict:
    """Run one chat turn. Returns the reply and whether a decision is pending."""
    resolved = agent._resolve_pending(body.text, body.session)
    reply = resolved if resolved is not None else agent._run_pipeline(body.text, body.session)
    return {"reply": reply, "pending": body.session in agent._pending}


_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lighthouse</title>
<style>
  :root{--bg:#0f1b24;--card:#16252f;--me:#235E6F;--lh:#1d2f3a;--accent:#E7A33E;--text:#eaf1f4;--mut:#9fb1bd}
  *{box-sizing:border-box} body{margin:0;font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;background:var(--bg);color:var(--text)}
  header{display:flex;align-items:center;gap:10px;padding:16px 20px;border-bottom:1px solid #263a47}
  header .dot{width:12px;height:12px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px 2px rgba(231,163,62,.6)}
  header b{font-size:18px} header span{color:var(--mut);font-size:13px}
  #log{max-width:760px;margin:0 auto;padding:22px 16px 140px}
  .row{display:flex;margin:10px 0} .row.me{justify-content:flex-end}
  .bub{max-width:80%;padding:12px 16px;border-radius:16px;line-height:1.5;font-size:15.5px;white-space:pre-wrap}
  .me .bub{background:var(--me);border-bottom-right-radius:4px}
  .lh .bub{background:var(--lh);border:1px solid #2b4150;border-bottom-left-radius:4px}
  .bub strong{color:#fff}
  .gate{display:flex;gap:10px;margin:6px 0 4px}
  .gate button{flex:1;border:none;border-radius:12px;padding:12px;font-size:15px;font-weight:700;cursor:pointer;color:#fff}
  .approve{background:#2e7d51} .deny{background:#b3402c}
  footer{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(transparent,var(--bg) 30%);padding:14px}
  .composer{max-width:760px;margin:0 auto;display:flex;gap:10px}
  textarea{flex:1;resize:none;height:48px;max-height:140px;padding:12px 14px;border-radius:14px;border:1px solid #2b4150;background:var(--card);color:var(--text);font-family:inherit;font-size:15px}
  .send{border:none;border-radius:14px;padding:0 20px;background:var(--accent);color:#1b2a41;font-weight:800;cursor:pointer}
  .hint{max-width:760px;margin:6px auto 0;color:var(--mut);font-size:12px;text-align:center}
</style></head><body>
<header><span class="dot"></span><div><b>Lighthouse</b> &nbsp;<span>watching out for Margaret</span></div></header>
<div id="log"></div>
<footer><div class="composer">
  <textarea id="t" placeholder="Paste a suspicious email, or type a question…"></textarea>
  <button class="send" onclick="send()">Send</button>
</div><div class="hint">Enter to send · Shift+Enter for a new line</div></footer>
<script>
const log=document.getElementById('log'), t=document.getElementById('t');
const session='web-'+Math.random().toString(36).slice(2,9);
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function fmt(s){return esc(s).replace(/\\*\\*(.+?)\\*\\*/g,'<strong>$1</strong>')}
function add(who,text){const r=document.createElement('div');r.className='row '+who;
  r.innerHTML='<div class="bub">'+fmt(text)+'</div>';log.appendChild(r);window.scrollTo(0,1e9);return r}
function gate(){const r=document.createElement('div');r.className='row lh';
  r.innerHTML='<div style="max-width:80%"><div class="gate"><button class="approve" onclick="decide(\\'approve\\')">Approve</button><button class="deny" onclick="decide(\\'deny\\')">Deny</button></div></div>';
  log.appendChild(r);window.scrollTo(0,1e9);return r}
let gateEl=null;
async function turn(text){add('me',text);const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({text,session})});const d=await r.json();add('lh',d.reply);
  if(gateEl){gateEl.remove();gateEl=null} if(d.pending){gateEl=gate()}}
function send(){const v=t.value.trim();if(!v)return;t.value='';turn(v)}
function decide(w){if(gateEl){gateEl.remove();gateEl=null}turn(w)}
t.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
add('lh',"Hi — I'm Lighthouse. Paste a suspicious email and I'll check it, decide what to do, and either handle it safely or ask you before anything risky.");
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _PAGE
