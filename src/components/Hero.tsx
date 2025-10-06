// src/components/Hero.tsx
import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "../lib/api";
import { usePrefs } from "../context/PrefsContext";

type Stage = { name: string; status: "idle" | "running" | "done" };

export default function Hero() {
  const nav = useNavigate();
  const { agg_mode, drop_all_zero } = usePrefs();
  const fileRef = useRef<HTMLInputElement>(null);

  const [stages, setStages] = useState<Stage[]>([
    { name: "Upload", status: "idle" },
    { name: "Detect (IA)", status: "idle" },
    { name: "Normalize", status: "idle" },
    { name: "Suggest (IA)", status: "idle" },
  ]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function openPicker() {
    setErr(null);
    fileRef.current?.click();
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;

    setLoading(true);
    // feedback visual otimista: marca o primeiro passo como "running"
    setStages(s => s.map((t, i) => (i === 0 ? { ...t, status: "running" } : { ...t, status: "idle" })));

    try {
      // chamada única ao backend (pipeline completo)
      const resp = await api.pipeline(f, { agg_mode, drop_all_zero });

      // quando retorna, marcamos tudo como concluído (o trabalho ocorreu no backend)
      setStages(s => s.map(t => ({ ...t, status: "done" })));

      // cache local para fallback do /dashboard/:id
      localStorage.setItem(`dash:${resp.normalized_dataset_id}`, JSON.stringify(resp.dashboard));

      // navegação com dado efêmero em state
      nav(`/dashboard/${resp.normalized_dataset_id}`, { state: { fromPipeline: true } });
    } catch (e: any) {
      setErr(e?.message ?? String(e));
      setStages(s => s.map(t => ({ ...t, status: "idle" })));
    } finally {
      setLoading(false);
      if (fileRef.current) fileRef.current.value = ""; // permite reenviar o mesmo arquivo depois
    }
  }

  return (
    <section className="relative overflow-hidden py-20 lg:py-28 bg-background">
      {/* fundo suave/gradiente */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-b from-indigo-50/70 to-transparent dark:from-indigo-950/20" />
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 h-72 w-[80%] rounded-[48px] blur-3xl opacity-20 bg-gradient-to-r from-indigo-400 via-fuchsia-400 to-cyan-400 dark:opacity-25" />
      </div>

      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-5xl text-center">
          <span className="inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground">
            AutoDash BI Comercial
          </span>

          <h1 className="mt-4 text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            Dashboards comerciais{" "}
            <span className="bg-gradient-to-r from-indigo-500 via-fuchsia-500 to-cyan-500 bg-clip-text text-transparent">
              em minutos
            </span>{" "}
            a partir de planilhas
          </h1>

          <p className="mx-auto mt-4 max-w-3xl text-lg text-muted-foreground">
            Faça upload do seu arquivo <strong>CSV/XLSX</strong> e receba KPIs, gráficos e insights automaticamente.
            O backend detecta colunas, normaliza e calcula tudo – você só vê o dashboard pronto.
          </p>

          {/* CTAs */}
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" className="group" onClick={openPicker} disabled={loading}>
              <Upload className="mr-2 h-5 w-5 transition-transform group-hover:scale-110" />
              {loading ? "Processando..." : "Começar Gratuitamente"}
            </Button>

            <input
              ref={fileRef}
              type="file"
              accept=".csv,.xlsx"
              hidden
              onChange={onFile}
            />

            <Button size="lg" variant="outline" onClick={() => window.open("#agenda-demo", "_self")}>
              Agendar demo
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>

          {/* indicadores de etapas */}
          <div className="mx-auto mt-5 w-full max-w-sm text-left text-sm">
            {stages.map((t, idx) => (
              <div
                key={idx}
                className={`flex items-center gap-2 ${t.status === "idle" ? "opacity-60" : ""}`}
              >
                <span>{t.status === "running" ? "⏳" : t.status === "done" ? "✅" : "•"}</span>
                <span>{t.name}</span>
              </div>
            ))}
            {!!err && <div className="mt-2 text-sm text-red-600">Erro: {err}</div>}
          </div>

          {/* “faixas” de confiança / bullets rápidos */}
          <div className="mx-auto mt-8 grid max-w-4xl grid-cols-1 gap-3 text-sm text-muted-foreground sm:grid-cols-3">
            <div className="rounded-xl border bg-card p-3 text-center">Sem cartão de crédito</div>
            <div className="rounded-xl border bg-card p-3 text-center">Suporte a CSV e XLSX</div>
            <div className="rounded-xl border bg-card p-3 text-center">Resultados em minutos</div>
          </div>
        </div>

        {/* mock de vitrine/print do dashboard – opcional */}
        <div className="mx-auto mt-12 max-w-6xl rounded-3xl border bg-card p-4 shadow-sm">
          <div className="aspect-[16/9] w-full rounded-2xl border bg-muted/40" />
        </div>
      </div>
    </section>
  );
}
