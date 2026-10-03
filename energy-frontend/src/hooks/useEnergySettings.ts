import { useCallback, useMemo, useSyncExternalStore } from "react";
type EnergySettings = { tariff: string; factor: string };
function subscribe(callback: () => void) {
  window.addEventListener("energy-settings-change", callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener("energy-settings-change", callback);
    window.removeEventListener("storage", callback);
  };
}
export function useEnergySettings() {
  const raw = useSyncExternalStore(subscribe, () => localStorage.getItem("energy-settings") || "{}");
  const settings = useMemo<EnergySettings>(() => {
    try { const saved = JSON.parse(raw); return { tariff: String(saved.tariff ?? ""), factor: String(saved.factor ?? "") }; }
    catch { return { tariff: "", factor: "" }; }
  }, [raw]);
  const setSettings = useCallback((next: EnergySettings) => {
    localStorage.setItem("energy-settings", JSON.stringify(next));
    window.dispatchEvent(new Event("energy-settings-change"));
  }, []);
  return { settings, setSettings };
}
