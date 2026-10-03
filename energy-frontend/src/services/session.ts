export interface Session { email: string; expiresAt: number }
export function readSession(): Session | null {
  try {
    const token = localStorage.getItem("token");
    if (!token) return null;
    const value = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    if (typeof value.sub !== "string" || typeof value.exp !== "number" || value.exp * 1000 <= Date.now()) return null;
    return { email: value.sub, expiresAt: value.exp * 1000 };
  } catch { return null; }
}
export function saveSession(token: string) {
  localStorage.setItem("token", token);
  window.dispatchEvent(new Event("energy-auth-change"));
}
export function clearSession() {
  localStorage.removeItem("token");
  window.dispatchEvent(new Event("energy-auth-change"));
}
