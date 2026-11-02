import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Activity, Bot, ChevronDown, FileText, LayoutDashboard, LogOut, Menu, ShieldCheck, Sparkles, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useState } from "react";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isAdmin = user?.role?.toLowerCase() === "admin";

  const signOut = () => {
    logout();
    navigate("/login");
  };

  const nav = (
    <>
      <div className="nav-section-label">WORKSPACE</div>
      <NavLink to="/chat" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}><Bot size={18}/> AI assistant</NavLink>
      <NavLink to="/documents" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}><FileText size={18}/> Documents</NavLink>
      {isAdmin && <>
        <div className="nav-section-label nav-gap">ADMINISTRATION</div>
        <NavLink to="/admin" end onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}><LayoutDashboard size={18}/> Overview</NavLink>
        <NavLink to="/admin/audit" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}><Activity size={18}/> Audit activity</NavLink>
      </>}
    </>
  );

  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
      <div className="brand"><div className="brand-icon"><Sparkles size={19}/></div><div><strong>AskIT</strong><span>PRIVATE AI SUPPORT</span></div><button className="mobile-close icon-btn" onClick={() => setMobileOpen(false)}><X size={18}/></button></div>
      <nav className="side-nav">{nav}</nav>
      <div className="sidebar-bottom"><div className="privacy-note"><ShieldCheck size={16}/><div><b>Private by design</b><span>Local AI · Protected data</span></div></div><button className="profile-row" onClick={signOut}><div className="avatar">{user?.username?.slice(0,1).toUpperCase() || "U"}</div><div className="profile-copy"><b>{user?.username || "Account"}</b><span>{user?.role || "User"}</span></div><LogOut size={16}/></button></div>
    </aside>
    {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <main className="main-area"><header className="topbar"><button className="mobile-menu icon-btn" onClick={() => setMobileOpen(true)}><Menu size={20}/></button><div className="breadcrumb">Workspace <span>/</span> <b>IT Support</b></div><div className="topbar-right"><span className="status-dot"/> Local assistant online <div className="top-avatar">{user?.username?.slice(0,1).toUpperCase()}</div></div></header><div className="page-content"><Outlet/></div></main>
  </div>;
}
