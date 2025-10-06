import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

type Prefs = {
  agg_mode: "resample"|"groupby";
  drop_all_zero: boolean;
  theme: "light"|"dark";
  setAggMode: (m: "resample"|"groupby") => void;
  setDropAllZero: (v: boolean) => void;
  setTheme: (t: "light"|"dark") => void;
};

const PrefsCtx = createContext<Prefs | null>(null);
const KEY = "autodash:prefs";

export function PrefsProvider({ children }: { children: React.ReactNode }) {
  const [agg_mode, setAggMode] = useState<"resample"|"groupby">(() => {
    const raw = localStorage.getItem(KEY); return raw ? (JSON.parse(raw).agg_mode ?? "resample") : "resample";
  });
  const [drop_all_zero, setDropAllZero] = useState<boolean>(() => {
    const raw = localStorage.getItem(KEY); return raw ? !!(JSON.parse(raw).drop_all_zero) : true;
  });
  const [theme, setTheme] = useState<"light"|"dark">(() => {
    const raw = localStorage.getItem(KEY); return raw ? (JSON.parse(raw).theme ?? "light") : "light";
  });

  useEffect(() => { localStorage.setItem(KEY, JSON.stringify({ agg_mode, drop_all_zero, theme })); },
    [agg_mode, drop_all_zero, theme]);

  const value = useMemo(() => ({ agg_mode, drop_all_zero, theme, setAggMode, setDropAllZero, setTheme }),
    [agg_mode, drop_all_zero, theme]);

  return <PrefsCtx.Provider value={value}>{children}</PrefsCtx.Provider>;
}

export function usePrefs() {
  const ctx = useContext(PrefsCtx);
  if (!ctx) throw new Error("usePrefs must be used within PrefsProvider");
  return ctx;
}
