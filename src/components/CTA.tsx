import React, { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { usePrefs } from "../context/PrefsContext";

const CTA = () => {
  const nav = useNavigate();
  const { agg_mode, drop_all_zero } = usePrefs();
  const fileRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<{label:string; state:"idle"|"running"|"done"}[]>([
    { label: "Upload", state: "idle" },
    { label: "Detect (IA)", state: "idle" },
    { label: "Normalize", state: "idle" },
    { label: "Suggest (IA)", state: "idle" },
  ]);
  const [error, setError] = useState<string | null>(null);

  function openPicker() {
    setError(null);
    fileRef.current?.click();
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setLoading(true);
    setSteps(s => s.map((st,i)=> ({...st, state: i===0 ? "running":"idle"})));
    try {
      const resp = await api.pipeline(f, { agg_mode, drop_all_zero });
      setSteps(s => s.map(st => ({ ...st, state: "done" })));
      localStorage.setItem(`dash:${resp.normalized_dataset_id}`, JSON.stringify(resp.dashboard));
      nav(`/dashboard/${resp.normalized_dataset_id}`, { state: { fromPipeline: true } });
    } catch (e: any) {
      setError(e.message ?? String(e));
      setSteps(s => s.map(st => ({ ...st, state: "idle" })));
    } finally {
      setLoading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <section className="py-24 bg-background">
      <div className="container px-4">
        <div className="relative max-w-4xl mx-auto">
          <div className="absolute inset-0 bg-gradient-hero opacity-10 blur-3xl rounded-3xl" />
          <div className="relative bg-gradient-card rounded-3xl border-2 border-border p-12 text-center">
            <h2 className="text-4xl lg:text-5xl font-bold mb-4">
              Pronto para transformar suas{" "}
              <span className="bg-gradient-hero bg-clip-text text-transparent">planilhas em insights?</span>
            </h2>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Faça upload da sua primeira planilha e veja a mágica acontecer em minutos.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="hero" className="group" onClick={openPicker} disabled={loading}>
                <Upload className="h-5 w-5 transition-transform group-hover:scale-110" />
                {loading ? "Processando..." : "Começar Gratuitamente"}
              </Button>
              <input ref={fileRef} type="file" accept=".csv,.xlsx" hidden onChange={onFile} />
              <Button size="lg" variant="outline">
                Agendar Demo
                <ArrowRight className="h-5 w-5" />
              </Button>
            </div>

            <p className="text-sm text-muted-foreground mt-6">
              Sem cartão de crédito. Sem instalação. Resultados em 5 minutos.
            </p>

            {/* Feedback dos passos */}
            <div className="mt-4 text-sm space-y-1">
              {steps.map((s, i) => (
                <div key={i} className={s.state==="idle" ? "opacity-60" : ""}>
                  {s.state==="running" ? "⏳" : s.state==="done" ? "✅" : "•"} {s.label}
                </div>
              ))}
              {!!error && <div className="text-red-600 mt-2">Erro: {error}</div>}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTA;
