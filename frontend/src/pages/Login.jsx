import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("manager@fieldops.local");
  const [password, setPassword] = useState("manager12345");
  const [error, setError] = useState("");

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("Could not sign in. Check email and password.");
    }
  }

  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <div className="hidden bg-[#10231f] p-12 text-[#f4efe6] md:flex md:flex-col md:justify-between">
        <div className="font-mono tracking-[0.4em]">FIELDOPS</div>
        <div>
          <h1 className="max-w-md text-4xl font-semibold leading-tight">Jobs in the field, visible from the office.</h1>
          <p className="mt-4 max-w-md text-[#c9d7d2]">
            Assign technicians, enforce a real job workflow, track expenses, and close work with an audit trail.
          </p>
        </div>
      </div>
      <form onSubmit={onSubmit} className="flex flex-col justify-center bg-[#fbf8f2] px-8 py-16 md:px-16">
        <h2 className="text-2xl font-semibold text-[#10231f]">Sign in</h2>
        <label className="mt-8 text-sm">Email</label>
        <input
          className="mt-1 rounded border border-[#d8ccb4] bg-white px-3 py-2"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <label className="mt-4 text-sm">Password</label>
        <input
          type="password"
          className="mt-1 rounded border border-[#d8ccb4] bg-white px-3 py-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="mt-3 text-sm text-[#9b1c1c]">{error}</p>}
        <button className="mt-6 rounded bg-[#1b4d43] px-4 py-2.5 font-medium text-white">Continue</button>
      </form>
    </div>
  );
}
