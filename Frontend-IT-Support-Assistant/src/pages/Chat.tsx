import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ArrowUp, Bot, Copy, FileText, Plus, Sparkles, UserRound } from "lucide-react";
import { api, getApiError } from "../lib/api";
import { normalizeChat } from "../lib/normalizers";
import type { ChatResult } from "../types";
import { Alert } from "../components/ui";

export default function Chat() {
  const [question,setQuestion] = useState(""); const [messages,setMessages] = useState<ChatResult[]>([]);
  const [busy,setBusy] = useState(false); const [error,setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(()=>{ endRef.current?.scrollIntoView({behavior:"smooth"}); },[messages,busy]);

  async function send(e?: FormEvent, preset?: string) {
    e?.preventDefault(); const q = (preset ?? question).trim(); if (!q || busy) return;
    setQuestion(""); setError(""); setBusy(true);
    try { const response = await api.post("/ask",{question:q}); setMessages(prev=>[...prev,normalizeChat(response.data,q)]); }
    catch(err) { setError(getApiError(err)); }
    finally { setBusy(false); }
  }
  const copy = async (text:string) => { try { await navigator.clipboard.writeText(text); } catch { setError("Clipboard access is unavailable in this browser."); } };

  return <div className="chat-page"><div className="page-heading chat-heading"><div><span className="eyebrow">YOUR KNOWLEDGE WORKSPACE</span><h1>AI assistant</h1><p>Ask questions. Get answers grounded in your internal documentation.</p></div><div className="model-pill"><span className="status-dot"/> Local model connected</div></div>
    {error && <Alert onClose={()=>setError("")}>{error}</Alert>}
    <div className={`conversation ${messages.length===0?"conversation-empty":""}`}>
      {messages.length===0 ? <div className="welcome-panel"><div className="welcome-icon"><Sparkles size={25}/></div><span className="eyebrow">AskIT AI</span><h2>What can I help you<br/>figure out today?</h2><p>Ask about your IT policies, processes, security guidance or internal documentation.</p><div className="suggestion-grid">{["What should I do if I forget my password?","What are the password requirements?","How do I report a security incident?"].map((s,i)=><button className="suggestion" key={s} onClick={()=>send(undefined,s)}><span>{["01","02","03"][i]}</span>{s}<ArrowUp size={15}/></button>)}</div></div> : <div className="message-list">{messages.map((m,i)=><div className="exchange" key={i}><div className="message user-message"><div className="message-avatar user-avatar"><UserRound size={16}/></div><div className="message-body"><div className="message-meta">YOU <span>·</span> QUESTION</div><p>{m.question}</p></div></div><div className="message assistant-message"><div className="message-avatar ai-avatar"><Bot size={17}/></div><div className="message-body"><div className="message-meta">AskIT <span>·</span> ANSWER <button className="copy-btn" onClick={()=>copy(m.answer)}><Copy size={13}/> Copy</button></div><p className="answer-text">{m.answer}</p>{m.sources.length>0 && <div className="sources-block"><div className="sources-title"><FileText size={14}/> SOURCES <span>{m.sources.length}</span></div><div className="source-list">{m.sources.map((s,j)=>{const name=String(s.original_filename??s.filename??s.document_name??s.metadata?.original_filename??`Source ${j+1}`);const page=s.page??s.metadata?.page;const excerpt=s.content??s.text;return <div className="source-item" key={j}><FileText size={15}/><div><b>{name}</b><span>{page!==undefined?`Page ${page}`:"Retrieved document"}{typeof excerpt==="string"&&excerpt?` · ${excerpt.slice(0,170)}${excerpt.length>170?"…":""}`:""}</span></div></div>;})}</div></div>}</div></div></div>)}</div>}
      {busy && <div className="thinking-row"><div className="message-avatar ai-avatar"><Bot size={17}/></div><div><span className="thinking-dots"><i/><i/><i/></span><small>Searching your knowledge base…</small></div></div>}
      <div ref={endRef}/>
    </div>
    <form className="composer" onSubmit={send}><div className="composer-top"><span><span className="composer-dot"/> GROUNDED IN YOUR DOCUMENTS</span><span>SHIFT + ENTER FOR NEW LINE</span></div><textarea value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}}} placeholder="Ask a question about your IT documentation…" maxLength={1000} rows={2}/><div className="composer-bottom"><span>{question.length}/1000 characters</span><button className="send-btn" type="submit" disabled={!question.trim()||busy}><ArrowUp size={17}/></button></div></form>
    <div className="chat-disclaimer"><ShieldCheckIcon/> Answers are generated from accessible documents. Always verify critical security decisions.</div>
  </div>;
}
function ShieldCheckIcon(){return <span className="tiny-shield">◆</span>}
