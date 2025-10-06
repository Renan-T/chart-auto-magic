const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function http<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, opts);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText} - ${await r.text()}`);
  return r.json() as Promise<T>;
}

export type KPI = { name: string; value: number; unit?: "number"|"percent"|"currency:BRL" };
export type ChartSeries = { key: string; label: string; dashed?: boolean };
export type Chart =
  | { type: "line"|"area"; title: string; data: any[]; xKey: string; series: ChartSeries[] }
  | { type: "bar"|"stacked_bar"; title: string; data: any[]; xKey: string; yKey: string }
  | { type: "pie"|"donut"; title: string; data: { name: string; value: number }[]; categoryKey: string; valueKey: string };
export type Insight = { type: "positive"|"warning"|"info"; title: string; message: string };
export type DashboardDoc = { dataset_id: string; kpis: KPI[]; charts: Chart[]; insights: Insight[]; version: string };

export type PipelineResponse = {
  dataset_id: string;
  normalized_dataset_id: string;
  dashboard: DashboardDoc;
  stages: { name: string; start: string; end: string|null; meta: any }[];
};

export const api = {
  pipeline: async (file: File, opts?: { model?: string; agg_mode?: "resample"|"groupby"; drop_all_zero?: boolean }) => {
    const fd = new FormData();
    fd.append("file", file);
    if (opts?.model) fd.append("model", opts.model);
    if (opts?.agg_mode) fd.append("agg_mode", opts.agg_mode);
    if (typeof opts?.drop_all_zero === "boolean") fd.append("drop_all_zero", String(opts.drop_all_zero));
    return http<PipelineResponse>("/api/pipeline/auto", { method: "POST", body: fd });
  },
  latest: (ndsId: string) => http<DashboardDoc>(`/api/dash/latest/${ndsId}`),
};
