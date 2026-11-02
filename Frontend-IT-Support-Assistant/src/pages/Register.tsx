import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getApiError } from "../lib/api";
import { Alert } from "../components/ui";

export default function Register() {
  const { register } = useAuth(); const navigate = useNavigate();
  const [username,setUsername] = useState(""); const [email,setEmail] = useState(""); const [password,setPassword] = useState("");
  const [error,setError] = useState(""); const [success,setSuccess] = useState(""); const [busy,setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault(); setError(""); setSuccess(""); setBusy(true);
    try { await register(username,email,password); setSuccess("Account created. You can now sign in."); setTimeout(() => navigate("/login"), 900); }
    catch(err) { setError(getApiError(err)); } finally { setBusy(false); }
  }
  return <div className="auth-page register-page"><div className="auth-visual"><div className="auth-orb orb-one"/><div className="auth-orb orb-two"/><div className="auth-visual-content"><div className="brand brand-light"><div className="brand-icon"><Sparkles size={19}/></div><div><strong>northstar</strong><span>PRIVATE AI SUPPORT</span></div></div><div className="visual-copy"><span className="eyebrow light-eyebrow">A MORE INFORMED WORKDAY</span><h1>Knowledge<br/><em>at your side.</em></h1><p>Find trusted answers from the documents your organization already relies on.</p></div><div className="visual-foot">PRIVATE AI IT SUPPORT ASSISTANT <span>•</span> 01 / SECURE WORKSPACE</div></div></div><div className="auth-form-side"><form className="auth-form" onSubmit={submit}><div className="mobile-brand brand"><div className="brand-icon"><Sparkles size={19}/></div><div><strong>northstar</strong><span>PRIVATE AI SUPPORT</span></div></div><div className="form-heading"><div className="form-icon"><Sparkles size={20}/></div><span className="eyebrow">GET STARTED</span><h2>Create your account</h2><p>Your workspace access will follow your assigned role.</p></div>{error && <Alert>{error}</Alert>}{success && <Alert type="success">{success}</Alert>}<label className="field-label">Username<input value={username} onChange={e=>setUsername(e.target.value)} minLength={3} maxLength={50} autoComplete="username" required placeholder="Choose a username"/></label><label className="field-label">Work email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" required placeholder="you@company.com"/></label><label className="field-label">Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={12} maxLength={128} autoComplete="new-password" required placeholder="At least 12 characters"/><small className="field-hint">Use at least 12 characters.</small></label><button className="primary-btn full-btn" disabled={busy}>{busy ? "Creating account…" : <>Create account <ArrowRight size={17}/></>}</button><p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p></form></div></div>;
}
