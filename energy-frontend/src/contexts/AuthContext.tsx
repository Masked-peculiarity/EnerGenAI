import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "@/services/api";
import { clearSession, readSession, Session } from "@/services/session";

const AuthContext = createContext<{ session: Session | null; profileError: string; logout: () => void }>({
  session: null, profileError: "", logout: clearSession
});
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState(readSession);
  const [profileError, setProfileError] = useState("");
  useEffect(() => {
    const update = () => setSession(readSession());
    window.addEventListener("energy-auth-change", update);
    window.addEventListener("storage", update);
    return () => {
      window.removeEventListener("energy-auth-change", update);
      window.removeEventListener("storage", update);
    };
  }, []);
  useEffect(() => {
    if (!session) return;
    const controller = new AbortController();
    setProfileError("");
    api<{ email: string }>("/api/auth/me", { signal: controller.signal })
      .catch(error => { if (!controller.signal.aborted) setProfileError(error.message); });
    const timeout = window.setTimeout(clearSession, Math.min(session.expiresAt - Date.now(), 2147483647));
    return () => { controller.abort(); window.clearTimeout(timeout); };
  }, [session]);
  return <AuthContext.Provider value={{ session, profileError, logout: clearSession }}>{children}</AuthContext.Provider>;
}
// Context hook intentionally shares this module with its provider.
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
