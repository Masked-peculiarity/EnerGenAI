export interface Metric { mae_wh: number; rmse_wh: number; r2: number; smape_percent: number }
export interface ModelReport {
  selected_model: string;
  comparison: Record<string, { validation: Metric; test: Metric; fit_seconds: number }>;
  recursive_test: Record<string, { horizon_minutes: number; origins: number; selected_model: Metric; persistence: Metric }>;
  dataset: { start: string; end: string; rows: number; interval_minutes: number };
  splits: Record<string, { rows: number; start: string; end: string }>;
}
export interface ForecastResult {
  origin: string; horizon_minutes: number; total_kwh: number; model: string; method: string;
  predictions: { timestamp: string; appliances_wh: number; actual_wh?: number }[];
}
export interface EnergySummary {
  source: string; period_start: string; period_end: string; observations: number;
  latest_appliances_wh: number; total_appliance_kwh: number; lighting_kwh: number;
  average_hourly_wh: number | null; daily_average_kwh: number | null;
  latest_recorded_day: string; latest_day_kwh: number; latest_day_intervals: number;
  peak_interval: { timestamp: string; appliances_wh: number };
  peak_hour: { timestamp: string; appliances_wh: number; intervals: number };
  unusual_intervals: number | null; predicted_next_hour_kwh: number;
  estimated_cost: number | null; estimated_carbon_kg: number | null;
}
export interface Timeseries { rows: { timestamp: string; appliances_wh: number; lights_wh: number }[]; truncated: boolean }
export interface Anomaly { timestamp: string; actual_wh: number; predicted_wh: number; residual: number; anomaly_score: number; is_anomaly: boolean; residual_flag: boolean; isolation_flag: boolean; split: string }
export interface Source { citation: string; source: string; section?: number; page?: number; authority?: string; url?: string; excerpt?: string; private?: boolean }
export interface ChatResult { reply: string; mode: string; sources: Source[]; tool_trace: { tool: string; status: string }[]; retrieval_trace: { stage: string; accepted?: number; query?: string }[] }
