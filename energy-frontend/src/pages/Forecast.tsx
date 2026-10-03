import { useEffect, useState } from "react";
import PageLayout from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DemoNotice, EnergyChart, ErrorState, MetricCard, panelClass } from "@/components/energy/Shared";
import { api, numberLabel, timestampLabel } from "@/services/api";
import { ForecastResult, ModelReport } from "@/types/energy";

interface Evaluation { rows: { timestamp: string; actual_wh: number; predicted_wh: number }[]; metrics: ModelReport; evaluation: string }
export default function Forecast() {
  const [horizon, setHorizon] = useState(6);
  const [origin, setOrigin] = useState("");
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError("");
    Promise.all([api<ForecastResult>("/api/forecast", { method: "POST", body: JSON.stringify({ horizon_steps: horizon, ...(origin ? { origin } : {}) }), signal: controller.signal }), api<Evaluation>("/api/forecast/evaluation", { signal: controller.signal })])
      .then(([future, historical]) => { setForecast(future); setEvaluation(historical); })
      .catch(err => { if (err.name !== "AbortError") setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [horizon, origin, refresh]);
  const report = evaluation?.metrics;
  const score = report?.comparison[report.selected_model].test;
  const recursive = report?.recursive_test[String(horizon)];
  return <PageLayout><h1 className="mb-2 text-3xl font-semibold">Appliance-energy forecast</h1><p className="mb-5 text-muted-foreground">Forecast from recorded history at ten-minute resolution.</p><DemoNotice />
    <div className={panelClass + " mb-6 flex flex-wrap items-end gap-4"}>
      <div><p className="text-sm font-medium">Horizon</p><div className="mt-2 flex gap-2"><Button id="horizon" variant={horizon === 6 ? "default" : "outline"} onClick={() => setHorizon(6)}>Next hour</Button><Button variant={horizon === 144 ? "default" : "outline"} onClick={() => setHorizon(144)}>Next 24 hours</Button></div></div>
      <div><Label htmlFor="origin">Historical origin (optional)</Label><Input id="origin" type="datetime-local" step="600" value={origin} onChange={e => setOrigin(e.target.value)} /></div>
      <Button variant="outline" onClick={() => { setOrigin(""); setRefresh(refresh + 1); }}>Use latest reading</Button>
      <p className="w-full text-xs text-muted-foreground">Leave origin blank for the final dataset reading. Future sensor and lighting values are held at their last observed values; predicted energy feeds subsequent lag features.</p>
    </div>
    {error && <ErrorState>{error}</ErrorState>}{loading && <p role="status">Computing forecast…</p>}
    {!loading && !error && forecast && evaluation && report && score && <>
      <div className="mb-6 grid gap-4 sm:grid-cols-4"><MetricCard label="Forecast total" value={numberLabel(forecast.total_kwh) + " kWh"} detail={forecast.horizon_minutes + " minutes after " + timestampLabel(forecast.origin)} /><MetricCard label="One-step test MAE" value={numberLabel(score.mae_wh) + " Wh"} /><MetricCard label="One-step test RMSE" value={numberLabel(score.rmse_wh) + " Wh"} /><MetricCard label="One-step test R²" value={numberLabel(score.r2, 3)} detail="Regression score, not percentage accuracy" /></div>
      <EnergyChart rows={forecast.predictions} title={horizon === 6 ? "Next-hour forecast" : "Next-day forecast"} unit="Wh per ten-minute interval" series={[{ key: "appliances_wh", label: "Forecast", color: "#159a82" }, { key: "actual_wh", label: "Observed after historical origin (if available)", color: "#5579b5" }]} />
      {recursive && <p className="my-4 rounded-lg border p-4 text-sm">Recursive {recursive.horizon_minutes / 60}-hour test: MAE {numberLabel(recursive.selected_model.mae_wh)} Wh, RMSE {numberLabel(recursive.selected_model.rmse_wh)} Wh, R² {numberLabel(recursive.selected_model.r2, 3)} across {recursive.origins} origins. {recursive.selected_model.r2 < 0 && "The negative R² means this horizon underperforms the test-period mean; use it as an exploratory profile, not a reliable schedule."}</p>}
      <div className="mt-6"><EnergyChart rows={evaluation.rows} title="Held-out actual vs predicted: final two recorded days" unit="Wh per ten-minute interval; one-step rolling origin" series={[{ key: "actual_wh", label: "Actual", color: "#5579b5" }, { key: "predicted_wh", label: "One-step prediction", color: "#159a82" }]} /></div>
      <section className={panelClass + " mt-6 overflow-x-auto"}><h2 className="text-lg font-semibold">Chronological model comparison</h2><p className="my-2 text-sm text-muted-foreground">Selected by validation MAE: {report.selected_model}. Training / validation / test use the oldest 70% / next 15% / final 15% after a 24-hour warmup.</p><table className="w-full text-left text-sm"><thead><tr className="border-b"><th className="py-3">Model</th><th>Validation MAE (Wh)</th><th>Test MAE (Wh)</th><th>Test RMSE (Wh)</th><th>Test R²</th></tr></thead><tbody>{Object.entries(report.comparison).map(([name, value]) => <tr key={name} className={"border-b " + (name === report.selected_model ? "bg-primary/5" : "")}><td className="py-3">{name.replace(/_/g, " ")}{name === report.selected_model ? " (selected)" : ""}</td><td>{numberLabel(value.validation.mae_wh)}</td><td>{numberLabel(value.test.mae_wh)}</td><td>{numberLabel(value.test.rmse_wh)}</td><td>{numberLabel(value.test.r2, 3)}</td></tr>)}</tbody></table><p className="mt-3 text-xs text-muted-foreground">One-step evaluation observes actual past readings as they arrive. Recursive evaluation uses only information available at each origin. Their scores answer different questions.</p></section>
    </>}
  </PageLayout>;
}
