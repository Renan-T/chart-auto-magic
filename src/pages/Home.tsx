import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, PipelineResponse } from "../lib/api";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();

  async function run() {
    if (!file) return;
    setLoading(true); setLog([]);
    try {
      setLog(l => [...l, "Pipeline (upload+IA+normalize+suggest)..."]);
      const resp: PipelineResponse = await api.pipeline(file, { /* opcional: agg_mode/drop_all_zero */ });

      // cache local (fallback para a página de dashboard)
      localStorage.setItem(`dash:${resp.normalized_dataset_id}`, JSON.stringify(resp.dashboard));

      setLog(l => [...l, "OK! Redirecionando para o dashboard..."]);
      nav(`/dashboard/${resp.normalized_dataset_id}`);
    } catch (e: any) {
      setLog(l => [...l, "ERRO: " + (e?.message ?? String(e))]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>AutoDash BI Comercial (teste rápido)</h1>
      <input type="file" accept=".csv,.xlsx" onChange={e => setFile(e.target.files?.[0] ?? null)} />
      <button disabled={!file || loading} onClick={run}>
        {loading ? "Processando..." : "Gerar dashboard (pipeline)"}
      </button>
      <pre>{log.join("\n")}</pre>
    </div>
  );
}
