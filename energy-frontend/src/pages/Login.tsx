import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Zap } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL;

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (res.ok) {
      localStorage.setItem("token", data.token);
       setTimeout(() => {
      navigate("/index", { replace: true });
    }, 0);
    } else {
      alert(data.error || "Login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="glass p-8 rounded-2xl w-full max-w-md shadow-card">
        <div className="text-center mb-6">
          <Zap className="mx-auto mb-2 text-primary" />
          <h2 className="text-2xl font-bold">Login</h2>
          <p className="text-muted-foreground">
            Access Website
          </p>
        </div>

        <div className="space-y-4">
          <Input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <Button className="w-full" onClick={handleLogin}>
            Login
          </Button>

          <p className="text-sm text-center text-muted-foreground">
            No account?{" "}
            <Link to="/signup" className="text-primary">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
