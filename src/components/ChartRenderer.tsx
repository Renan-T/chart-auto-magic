// src/components/ChartRenderer.tsx
import React from "react";
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area, BarChart, Bar,
  PieChart, Pie, Cell, CartesianGrid, XAxis, YAxis, Tooltip, Legend
} from "recharts";

type ChartSeries = { key: string; label: string; dashed?: boolean };
type LineAreaChart = { type: "line" | "area"; title: string; data: any[]; xKey: string; series: ChartSeries[] };
type BarChartT = { type: "bar" | "stacked_bar"; title: string; data: any[]; xKey: string; yKey: string };
type PieChartT = { type: "pie" | "donut"; title: string; data: { name: string; value: number }[]; categoryKey: string; valueKey: string };
export type ChartSpec = LineAreaChart | BarChartT | PieChartT;

function currencyTick(v: any) {
  // formata eixos com separador brasileiro (sem travar unit aqui)
  const n = Number(v);
  return isNaN(n) ? v : n.toLocaleString("pt-BR");
}

export default function ChartRenderer({ chart }: { chart: ChartSpec }) {
  if (!chart) return null;

  // LINE / AREA
  if (chart.type === "line" || chart.type === "area") {
    const series = chart.series ?? [];
    return (
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          {chart.type === "line" ? (
            <LineChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chart.xKey} />
              <YAxis tickFormatter={currencyTick} />
              <Tooltip />
              <Legend />
              {series.map((s, idx) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label || s.key}
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray={s.dashed ? "6 6" : undefined}
                />
              ))}
            </LineChart>
          ) : (
            <AreaChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chart.xKey} />
              <YAxis tickFormatter={currencyTick} />
              <Tooltip />
              <Legend />
              {series.map((s, idx) => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label || s.key}
                  strokeWidth={2}
                  // sem cores específicas: o Recharts usa paleta default
                />
              ))}
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    );
  }

  // BAR / STACKED BAR
  if (chart.type === "bar" || chart.type === "stacked_bar") {
    return (
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={chart.xKey} />
            <YAxis tickFormatter={currencyTick} />
            <Tooltip />
            <Legend />
            {/* Para simplificar: um eixo Y por chave (se quiser stacked, você pode
                adicionar múltiplas Bars, cada uma com dataKey distinta e same stackId) */}
            <Bar dataKey={chart.yKey} name={chart.yKey} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // PIE / DONUT
  if (chart.type === "pie" || chart.type === "donut") {
    const inner = chart.type === "donut" ? 60 : 0; // “donut” = pie com buraco
    return (
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <PieChart>
            <Tooltip />
            <Legend />
            <Pie
              data={chart.data}
              dataKey={chart.valueKey}
              nameKey={chart.categoryKey}
              innerRadius={inner}
              outerRadius={100}
              label={(e: any) => `${e.name}: ${Number(e.value).toLocaleString("pt-BR")}`}
            >
              {chart.data.map((entry, index) => (
                <Cell key={`cell-${index}`} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // fallback – nunca deve cair aqui se o backend mandar tipos válidos
  return <div>Tipo de gráfico não suportado: {(chart as any).type}</div>;
}
