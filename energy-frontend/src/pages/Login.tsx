import { useState } from "react";
import { useNavigate, Link, Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Zap } from "lucide-react";

import { API_BASE } from "@/services/api";
import { saveSession } from "@/services/session";
import { useAuth } from "@/contexts/AuthContext";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { session } = useAuth();

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.msg || data.error || "Login failed");
        return;
      }
      saveSession(data.token);
      navigate("/dashboard", { replace: true });
    } catch {
      setError("Could not reach the server. Check that the backend is running.");
    } finally {
      setSubmitting(false);
    }
  };

  if (session) return <Navigate to="/dashboard" replace />;
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="glass p-8 rounded-2xl w-full max-w-md shadow-card">
        <div className="text-center mb-6">
          <Zap className="mx-auto mb-2 text-primary" />
          <h1 className="text-2xl font-bold">Log in</h1>
          <p className="text-muted-foreground">
            Welcome back to EnerGenAI
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleLogin}>
          <Input
            type="email"
            required
            autoComplete="email"
            placeholder="Email"
            aria-label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            type="password"
            required
            autoComplete="current-password"
            placeholder="Password"
            aria-label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

          <Button className="w-full" type="submit" disabled={submitting}>
            {submitting ? "Logging in..." : "Log in"}
          </Button>

          <p className="text-sm text-center text-muted-foreground">
            No account?{" "}
            <Link to="/signup" className="text-primary">
              Sign up
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Login;
