import { useState } from "react";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { UserPlus } from "lucide-react";

import { API_BASE } from "@/services/api";
import { saveSession } from "@/services/session";
import { useAuth } from "@/contexts/AuthContext";

const Signup = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { session } = useAuth();

  const handleSignup = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.msg || data.error || "Signup failed");
        return;
      }
      const login = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const auth = await login.json();
      if (!login.ok) {
        setError("Your account was created. Please log in using the link below.");
        return;
      }
      saveSession(auth.token);
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
          <UserPlus className="mx-auto mb-2 text-primary" />
          <h2 className="text-2xl font-bold">Create Account</h2>
        </div>

        <form className="space-y-4" onSubmit={handleSignup}>
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
            minLength={8}
            autoComplete="new-password"
            placeholder="Password"
            aria-label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <p className="text-sm text-muted-foreground">Use at least 8 characters.</p>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

          <Button className="w-full" type="submit" disabled={submitting}>
            {submitting ? "Creating account..." : "Sign Up"}
          </Button>

          <p className="text-sm text-center text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-primary">
              Log in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Signup;
