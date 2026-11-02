import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import Admin from "./pages/Admin";
import Audit from "./pages/Audit";

export default function App() {
  return <Routes>
    <Route path="/login" element={<Login/>}/>
    <Route path="/register" element={<Register/>}/>
    <Route element={<ProtectedRoute/>}>
      <Route element={<AppLayout/>}>
        <Route path="/chat" element={<Chat/>}/>
        <Route path="/documents" element={<Documents/>}/>
        <Route element={<ProtectedRoute adminOnly/>}>
          <Route path="/admin" element={<Admin/>}/>
          <Route path="/admin/audit" element={<Audit/>}/>
        </Route>
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/chat" replace/>}/>
  </Routes>;
}
