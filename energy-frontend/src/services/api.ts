export const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:5000").replace(/\/$/, "");

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = localStorage.getItem("token");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  let response: Response;
  try { response = await fetch(`${API_BASE}${path}`, { ...options, headers }); }
  catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new Error("Could not reach the API. Start the backend and check VITE_API_URL.");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      clearSession();
      throw new Error("Your login has expired. Log in again to use personal documents.");
    }
    throw new Error(data.error || data.msg || `Request failed (HTTP ${response.status})`);
  }
  return data as T;
}

export const timestampLabel = (value: string) => value.replace("T", " ").slice(0, 16);
export const numberLabel = (value: number | null | undefined, digits = 2) => value == null ? "Not set" : value.toLocaleString(undefined, { maximumFractionDigits: digits });
import { clearSession } from "./session";
