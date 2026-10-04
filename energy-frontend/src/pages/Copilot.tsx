import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import PageLayout from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Bot, FileUp, Mic, MicOff, Send, User } from "lucide-react";
import { useSpeechToText } from "@/hooks/useSpeechToText";
import { DemoNotice, panelClass } from "@/components/energy/Shared";
import { api } from "@/services/api";
import { ChatResult } from "@/types/energy";
import { useEnergySettings } from "@/hooks/useEnergySettings";

interface Message { id: string; role: "user" | "assistant"; content: string; evidence?: ChatResult }
const questions = ["Why was usage high yesterday?", "What time is energy use highest?", "What does the next-hour forecast show?", "How can I reduce energy consumption?", "Explain unusual consumption."];
const toolNames: Record<string, string> = { get_energy_summary: "Energy summary", get_energy_timeseries: "History", forecast_energy: "Forecast", detect_anomalies: "Unusual intervals", get_peak_usage: "Peak usage", estimate_cost: "Cost estimate", estimate_carbon: "Carbon estimate", search_energy_knowledge: "Document evidence" };

export default function Copilot() {
  const [messages, setMessages] = useState<Message[]>([{ id: "welcome", role: "assistant", content: "Hello! I'm your Energy Assistant. I can explain the UCI demonstration household's consumption and forecasts, investigate unusual intervals, and retrieve energy-saving guidance or your uploaded documents. What would you like to explore?" }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const uploadInput = useRef<HTMLInputElement>(null);
  const { transcript, isListening, startListening, stopListening } = useSpeechToText();
  const { settings } = useEnergySettings();
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);
  useEffect(() => { if (transcript) setInput(transcript); }, [transcript]);
  const append = (content: string, evidence?: ChatResult) => setMessages(old => [...old, { id: crypto.randomUUID(), role: "assistant", content, evidence }]);
  const send = async () => {
    if (!input.trim() || busy) return;
    const conversation: Message[] = [...messages, { id: crypto.randomUUID(), role: "user", content: input.trim() }];
    setMessages(conversation); setInput(""); setBusy(true);
    try {
      const data = await api<ChatResult>("/api/agent/chat", { method: "POST", body: JSON.stringify({ messages: conversation.filter(message => message.id !== "welcome").slice(-12).map(({ role, content }) => ({ role, content: content.slice(0, 1000) })), ...(settings.tariff ? { tariff: Number(settings.tariff) } : {}), ...(settings.factor ? { factor: Number(settings.factor) } : {}) }) });
      append(data.reply, data);
    } catch (err) { append(err instanceof Error ? err.message : "Could not reach the Copilot"); }
    finally { setBusy(false); }
  };
  const upload = async (file?: File) => {
    if (!file || uploading) return;
    setUploading(true);
    try { const body = new FormData(); body.append("file", file); const data = await api<{ source: string; chunks: number }>("/api/documents", { method: "POST", body }); append(`Indexed ${data.source} into ${data.chunks} searchable sections. Ask a question about its contents.`); }
    catch (err) { append(err instanceof Error ? err.message : "Document upload failed"); }
    finally { setUploading(false); if (uploadInput.current) uploadInput.current.value = ""; }
  };
  return <PageLayout><div className="mx-auto max-w-5xl"><h1 className="mb-2 text-3xl font-semibold">Energy Copilot</h1><p className="mb-5 text-muted-foreground">Answers combine computed energy evidence with graded document passages.</p><DemoNotice />
    <div className={panelClass + " flex h-[65vh] min-h-[480px] flex-col p-0"}>
      <div className="flex-1 space-y-5 overflow-y-auto p-5" aria-live="polite">{messages.map(message => <div key={message.id} className={"flex gap-3 " + (message.role === "user" ? "flex-row-reverse" : "")}>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">{message.role === "assistant" ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}</div>
        <div className={"max-w-[90%] rounded-xl px-4 py-3 text-sm " + (message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted/70")}><p className="whitespace-pre-wrap">{message.content}</p>
          {message.evidence && <div className="mt-3 border-t pt-3 text-xs text-muted-foreground"><p>{message.evidence.mode === "ai" ? "AI answer grounded in retrieved evidence" : "Computed evidence and local excerpts"}</p><p className="mt-1">Tools: {message.evidence.tool_trace.map(tool => (toolNames[tool.tool] || tool.tool) + (tool.status === "ok" ? "" : " (unavailable)")).join(" · ")}</p><p className="mt-1">Retrieval: {message.evidence.retrieval_trace.map(step => step.stage + (step.accepted != null ? ` (${step.accepted} accepted)` : "")).join(" → ")}</p>
            {!!message.evidence.sources.length && <ul className="mt-2 space-y-1">{message.evidence.sources.map(source => <li key={source.citation}>[{source.citation}] {source.url ? <a className="underline" href={source.url} target="_blank" rel="noreferrer">{source.source}</a> : source.source}{source.private ? `, section ${source.section}` : ""} · {source.authority}</li>)}</ul>}
          </div>}
        </div></div>)}{busy && <p role="status" className="text-sm text-muted-foreground">Checking energy tools and document evidence…</p>}<div ref={bottom} /></div>
      {messages.length === 1 && <div className="flex flex-wrap gap-2 px-5 pb-4">{questions.map(question => <button key={question} onClick={() => setInput(question)} className="rounded-full border px-3 py-1.5 text-sm hover:bg-muted">{question}</button>)}</div>}
      <div className="border-t p-4"><div className="flex gap-2"><Button variant="outline" size="icon" disabled={uploading || !localStorage.getItem("token")} onClick={() => uploadInput.current?.click()} title="Upload your private PDF, TXT, or Markdown document" aria-label="Upload private document"><FileUp className="h-4 w-4" /></Button><input ref={uploadInput} hidden type="file" accept=".pdf,.txt,.md" onChange={e => void upload(e.target.files?.[0])} /><Button variant="outline" size="icon" onClick={isListening ? stopListening : startListening} aria-label={isListening ? "Stop voice input" : "Start voice input"}>{isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}</Button><Input maxLength={1000} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); void send(); } }} placeholder="Ask about usage, forecasts, anomalies, or saving energy" aria-label="Energy question" /><Button size="icon" disabled={busy || !input.trim()} onClick={() => void send()} aria-label="Send question"><Send className="h-4 w-4" /></Button></div><p className="mt-2 text-xs text-muted-foreground">When Groq is configured, chat, computed summaries, and matching document excerpts are sent to it. Local evidence remains available without a working key. {!localStorage.getItem("token") && <Link to="/login" className="underline">Log in to upload private documents.</Link>}</p></div>
    </div></div></PageLayout>;
}
