import { useEffect, useState } from "react";
import PageLayout from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DemoNotice, EnergyChart, ErrorState, MetricCard, panelClass } from "@/components/energy/Shared";
import { api, numberLabel, timestampLabel } from "@/services/api";
import { EnergySummary, Timeseries } from "@/types/energy";
import { useEnergySettings } from "@/hooks/useEnergySettings";

export default function Dashboard() {
  const { settings, setSettings } = useEnergySettings();
  const [range, setRange] = useState({ start: "", end: "" });
  const [summary, setSummary] = useState<EnergySummary | null>(null);
  const [series, setSeries] = useState<Timeseries | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries({ ...range, ...settings })) if (value) params.set(key, value);
    const times = new URLSearchParams();
    if (range.start) times.set("start", range.start);
    if (range.end) times.set("end", range.end);
    times.set("resolution", "hour");
    Promise.all([api<EnergySummary>(`/api/analytics/summary?${params}`, { signal: controller.signal }), api<Timeseries>(`/api/analytics/timeseries?${times}`, { signal: controller.signal })])
      .then(([data, trend]) => { setSummary(data); setSeries(trend); })
      .catch(err => { if (err.name !== "AbortError") setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [range, settings, refresh]);
  return <PageLayout><h1 className="mb-2 text-3xl font-semibold">Energy dashboard</h1><p className="mb-5 text-muted-foreground">Measured appliance use, forecasts, and unusual intervals from the research household.</p><DemoNotice />
    <div className={panelClass + " mb-6 grid gap-4 sm:grid-cols-4"}>
      <div><Label htmlFor="start">From (optional)</Label><Input id="start" type="date" value={range.start} onChange={e => setRange({ ...range, start: e.target.value })} /></div>
      <div><Label htmlFor="end">Until (exclusive)</Label><Input id="end" type="date" value={range.end} onChange={e => setRange({ ...range, end: e.target.value })} /></div>
      <div><Label htmlFor="tariff">Rate per kWh (your currency)</Label><Input id="tariff" type="number" min="0" step="0.01" placeholder="Enter your rate" value={settings.tariff} onChange={e => setSettings({ ...settings, tariff: e.target.value })} /></div>
      <div><Label htmlFor="factor">Grid factor (kg CO2 / kWh)</Label><Input id="factor" type="number" min="0" step="0.01" placeholder="Enter regional factor" value={settings.factor} onChange={e => setSettings({ ...settings, factor: e.target.value })} /></div>
      <p className="text-xs text-muted-foreground sm:col-span-4">Blank dates show the latest seven recorded days. Cost and carbon cover the appliance channel and require your own assumptions. Settings are saved in this browser.</p>
    </div>
    {error && <ErrorState>{error} <Button variant="outline" size="sm" onClick={() => setRefresh(refresh + 1)}>Retry</Button></ErrorState>}
    {loading && <p role="status">Loading analytics…</p>}
    {!loading && !error && summary && series && <>
      <p className="mb-4 text-sm text-muted-foreground">{timestampLabel(summary.period_start)} to {timestampLabel(summary.period_end)} · {summary.observations.toLocaleString()} recorded intervals</p>
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Latest appliance interval" value={numberLabel(summary.latest_appliances_wh, 0) + " Wh"} detail={timestampLabel(summary.period_end)} />
        <MetricCard label="Latest recorded day" value={numberLabel(summary.latest_day_kwh) + " kWh"} detail={summary.latest_recorded_day + " · " + summary.latest_day_intervals + "/144 intervals recorded"} />
        <MetricCard label="Next-hour forecast" value={numberLabel(summary.predicted_next_hour_kwh) + " kWh"} detail="From the dataset's latest observation" />
        <MetricCard label="Unusual intervals" value={summary.unusual_intervals == null ? "Not evaluated" : String(summary.unusual_intervals)} detail="Residual or Isolation Forest flag" />
        <MetricCard label="Selected-period appliances" value={numberLabel(summary.total_appliance_kwh) + " kWh"} />
        <MetricCard label="Lighting energy" value={numberLabel(summary.lighting_kwh) + " kWh"} detail="Separate lighting channel" />
        <MetricCard label="Estimated appliance cost" value={numberLabel(summary.estimated_cost)} detail="Your rate's currency; excludes fees and taxes" />
        <MetricCard label="Estimated carbon" value={numberLabel(summary.estimated_carbon_kg) + (summary.estimated_carbon_kg == null ? "" : " kg CO2")} detail="Using your regional emissions factor" />
      </div>
      <EnergyChart rows={series.rows} title="Recorded hourly energy" unit="Wh per hour; edge hours may be partial" series={[{ key: "appliances_wh", label: "Appliances", color: "#159a82" }, { key: "lights_wh", label: "Lighting", color: "#5579b5" }]} />
      {series.truncated && <p className="mt-2 text-sm">Trend is limited to the first 1,000 hourly points. Narrow the date range for more detail.</p>}
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <MetricCard label="Average complete hour" value={numberLabel(summary.average_hourly_wh) + " Wh"} />
        <MetricCard label="Average complete day" value={numberLabel(summary.daily_average_kwh) + " kWh"} />
        <MetricCard label="Highest-use hour" value={numberLabel(summary.peak_hour.appliances_wh, 0) + " Wh"} detail={timestampLabel(summary.peak_hour.timestamp)} />
      </div>
    </>}
  </PageLayout>;
}
