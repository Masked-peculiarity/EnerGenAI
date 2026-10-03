import { useState } from "react";
import PageLayout from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorState, panelClass } from "@/components/energy/Shared";
import { api } from "@/services/api";
interface Bill { source: string; fields: Record<string, string | number | null>; method: string; comparison: string }
export default function BillAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [data, setData] = useState<Bill | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const analyze = async () => {
    if (!file) return;
    setLoading(true); setError(""); setData(null);
    try { const body = new FormData(); body.append("file", file); setData(await api<Bill>("/api/bills/analyze", { method: "POST", body })); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not analyze the bill"); }
    finally { setLoading(false); }
  };
  return <PageLayout><h1 className="mb-2 text-3xl font-semibold">Electricity-bill extraction</h1><p className="mb-6 text-muted-foreground">Extract labeled fields locally, then check them against your original bill.</p><section className={panelClass}><Input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e => setFile(e.target.files?.[0] || null)} /><Button className="mt-4" disabled={!file || loading} onClick={() => void analyze()}>{loading ? "Extracting…" : "Extract bill fields"}</Button><p className="mt-3 text-sm text-muted-foreground">PDFs need selectable text. Image bills require local Tesseract OCR on the backend. Files are processed locally and are not sent to Groq.</p></section>{error && <ErrorState>{error}</ErrorState>}{data && <section className={panelClass + " mt-6"}><h2 className="mb-3 text-lg font-semibold">Review extracted fields</h2><dl className="grid gap-3 sm:grid-cols-2">{Object.entries(data.fields).map(([key, value]) => <div key={key}><dt className="text-sm text-muted-foreground">{key.replace(/_/g, " ")}</dt><dd className="font-medium">{value ?? "Not found — check the original bill"}</dd></div>)}</dl><p className="mt-5 text-sm">Confirm these fields before using them. Amounts retain the currency on the original bill.</p><p className="mt-3 text-sm text-muted-foreground">{data.comparison}</p></section>}</PageLayout>;
}
