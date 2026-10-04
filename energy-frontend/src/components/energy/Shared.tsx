import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { timestampLabel } from "@/services/api";

export const panelClass = "rounded-xl border bg-card p-5";
export function DemoNotice() {
  return <div className="mb-6 rounded-lg border bg-muted/50 px-4 py-3 text-sm text-muted-foreground">UCI demonstration household · Belgium, January–May 2016 · Energy in Wh per 10-minute interval. These readings describe the research dataset, not your home. <Link className="underline" to="/forecast">View evaluation</Link>.</div>;
}
export function MetricCard({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <div className={panelClass}><p className="text-sm text-muted-foreground">{label}</p><p className="mt-2 text-2xl font-semibold">{value}</p>{detail && <p className="mt-2 text-xs text-muted-foreground">{detail}</p>}</div>;
}
export function ErrorState({ children }: { children: ReactNode }) {
  return <p role="alert" className="my-4 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm">{children}</p>;
}
export function EnergyChart({ rows, series, title, unit }: { rows: object[]; series: { key: string; label: string; color: string }[]; title: string; unit: string }) {
  return <section className={panelClass}><h2 className="mb-1 text-lg font-semibold">{title}</h2><p className="mb-4 text-xs text-muted-foreground">UCI dataset local timestamps · {unit}</p><div className="h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={rows}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="timestamp" tickFormatter={(v: string) => timestampLabel(v).slice(5)} minTickGap={65} /><YAxis width={55} label={{ value: "Wh", angle: -90, position: "insideLeft" }} /><Tooltip labelFormatter={(v) => timestampLabel(String(v))} />{series.map(item => <Line isAnimationActive={false} key={item.key} type="linear" dataKey={item.key} name={item.label} stroke={item.color} dot={false} strokeWidth={1.6} />)}</LineChart></ResponsiveContainer></div><div className="mt-3 flex flex-wrap gap-5 text-sm">{series.map(item => <span key={item.key} className="flex items-center gap-2"><span className="h-2 w-5" style={{ backgroundColor: item.color }} />{item.label}</span>)}</div></section>;
}
