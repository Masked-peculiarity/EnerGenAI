import { FormEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import PageLayout from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ErrorState, MetricCard, panelClass } from "@/components/energy/Shared";
import { api, numberLabel } from "@/services/api";

type Mode = "conditions" | "home";
interface Scores { mae: number; rmse: number; r2: number }
interface Report {
  source: string; source_url: string; unit: string; rows: number; selected_model: string;
  warning: string; split_policy: string; metrics: Scores;
  ranges: Record<string,{min:number;max:number;default:number}>;
  choices: Record<string,number[]>; features:string[];
  examples:{inputs:Record<string,number>;actual:number}[];
}
interface Prediction {
  estimate:number;unit:string;model:string;warnings:string[];monthly_average_kwh:number|null;
  interval:{lower:number;upper:number;nominal_coverage:number;test_coverage:number};
}
const labels:Record<string,string> = {
  temperature_c:"Average room temperature (°C)",humidity_percent:"Average room humidity (%)",
  lighting_wh:"Lighting energy (Wh per 10 minutes)",outdoor_temperature_c:"Outdoor temperature (°C)",
  hour:"Hour of day (0–23.99)",day_of_week:"Day of week",month:"Month",
  floor_area_sqft:"Energy-consuming floor area (sq ft)",occupants:"Household members (7 means 7 or more)",
  heating_degree_days:"Annual heating degree days (base 65°F)",cooling_degree_days:"Annual cooling degree days (base 65°F)",
  home_type:"Home type",heating_fuel:"Main heating fuel",air_conditioning:"Air conditioning used"
};
const options:Record<string,Record<number,string>> = {
  day_of_week:{0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"},
  month:{1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"},
  home_type:{1:"Mobile home",2:"Detached house",3:"Attached house / townhome",4:"Apartment (2–4 units)",5:"Apartment (5+ units)"},
  heating_fuel:{1:"Natural gas",2:"Propane",3:"Fuel oil",5:"Electricity",7:"Wood / pellets",99:"Other",[-2]:"No applicable heating fuel"},
  air_conditioning:{0:"No",1:"Yes"}
};
const boundaries:Record<string,[number,number]> = {
  temperature_c:[-30,60],humidity_percent:[0,100],lighting_wh:[0,10000],outdoor_temperature_c:[-80,80],
  hour:[0,23.99],floor_area_sqft:[1,100000],occupants:[1,7],heating_degree_days:[0,25000],cooling_degree_days:[0,25000]
};
export default function Predictor() {
  const [mode,setMode] = useState<Mode>("conditions");
  const [reports,setReports] = useState<Record<Mode,Report>|null>(null);
  const [values,setValues] = useState<Record<string,string>>({});
  const [result,setResult] = useState<Prediction|null>(null);
  const [actual,setActual] = useState<number|null>(null);
  const [error,setError] = useState("");
  const [busy,setBusy] = useState(false);
  const request = useRef<AbortController|null>(null);
  const report = reports?.[mode];
  useEffect(()=>{
    const controller=new AbortController();
    api<Record<Mode,Report>>("/api/prediction/models",{signal:controller.signal})
      .then(setReports).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
    return ()=>{controller.abort();request.current?.abort();};
  },[]);
  useEffect(()=>{
    request.current?.abort();setBusy(false);setResult(null);setActual(null);
    if(!report)return;
    setError("");
    setValues(Object.fromEntries(report.features.map(key=>[key,String(options[key] ?
      (report.choices[key]?.[0] ?? Number(Object.keys(options[key])[0])) : Number(report.ranges[key].default.toFixed(2)))])));
  },[mode,report]);
  const submit=async(event:FormEvent)=>{
    event.preventDefault();
    request.current?.abort();
    const controller=new AbortController();request.current=controller;
    setBusy(true);setError("");setResult(null);
    try {
      const prediction=await api<Prediction>("/api/prediction",{method:"POST",signal:controller.signal,
        body:JSON.stringify({mode,inputs:Object.fromEntries(Object.entries(values).map(([key,value])=>[key,Number(value)]))})});
      if(!controller.signal.aborted)setResult(prediction);
    } catch(e){if(!controller.signal.aborted)setError((e as Error).message);}
    finally{if(!controller.signal.aborted)setBusy(false);}
  };
  return <PageLayout>
    <h1 className="mt-5 text-3xl font-semibold">Energy consumption predictor</h1>
    <p className="my-3 text-muted-foreground">Enter conditions or a home profile. For future consumption from recorded history, use <Link className="underline" to="/forecast">Forecast</Link>.</p>
    <div className="my-6 flex flex-wrap gap-3" role="group" aria-label="Prediction model">
      <Button variant={mode==="conditions"?"default":"outline"} onClick={()=>setMode("conditions")}>Appliance conditions</Button>
      <Button variant={mode==="home"?"default":"outline"} onClick={()=>setMode("home")}>Home profile</Button>
    </div>
    {!reports && !error && <p role="status">Loading prediction models...</p>}
    {error && <ErrorState>{error}</ErrorState>}
    {report && <>
      <section className="mb-6 rounded-lg border bg-muted/50 p-4 text-sm">
        <p>{report.source}. <a className="underline" href={report.source_url} target="_blank" rel="noreferrer">Dataset source</a></p>
        <p className="mt-2">{report.warning}</p>
        {report.metrics.r2<=0 && <p className="mt-2 font-medium">Weak predictive skill: held-out R² is non-positive. Use this mode for exploration, not reliable household planning.</p>}
      </section>
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <form onSubmit={submit} className={panelClass}>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Input conditions</h2>
            <Button type="button" variant="outline" onClick={()=>{
              request.current?.abort();setBusy(false);
              const example=report.examples[0];
              setValues(Object.fromEntries(Object.entries(example.inputs).map(([key,value])=>[key,String(value)])));
              setActual(example.actual);setResult(null);setError("");
            }}>Load held-out example</Button>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">{report.features.map(key=><div key={key}>
            <Label htmlFor={"predict-"+key}>{labels[key]}</Label>
            {options[key] ? <select id={"predict-"+key} required className="mt-2 h-10 w-full rounded-md border bg-background px-3 text-sm" value={values[key]??""} onChange={e=>{request.current?.abort();setBusy(false);setValues({...values,[key]:e.target.value});setActual(null);setResult(null);}}>
              {Object.entries(options[key]).filter(([value])=>!report.choices[key] || report.choices[key].includes(Number(value))).map(([value,label])=><option key={value} value={value}>{label}</option>)}
            </select> : <Input id={"predict-"+key} required type="number" className="mt-2" min={boundaries[key]?.[0]} max={boundaries[key]?.[1]} step={key==="occupants"?1:"any"} value={values[key]??""} onChange={e=>{request.current?.abort();setBusy(false);setValues({...values,[key]:e.target.value});setActual(null);setResult(null);}}/>}
            {report.ranges[key] && <p className="mt-1 text-xs text-muted-foreground">Training range: {numberLabel(report.ranges[key].min)} to {numberLabel(report.ranges[key].max)}</p>}
          </div>)}</div>
          <p className="mt-4 text-xs text-muted-foreground">{mode==="conditions" ?
            "Room inputs are averages across nine room sensors. Lighting is energy, not bulb wattage: 60 W for 10 minutes = 10 Wh. Hour 18.5 means 18:30. Defaults are training medians, not measurements from your home." :
            "Use annual local heating/cooling degree days with a 65°F base, not today's temperature. Floor area includes energy-consuming basements/attics. Defaults describe the training data, not your home. Solar and momentary HVAC On/Off are not model inputs."}</p>
          <Button className="mt-5 w-full" disabled={busy} type="submit">{busy?"Predicting...":"Predict consumption"}</Button>
        </form>
        <section className={panelClass} aria-live="polite"><h2 className="text-lg font-semibold">Prediction result</h2>
          {!result ? <p className="mt-4 text-muted-foreground">Complete the inputs, then predict consumption.</p> : <>
            <p className="mt-4 text-3xl font-semibold" data-testid="prediction-value">{numberLabel(result.estimate)} <span className="text-base">{result.unit}</span></p>
            <p className="mt-3 text-sm">Nominal 80% prediction interval: {numberLabel(result.interval.lower)}–{numberLabel(result.interval.upper)} {result.unit}.</p>
            <p className="mt-2 text-xs text-muted-foreground">Observed held-out coverage: {numberLabel(result.interval.test_coverage*100,1)}%. Coverage is not guaranteed for another region, household, or future conditions.</p>
            {result.monthly_average_kwh!==null && <p className="mt-4 text-sm">Annual estimate ÷ 12: {numberLabel(result.monthly_average_kwh)} kWh/month on average. This is not a seasonal monthly prediction.</p>}
            {actual!==null && <div className="mt-5 rounded-md border p-3"><p>Held-out actual: {numberLabel(actual)} {result.unit}</p><p>Absolute error for this example: {numberLabel(Math.abs(actual-result.estimate))} {result.unit}</p><p className="mt-2 text-xs text-muted-foreground">This observation was excluded from fitting, selection, and calibration. A single example does not prove model accuracy.</p></div>}
            <ul className="mt-5 list-disc space-y-2 pl-5 text-sm">{result.warnings.map(w=><li key={w}>{w}</li>)}</ul>
          </>}
        </section>
      </div>
      <section className="mt-6"><h2 className="mb-3 text-lg font-semibold">Measured performance on unseen data</h2>
        <div className="grid gap-4 sm:grid-cols-3"><MetricCard label="Test MAE" value={numberLabel(report.metrics.mae)} detail={report.unit}/><MetricCard label="Test RMSE" value={numberLabel(report.metrics.rmse)} detail={report.unit}/><MetricCard label="Test R²" value={numberLabel(report.metrics.r2,3)} detail="Regression score, not percentage accuracy"/></div>
        <p className="mt-3 text-xs text-muted-foreground">{report.rows.toLocaleString()} source records. Model: {report.selected_model}. {report.split_policy}. Conditions and home-profile targets are not added or averaged.</p>
      </section>
    </>}
  </PageLayout>;
}
