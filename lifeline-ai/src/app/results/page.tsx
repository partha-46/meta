"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { analyze, AnalyzeResult } from "@/lib/api";
import { urgencyMeta } from "@/lib/demo";
import { Button, Card, Container, Pill, TopNav } from "@/components/ui";
import { SOSButton } from "@/components/SOSButton";

type Intake = { symptoms: string; location: string; uploaded_files: string[] };

export default function ResultsPage() {
  const [intake] = useState<Intake | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      const raw = sessionStorage.getItem("lifeline:last_intake");
      return raw ? (JSON.parse(raw) as Intake) : null;
    } catch {
      return null;
    }
  });
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [liveConfidence, setLiveConfidence] = useState(0.25);

  useEffect(() => {
    if (!intake) return;
    let cancelled = false;
    analyze(intake)
      .then((r) => {
        if (cancelled) return;
        setResult(r);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e?.message ?? "Failed to analyze");
      })
      .finally(() => {
        if (cancelled) return;
      });
    return () => {
      cancelled = true;
    };
  }, [intake]);

  useEffect(() => {
    if (result || error) return;
    const t = window.setInterval(() => {
      setLiveConfidence((v) => Math.min(0.94, v + 0.03));
    }, 350);
    return () => window.clearInterval(t);
  }, [result, error]);

  const meta = useMemo(() => {
    if (!result) return null;
    return urgencyMeta(result.urgency);
  }, [result]);

  return (
    <div className="min-h-full bg-gradient-to-b from-white to-slate-50">
      <TopNav />
      <main className="py-10 sm:py-14">
        <Container>
          <div className="flex items-start justify-between gap-4">
            <div>
              <Pill className="bg-slate-100 text-slate-800">AI-assisted triage • Not a diagnosis</Pill>
              <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">Your results</h1>
              <p className="mt-2 max-w-2xl text-slate-600">
                We provide <span className="font-semibold">possible / likely</span> guidance only. If you feel unsafe, use SOS.
              </p>
            </div>
            <Link
              href="/"
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              New check
            </Link>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <div className="text-sm font-semibold text-slate-900">Your input</div>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-xs font-semibold text-slate-600">Symptoms</div>
                    <div className="mt-1 text-sm text-slate-900">{intake?.symptoms || "—"}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-xs font-semibold text-slate-600">Location</div>
                    <div className="mt-1 text-sm text-slate-900">{intake?.location || "—"}</div>
                    <div className="mt-2 text-xs text-slate-500">
                      Attachments: {intake?.uploaded_files?.length ? intake.uploaded_files.join(", ") : "none"}
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">AI analysis</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {result?.confidence_note ?? "Running live model inference..."} • Always verify with a clinician
                    </div>
                  </div>
                  {meta && <Pill className={`${meta.pill} ${result?.urgency === "emergency" ? "animate-pulse-soft" : ""}`}>{meta.label} urgency</Pill>}
                </div>

                {!result && !error && intake && (
                  <div className="mt-5 space-y-2">
                    <div className="loading-shimmer h-4 w-40 rounded-lg" />
                    <div className="loading-shimmer h-4 w-full rounded-lg" />
                    <div className="loading-shimmer h-4 w-5/6 rounded-lg" />
                    <div className="pt-2">
                      <div className="mb-1 flex items-center justify-between text-[11px] font-semibold text-blue-700">
                        <span>Live confidence update</span>
                        <span>{Math.round(liveConfidence * 100)}%</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-blue-100">
                        <div className="h-2 rounded-full bg-blue-600 transition-all duration-300" style={{ width: `${Math.round(liveConfidence * 100)}%` }} />
                      </div>
                    </div>
                  </div>
                )}
                {error && <div className="mt-5 text-sm text-red-700">{error}</div>}

                {result && (
                  <div className="mt-5 grid gap-4 sm:grid-cols-2 animate-fade-up">
                    <div className="rounded-2xl border border-slate-200 p-4">
                      <div className="text-xs font-semibold text-slate-600">Possible condition</div>
                      <div className="mt-1 text-base font-bold text-slate-900">{result.possible_condition}</div>
                    </div>
                    <div className="rounded-2xl border border-slate-200 p-4">
                      <div className="text-xs font-semibold text-slate-600">Recommended department</div>
                      <div className="mt-1 text-base font-bold text-slate-900">{result.recommended_department}</div>
                    </div>
                    <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 sm:col-span-2">
                      <div className="text-xs font-semibold text-blue-700">Model inference</div>
                      <div className="mt-1 text-sm text-blue-900">
                        Powered by <span className="font-bold">{result.model_provider}</span> model <span className="font-bold">{result.model_name}</span>
                        {" "}with confidence <span className="font-bold">{Math.round(result.confidence_score * 100)}%</span>.
                      </div>
                    </div>
                    <div className="rounded-2xl border border-slate-200 p-4 sm:col-span-2">
                      <div className="text-xs font-semibold text-slate-600">Recommended next step</div>
                      <div className="mt-1 text-sm text-slate-900">{result.recommended_next_step}</div>
                    </div>
                    <div className="rounded-2xl border border-slate-200 p-4 sm:col-span-2">
                      <div className="text-xs font-semibold text-slate-600">Temporary precautions</div>
                      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-900">
                        {result.temporary_precautions.map((p, i) => (
                          <li key={i}>{p}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 sm:col-span-2">
                      <div className="text-xs font-semibold text-amber-900">Disclaimer</div>
                      <div className="mt-1 text-xs text-amber-900/90">{result.disclaimer}</div>
                    </div>
                  </div>
                )}
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <div className="text-sm font-semibold text-slate-900">Next actions</div>
                <div className="mt-4 grid gap-3">
                  <Link
                    href={`/hospitals?location=${encodeURIComponent(intake?.location ?? "")}`}
                    className="rounded-2xl border border-slate-200 bg-white p-4 hover:bg-slate-50"
                  >
                    <div className="text-sm font-bold text-slate-900">Find nearby hospitals</div>
                    <div className="mt-1 text-xs text-slate-500">Compare best-rated, closest, fastest route</div>
                  </Link>
                  <Link
                    href="/book"
                    className="rounded-2xl border border-slate-200 bg-white p-4 hover:bg-slate-50"
                  >
                    <div className="text-sm font-bold text-slate-900">Book an appointment</div>
                    <div className="mt-1 text-xs text-slate-500">Choose doctor + time slot</div>
                  </Link>
                </div>
              </Card>

              <Card>
                <div className="text-sm font-semibold text-slate-900">If this feels urgent</div>
                <p className="mt-2 text-sm text-slate-600">
                  Use the SOS button to simulate ambulance dispatch with ETA and nearest hospital.
                </p>
                <div className="mt-4">
                  <Button variant="danger" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
                    Safety reminder
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </Container>
      </main>
      <SOSButton />
    </div>
  );
}

