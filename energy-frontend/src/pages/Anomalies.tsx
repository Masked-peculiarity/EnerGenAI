import { useEffect, useState } from "react";
import PageLayout from "@/components/layout/PageLayout";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DemoNotice, ErrorState, MetricCard, panelClass } from "@/components/energy/Shared";
import { api, numberLabel, timestampLabel } from "@/services/api";
import { Anomaly } from "@/types/energy";
interface Results { rows: Anomaly[]; total: number; truncated: boolean; residual_threshold_wh: number; meaning: string; evaluated_intervals?: number }
export default function Anomalies() {
  const [range, setRange] = useState({ start: "", end: "" });
  const [data, setData] = useState<Results | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError("");
    const params = new URLSearchParams(); if (range.start) params.set("start", range.start); if (range.end) params.set("end", range.end);
    api<Results>(`/api/anomalies?${params}`, { signal: controller.signal }).then(setData).catch(err => { if (err.name !== "AbortError") setError(err.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [range]);
  return <PageLayout><h1 className="mb-2 text-3xl font-semibold">Unusual energy consumption</h1><p className="mb-5 text-muted-foreground">Intervals flagged by unexpected forecast residuals or Isolation Forest. These flags do not diagnose equipment faults.</p><DemoNotice />
    <div className={panelClass + " mb-6 flex flex-wrap gap-4"}><div><Label htmlFor="anomaly-start">From</Label><Input id="anomaly-start" type="date" value={range.start} onChange={e => setRange({ ...range, start: e.target.value })} /></div><div><Label htmlFor="anomaly-end">Until (exclusive)</Label><Input id="anomaly-end" type="date" value={range.end} onChange={e => setRange({ ...range, end: e.target.value })} /></div><p className="w-full text-xs text-muted-foreground">Blank dates show the latest seven recorded days. Only validation/test intervals are evaluated; training-set scores are excluded.</p></div>
    {error && <ErrorState>{error}</ErrorState>}{loading && <p role="status">Loading unusual intervals…</p>}
    {!loading && !error && data && <><div className="mb-6 grid gap-4 sm:grid-cols-3"><MetricCard label="Flagged intervals" value={String(data.total)} /><MetricCard label="Residual threshold" value={numberLabel(data.residual_threshold_wh) + " Wh"} detail="Calibrated on validation residuals" /><MetricCard label="Evaluated intervals" value={String(data.evaluated_intervals ?? "See date coverage")} detail="Held-out observations only" /></div>
      {data.rows.length === 0 ? <p className={panelClass}>{data.evaluated_intervals === 0 ? "No held-out intervals are evaluated in this range." : "No unusual intervals were flagged in this range."}</p> : <section className={panelClass + " overflow-x-auto"}><table className="w-full text-left text-sm"><thead><tr className="border-b"><th className="py-3">Timestamp</th><th>Actual (Wh)</th><th>Expected (Wh)</th><th>Residual (Wh)</th><th>IF score</th><th>Evidence</th></tr></thead><tbody>{data.rows.map(row => <tr key={row.timestamp} className="border-b"><td className="py-3 pr-4 whitespace-nowrap">{timestampLabel(row.timestamp)}</td><td>{numberLabel(row.actual_wh, 0)}</td><td>{numberLabel(row.predicted_wh)}</td><td>{numberLabel(row.residual)}</td><td>{numberLabel(row.anomaly_score, 3)}</td><td>{[row.residual_flag && "Unexpected residual", row.isolation_flag && "Unusual feature combination"].filter(Boolean).join("; ")}</td></tr>)}</tbody></table>{data.truncated && <p className="mt-3 text-sm">Showing the first 200 flagged intervals. Narrow the date range for detail.</p>}</section>}</>}
  </PageLayout>;
}
