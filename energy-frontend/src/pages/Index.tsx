import { Link } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";
import { DemoNotice, panelClass } from "@/components/energy/Shared";
export default function Index() {
  return <div className="min-h-screen bg-slate-50"><Navbar /><main className="mx-auto max-w-6xl px-6 pb-16 pt-32">
    <p className="text-sm font-medium text-emerald-700">ENERGY ANALYTICS WORKSPACE</p>
    <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-900">Understand consumption. Explore what comes next.</h1>
    <p className="mt-5 max-w-2xl text-lg text-slate-600">Measured energy data, chronological forecasting, unusual-consumption detection, and a source-backed Energy Copilot.</p>
    <div className="my-7 flex gap-3"><Link className="rounded-lg bg-emerald-700 px-5 py-3 text-white" to="/dashboard">Explore dashboard</Link></div>
    <DemoNotice />
    <div className="mt-8 grid gap-4 md:grid-cols-2">{[
      ["/dashboard","Measured consumption","Inspect appliance and lighting energy, peak periods, optional cost and carbon estimates."],
      ["/forecast","Forecast and compare","Predict the next hour or day and compare held-out predictions with measured observations."],
      ["/anomalies","Unusual usage","Review residual and Isolation Forest flags. These are not fault diagnoses."],
      ["/copilot","Energy Copilot","Ask about consumption and energy-saving guidance, with citations and tool traces."]
    ].map(([url,title,description]) => <Link key={url} to={url} className={panelClass}><h2 className="text-lg font-semibold">{title}</h2><p className="mt-2 text-slate-600">{description}</p></Link>)}</div>
    <section className={panelClass+" mt-6"}><h2 className="font-semibold">Your account and documents</h2><p className="mt-2 text-slate-600">Add private reference documents through Copilot and extract bill fields through Bills. Manage your account from the profile menu. The dataset is shared, not your home or a live smart meter. Day-ahead forecasts remain experimental.</p></section>
  </main></div>;
}
