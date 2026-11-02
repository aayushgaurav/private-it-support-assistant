import { useEffect, useState } from "react";
import { Activity, FileText, RefreshCw, ShieldCheck, Users } from "lucide-react";
import { api, getApiError } from "../lib/api";
import { extractStats } from "../lib/normalizers";
import { Alert, Loader, StatCard } from "../components/ui";

export default function Admin() {
  const [data,setData]=useState<unknown>(null);const [loading,setLoading]=useState(true);const [error,setError]=useState("");
  async function load(){setLoading(true);setError("");try{const r=await api.get("/admin/dashboard");setData(r.data);}catch(e){setError(getApiError(e));}finally{setLoading(false);}}
  useEffect(()=>{load();},[]);
  const stats=extractStats(data);
  const fallback=[{label:"Dashboard status",value:data?"Connected":"—"},{label:"Available metrics",value:String(stats.length)}];
  return <div><div className="page-heading"><div><span className="eyebrow">CONTROL CENTER</span><h1>Overview</h1><p>Monitor the workspace and its knowledge resources.</p></div><button className="secondary-btn" onClick={load}><RefreshCw size={15}/> Refresh</button></div>{error&&<Alert>{error}</Alert>}{loading?<Loader label="Loading dashboard…"/>:<><div className="stats-grid">{(stats.length?stats:fallback).map((s,i)=><StatCard key={s.label} label={s.label} value={s.value} hint={i===0?"Live response from backend":"Returned dashboard field"}/>)}</div><div className="admin-content-grid"><div className="panel admin-feature"><div className="feature-icon"><Users size={19}/></div><h3>Access management</h3><p>User roles and access permissions are enforced by the backend. This dashboard displays only metrics returned by the existing API.</p><div className="feature-foot"><ShieldCheck size={15}/> Backend-enforced authorization</div></div><div className="panel admin-feature"><div className="feature-icon"><FileText size={19}/></div><h3>Knowledge resources</h3><p>Review the Documents area to upload, inspect and remove indexed knowledge files.</p><div className="feature-foot"><Activity size={15}/> Document activity</div></div></div><section className="panel raw-panel"><div className="section-title"><div className="section-icon"><Activity size={18}/></div><div><h2>Dashboard response</h2><p>Raw API payload, because the OpenAPI specification does not define its response schema.</p></div></div><pre>{JSON.stringify(data,null,2)}</pre></section></>}</div>;
}
