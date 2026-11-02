import type { ReactNode } from "react";
import { LoaderCircle, AlertCircle, CheckCircle2, X } from "lucide-react";

export function Loader({ label = "Loading…" }: { label?: string }) {
  return <div className="loader-wrap"><LoaderCircle className="spin" size={22} /><span>{label}</span></div>;
}

export function Alert({ children, type = "error", onClose }: { children: ReactNode; type?: "error" | "success" | "info"; onClose?: () => void }) {
  const Icon = type === "success" ? CheckCircle2 : AlertCircle;
  return <div className={`alert alert-${type}`}><Icon size={17}/><span>{children}</span>{onClose && <button className="icon-btn" onClick={onClose}><X size={15}/></button>}</div>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty-state"><div className="empty-mark">✳</div><h3>{title}</h3><p>{description}</p></div>;
}

export function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return <div className="stat-card"><span className="stat-label">{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</div>;
}
