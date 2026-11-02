import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ArrowRight, LockKeyhole, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getApiError } from "../lib/api";
import { Alert } from "../components/ui";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault(); setError(""); setBusy(true);
    try {
      await login(username, password);
      const from = (location.state as any)?.from?.pathname || "/chat";
      navigate(from, { replace: true });
    } catch (err) { setError(getApiError(err)); }
    finally { setBusy(false); }
  }

  return <div className="auth-page"><div className="auth-visual"><div className="auth-orb orb-one"/><div className="auth-orb orb-two"/><div className="auth-visual-content"><div className="brand brand-light"><div className="brand-icon"><Sparkles size={19}/></div><div><strong>AskIT</strong><span>PRIVATE AI SUPPORT</span></div></div><div className="visual-copy"><span className="eyebrow light-eyebrow">YOUR KNOWLEDGE. YOUR CONTROL.</span><h1>IT support,<br/><em>with context.</em></h1><p>A private AI assistant that understands your internal documentation and helps your team move forward.</p><div className="visual-points"><span><i/> Local-first intelligence</span><span><i/> Answers grounded in your docs</span><span><i/> Access built around your role</span></div></div><div className="visual-foot">PRIVATE AI IT SUPPORT ASSISTANT <span>•</span> 01 / SECURE WORKSPACE</div></div></div><div className="auth-form-side"><form className="auth-form" onSubmit={submit}><div className="mobile-brand brand"><div className="brand-icon"><Sparkles size={19}/></div><div><strong>AskIT</strong><span>PRIVATE AI SUPPORT</span></div></div><div className="form-heading"><div className="form-icon"><LockKeyhole size={20}/></div><span className="eyebrow">WELCOME BACK</span><h2>Sign in to your workspace</h2><p>Enter your account details to continue.</p></div>{error && <Alert>{error}</Alert>}<label className="field-label">Username<input value={username} onChange={e => setUsername(e.target.value)} placeholder="Your username" autoComplete="username" required minLength={3}/></label><label className="field-label">Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password" required/></label><button className="primary-btn full-btn" disabled={busy}>{busy ? "Signing in…" : <>Sign in <ArrowRight size={17}/></>}</button><p className="auth-switch">New to the workspace? <Link to="/register">Create an account</Link></p><div className="form-security"><LockKeyhole size={14}/> Your session is protected with bearer-token authentication.</div></form></div></div>;
}
