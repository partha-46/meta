"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Button, Card, Pill } from "@/components/ui";
import { sos } from "@/lib/api";

function formatEta(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function SOSButton() {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<"idle" | "dispatched">("idle");
  const [eta, setEta] = useState<number>(0);
  const [tracking, setTracking] = useState<string>("");
  const [hospitalName, setHospitalName] = useState<string>("");
  const [statusTick, setStatusTick] = useState(0);
  const timerRef = useRef<number | null>(null);

  const last = useMemo(() => {
    if (typeof window === "undefined") return null;
    try {
      const raw = sessionStorage.getItem("lifeline:last_intake");
      return raw ? (JSON.parse(raw) as { location?: string; symptoms?: string }) : null;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, []);

  async function requestSOS() {
    setBusy(true);
    try {
      const location = last?.location || "Downtown";
      const symptoms = last?.symptoms || undefined;
      const res = await sos(location, symptoms);
      setStatus("dispatched");
      setEta(res.eta_seconds);
      setTracking(res.tracking_code);
      setHospitalName(res.nearest_hospital.name);
      if (timerRef.current) window.clearInterval(timerRef.current);
      timerRef.current = window.setInterval(() => {
        setEta((t) => (t > 0 ? t - 1 : 0));
        setStatusTick((v) => v + 1);
      }, 1000);
    } finally {
      setBusy(false);
    }
  }

  const progress = status === "dispatched" ? Math.max(0, Math.min(100, 100 - Math.floor((eta / 900) * 100))) : 0;
  const dispatchMsg =
    statusTick % 6 < 2
      ? "Nearest ICU notified"
      : statusTick % 6 < 4
        ? "Ambulance en route"
        : "Paramedic team preparing arrival";

  return (
    <>
      <button
        aria-label="Emergency SOS"
        onClick={() => setOpen(true)}
        className="animate-bounce-soft fixed bottom-5 right-5 z-50 flex h-16 w-16 items-center justify-center rounded-full bg-red-600 text-white shadow-lg shadow-red-600/30 ring-1 ring-red-200 hover:bg-red-700 active:scale-[0.98] focus:outline-none focus:ring-4 focus:ring-red-200"
      >
        <span className="text-sm font-extrabold tracking-wide">SOS</span>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 grid place-items-end bg-slate-950/70 p-4 sm:place-items-center">
          <div className="w-full max-w-md animate-fade-up">
            <Card>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-lg font-extrabold text-slate-900">Emergency SOS</div>
                  <div className="mt-1 text-sm text-slate-600">
                    This is a demo simulation of ambulance dispatch. If this is real, call your local emergency number.
                  </div>
                </div>
                <button
                  className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                  onClick={() => setOpen(false)}
                >
                  Close
                </button>
              </div>

              <div className="mt-5 space-y-3">
                {status === "idle" ? (
                  <>
                    <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-900">
                      <div className="font-semibold">When to use SOS</div>
                      <ul className="mt-2 list-disc pl-5 text-red-800/90 space-y-1">
                        <li>Severe chest pain, trouble breathing</li>
                        <li>Unresponsive / seizure / severe bleeding</li>
                        <li>Blue lips or sudden collapse</li>
                      </ul>
                    </div>
                    <Button variant="danger" onClick={requestSOS} disabled={busy}>
                      {busy ? "Dispatching..." : "Request Ambulance"}
                    </Button>
                  </>
                ) : (
                  <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <Pill className="animate-pulse-soft bg-emerald-600 text-white">Ambulance dispatched</Pill>
                      <div className="text-xs font-semibold text-emerald-900">Tracking: {tracking}</div>
                    </div>
                    <div className="mt-3 text-sm text-emerald-900">
                      Nearest hospital: <span className="font-semibold">{hospitalName}</span>
                    </div>
                    <div className="mt-2 text-sm text-emerald-900">
                      ETA: <span className="font-extrabold tabular-nums">{formatEta(eta)}</span>
                    </div>
                    <div className="mt-3 rounded-xl border border-emerald-200 bg-white/60 p-2">
                      <div className="h-2 w-full rounded-full bg-emerald-100">
                        <div className="h-2 rounded-full bg-emerald-600 transition-all duration-700" style={{ width: `${progress}%` }} />
                      </div>
                      <div className="mt-1 text-[11px] font-semibold text-emerald-800">{dispatchMsg}</div>
                    </div>
                    <div className="mt-3 text-xs text-emerald-800/90">
                      Stay calm. If safe, unlock the door and keep phone volume on.
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}

