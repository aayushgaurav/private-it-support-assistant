import { useEffect, useState } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { api, getApiError } from "../lib/api";
import { normalizeAudit } from "../lib/normalizers";
import type { AuditItem } from "../types";
import { Alert, EmptyState, Loader } from "../components/ui";

export default function Audit() {
  const [items,setItems]=useState<AuditItem[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState("");const [action,setAction]=useState("");
  async function load(){setLoading(true);setError("");try{const r=await api.get("/admin/audit-logs",{params:{limit:50,offset:0,...(action?{action}: {})}});setItems(normalizeAudit(r.data));}catch(e){setError(getApiError(e));}finally{setLoading(false);}}
  useEffect(()=>{load();},[action]);
  return <div><div className="page-heading"><div><span className="eyebrow">SECURITY & GOVERNANCE</span><h1>Audit activity</h1><p>Review recorded actions from your workspace.</p></div><button className="secondary-btn" onClick={load}><RefreshCw size={15}/> Refresh</button></div>{error&&<Alert>{error}</Alert>}<section className="panel audit-panel"><div className="section-title"><div className="section-icon"><Activity size={18}/></div><div><h2>Recent activity</h2><p>Latest 50 records from the audit endpoint.</p></div></div><div className="filter-row"><label className="field-label compact-label">Filter by action<input value={action} onChange={e=>setAction(e.target.value)} placeholder="e.g. LOGIN, AI_QUERY"/></label></div>{loading?<Loader label="Loading audit activity…"/>:items.length===0?<EmptyState title="No audit records found" description="No records matched the current filter, or the API returned an unrecognized response format."/>:<div className="table-wrap"><table><thead><tr><th>ACTION</th><th>USER</th><th>DATE</th><th>DETAILS</th></tr></thead><tbody>{items.map(i=><tr key={i.id}><td><span className="action-badge">{i.action}</span></td><td>{i.username}</td><td>{i.createdAt?new Date(i.createdAt).toLocaleString():"—"}</td><td className="details-cell">{i.details||"—"}</td></tr>)}</tbody></table></div>}</section></div>;
}
