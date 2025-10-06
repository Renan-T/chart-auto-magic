import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { api, DashboardDoc } from "../lib/api";
import ChartRenderer from "../components/ChartRenderer";

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}
function fmtKpi(k:{name:string; value:number; unit?:string}) {
  if (k.unit==="currency:BRL") return `R$ ${k.value.toLocaleString("pt-BR",{minimumFractionDigits:2, maximumFractionDigits:2})}`;
  if (k.unit==="percent") return `${(k.value*100).toFixed(1)}%`;
  return String(k.value);
}

export default function Dashboard() {
  const { ndsId } = useParams();
  const q = useQuery();
  const [doc, setDoc] = useState<DashboardDoc|null>(null);
  const [err, setErr] = useState<string|null>(null);
  const [loading, setLoading] = useState(true);

  const from = q.get("from"); // YYYY-MM
  const to = q.get("to");     // YYYY-MM

  useEffect(() => {
    (async () => {
      setLoading(true); setErr(null);
      try {
        const d = await api.latest(ndsId!);
        setDoc(d);
      } catch {
        const cache = localStorage.getItem(`dash:${ndsId}`);
        if (cache) setDoc(JSON.parse(cache) as DashboardDoc);
        else setErr("Dashboard não encontrado.");
      } finally {
        setLoading(false);
      }
    })();
  }, [ndsId]);

  const filtered = useMemo(() => {
    if (!doc) return doc;
    const clone: DashboardDoc = JSON.parse(JSON.stringify(doc));
    clone.charts = clone.charts.map(ch => {
      if ((ch.type==="line" || ch.type==="area") && ch.xKey === "month" && Array.isArray(ch.data)) {
        ch.data = ch.data.filter((row:any) => {
          const m = row["month"]; // "YYYY-MM"
          if (from && m < from) return false;
          if (to && m > to) return false;
          return true;
        });
      }
      return ch;
    });
    return clone;
  }, [doc, from, to]);

  if (loading) return <div style={{ padding:24 }}>Carregando dashboard...</div>;
  if (err) return <div style={{ padding:24, color:"#b91c1c" }}>{err}</div>;
  if (!filtered) return null;

  return (
    <div style={{ padding:24 }}>
      <h1>Dashboard</h1>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))", gap:12 }}>
        {filtered.kpis.map(k=>(
          <div key={k.name} style={{ padding:12, border:"1px solid #eee", borderRadius:8 }}>
            <div style={{ fontSize:12, color:"#666" }}>{k.name}</div>
            <div style={{ fontSize:22, fontWeight:700 }}>{fmtKpi(k)}</div>
          </div>
        ))}
      </div>

      {/* Gráficos */}
      <h2 style={{ marginTop:24 }}>Gráficos</h2>
      {filtered.charts.map((c,i)=>(
        <div key={i} style={{ padding:12, border:"1px solid #eee", borderRadius:8, marginBottom:12 }}>
          <div style={{ fontWeight:600, marginBottom:8 }}>{c.title}</div>
          <ChartRenderer chart={c as any} />
        </div>
      ))}

      {!!filtered.insights.length && (
        <>
          <h2>Insights</h2>
          <ul>
            {filtered.insights.map((ins, idx)=>(
              <li key={idx}><strong>[{ins.type}] {ins.title}:</strong> {ins.message}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
