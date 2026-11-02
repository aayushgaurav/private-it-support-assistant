import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import { FileText, FileUp, RefreshCw, Trash2, UploadCloud } from "lucide-react";
import { api, getApiError } from "../lib/api";
import { normalizeDocuments } from "../lib/normalizers";
import type { DocumentItem } from "../types";
import { Alert, EmptyState, Loader } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function Documents() {
  const {user}=useAuth(); const isAdmin=user?.role?.toLowerCase()==="admin";
  const [docs,setDocs]=useState<DocumentItem[]>([]); const [loading,setLoading]=useState(true);
  const [file,setFile]=useState<File|null>(null); const [access,setAccess]=useState("ALL_EMPLOYEES");
  const [busy,setBusy]=useState(false); const [error,setError]=useState(""); const [notice,setNotice]=useState("");
  async function load(){setLoading(true);setError("");try{const r=await api.get("/documents");setDocs(normalizeDocuments(r.data));}catch(e){setError(getApiError(e));}finally{setLoading(false);}}
  useEffect(()=>{load();},[]);
  async function upload(e:ChangeEvent<HTMLFormElement>){e.preventDefault();if(!file)return;setError("");setNotice("");setBusy(true);try{const body=new FormData();body.append("file",file);body.append("access_level",access);await api.post("/upload",body);setNotice("Document uploaded successfully.");setFile(null);const input=document.getElementById("document-file") as HTMLInputElement|null;if(input)input.value="";await load();}catch(e){setError(getApiError(e));}finally{setBusy(false);}}
  async function remove(id:string){if(!window.confirm("Delete this document? This action cannot be undone."))return;setError("");try{await api.delete(`/documents/${encodeURIComponent(id)}`);setNotice("Document deleted.");await load();}catch(e){setError(getApiError(e));}}
  return <div><div className="page-heading"><div><span className="eyebrow">KNOWLEDGE BASE</span><h1>Documents</h1><p>Manage the knowledge available to your AI assistant.</p></div><button className="secondary-btn" onClick={load}><RefreshCw size={15}/> Refresh</button></div>
    {error&&<Alert onClose={()=>setError("")}>{error}</Alert>}{notice&&<Alert type="success" onClose={()=>setNotice("")}>{notice}</Alert>}
    {isAdmin&&<section className="panel upload-panel"><div className="section-title"><div className="section-icon"><UploadCloud size={18}/></div><div><h2>Add to your knowledge base</h2><p>Upload a PDF, DOCX or TXT document.</p></div></div><form onSubmit={upload} className="upload-form"><label className="dropzone" htmlFor="document-file"><FileUp size={23}/><b>{file?file.name:"Choose a document to upload"}</b><span>{file?`${(file.size/1024/1024).toFixed(2)} MB`:"PDF, DOCX or TXT · Maximum 10 MB (backend enforced)"}</span><input id="document-file" type="file" accept=".pdf,.docx,.txt" onChange={e=>setFile(e.target.files?.[0]??null)}/></label><div className="upload-controls"><label className="field-label compact-label">Access level<select value={access} onChange={e=>setAccess(e.target.value)}><option value="ALL_EMPLOYEES">All employees</option><option value="ADMIN_ONLY">Administrators only</option></select></label><button className="primary-btn" disabled={!file||busy}>{busy?"Uploading…":<><UploadCloud size={16}/> Upload document</>}</button></div></form></section>}
    <section className="panel documents-panel"><div className="section-title"><div className="section-icon"><FileText size={18}/></div><div><h2>Available documents</h2><p>{docs.length} document{docs.length===1?"":"s"} returned by the API</p></div></div>
      {loading?<Loader label="Loading documents…"/>:docs.length===0?<EmptyState title="No documents found" description="Documents returned by your backend will appear here."/>:<div className="table-wrap"><table><thead><tr><th>DOCUMENT</th><th>ACCESS</th><th>DEPARTMENT</th><th>UPLOADED</th>{isAdmin&&<th/>}</tr></thead><tbody>{docs.map(d=><tr key={d.id}><td><div className="file-cell"><div className="file-icon"><FileText size={17}/></div><b>{d.name}</b></div></td><td><span className={`access-badge ${d.accessLevel==="ADMIN_ONLY"?"restricted":""}`}>{d.accessLevel.replace(/_/g," ")}</span></td><td>{d.department||"—"}</td><td>{d.uploadedAt?new Date(d.uploadedAt).toLocaleDateString():"—"}</td>{isAdmin&&<td><button className="icon-btn danger-hover" title="Delete document" onClick={()=>remove(d.id)}><Trash2 size={16}/></button></td>}</tr>)}</tbody></table></div>}
    </section>
  </div>;
}
