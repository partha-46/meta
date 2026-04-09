"use client";

import { useMemo, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, Container, Pill, TopNav } from "@/components/ui";
import { uploadFiles } from "@/lib/api";
import { DEMO_CASES } from "@/lib/demo";

export default function Home() {
  const router = useRouter();
  const [symptoms, setSymptoms] = useState("");
  const [location, setLocation] = useState("");
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [toast, setToast] = useState<{ msg: string; kind: "info" | "error" } | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const canSubmit = symptoms.trim().length >= 3 && location.trim().length >= 2 && !busy;

  const fileNote = useMemo(() => {
    if (files.length === 0) return "Upload optional reports (PDF/images/prescriptions).";
    return `${files.length} file(s) selected. We'll attach filenames to your analysis.`;
  }, [files.length]);

  async function onSubmit() {
    if (!canSubmit) return;
    setBusy(true);
    try {
      let uploaded_files: string[] = [];
      if (files.length) {
        const up = await uploadFiles(files);
        uploaded_files = up.uploaded_files ?? [];
      }
      const payload = { symptoms: symptoms.trim(), location: location.trim(), uploaded_files };
      sessionStorage.setItem("lifeline:last_intake", JSON.stringify(payload));
      router.push("/results");
    } finally {
      setBusy(false);
    }
  }

  function enableGeolocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const lat = p.coords.latitude;
        const lng = p.coords.longitude;
        // store coords and show a quick toast while we reverse-geocode
        setCoords({ lat, lng });
        setToast({ msg: "Location detected — resolving address…", kind: "info" });
        reverseGeocodeAndSet(lat, lng);
      },
      (err) => {
        console.warn("geolocation error", err);
        setToast({ msg: "Could not get your location (permission denied or error).", kind: "error" });
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  useEffect(() => {
    // Auto-detect on page load (try to get permission silently)
    // Delay slightly to avoid immediate permission prompt in some browsers
    const t = setTimeout(() => {
      try {
        enableGeolocation();
      } catch (e) {
        // ignore
      }
    }, 600);
    return () => clearTimeout(t);
  }, []);

  async function reverseGeocodeAndSet(lat: number, lng: number) {
    try {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "";
  const url = `${apiBase}/reverse-geocode?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("geocode failed");
      const j = await res.json();
      const name = j.display_name || `${lat.toFixed(4)},${lng.toFixed(4)}`;
      setLocation(name);
      setToast({ msg: `Detected location: ${name}`, kind: "info" });
      // clear toast after a short delay
      setTimeout(() => setToast(null), 4500);
    } catch (e) {
      setLocation(`${lat.toFixed(4)},${lng.toFixed(4)}`);
      setToast({ msg: "Detected coordinates but failed to resolve address.", kind: "error" });
      setTimeout(() => setToast(null), 4500);
    }
  }

  function fillDemo(id: string) {
    const c = DEMO_CASES.find((d) => d.id === id);
    if (!c) return;
    setSymptoms(c.symptoms);
    setLocation(c.location);
  }

  return (
    <div className="min-h-full bg-gradient-to-b from-white to-slate-50">
      <TopNav />
      {/* Simple toast */}
      {toast && (
        <div className={`fixed left-1/2 top-20 -translate-x-1/2 z-50 rounded-xl px-4 py-3 shadow-md ${
          toast.kind === "error" ? "bg-red-600 text-white" : "bg-blue-600 text-white"
        }`} role="status">
          {toast.msg}
        </div>
      )}
      <main className="py-10 sm:py-14">
        <Container>
          <div className="grid gap-8 lg:grid-cols-2 lg:items-start">
            <div className="space-y-5">
              <Pill className="bg-blue-50 text-blue-700">Not a diagnosis • Demo-ready triage</Pill>
              <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
                Get urgent guidance and the best next step—fast.
              </h1>
              <p className="text-slate-600 leading-7">
                LifeLine AI helps you understand symptom urgency, find nearby hospitals, book an appointment, or request
                emergency help. It always uses <span className="font-semibold">possible / likely</span> wording—never a final diagnosis.
              </p>

              <div className="grid gap-3 sm:grid-cols-3">
                {DEMO_CASES.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => fillDemo(d.id)}
                    className="rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"
                  >
                    <div className="text-sm font-semibold text-slate-900">{d.title}</div>
                    <div className="mt-1 text-xs text-slate-500">Autofill demo</div>
                  </button>
                ))}
              </div>
            </div>

            <Card>
              <div className="space-y-4">
                <div>
                  <div className="text-sm font-semibold text-slate-900">Describe symptoms</div>
                  <textarea
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    placeholder="I have chest pain and shortness of breath"
                    className="mt-2 min-h-[120px] w-full resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Location</div>
                      <div className="mt-2 flex items-center gap-2">
                        <input
                          value={location}
                          onChange={(e) => setLocation(e.target.value)}
                          placeholder="Downtown / Westside / Northside"
                          className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                        />
                        <Button variant="secondary" onClick={enableGeolocation}>
                          Use my location
                        </Button>
                      </div>
                      {coords && (
                        <div className="mt-2 flex items-center gap-2">
                          <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                            <div className="font-semibold">Detected</div>
                            <div className="text-xs">{location}</div>
                            <div className="text-xs text-slate-500">{coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}</div>
                          </div>
                          <Button variant="secondary" onClick={() => { setCoords(null); setLocation(""); }}>
                            Clear
                          </Button>
                        </div>
                      )}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Upload reports (optional)</div>
                    <input
                      type="file"
                      multiple
                      accept="application/pdf,image/*"
                      aria-label="Upload reports"
                      onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                      className="mt-2 block w-full text-sm file:mr-3 file:rounded-xl file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-slate-900 hover:file:bg-slate-200"
                    />
                    <div className="mt-2 text-xs text-slate-500">{fileNote}</div>
                    <div className="mt-1 text-[11px] font-semibold text-emerald-700">Secure upload indicator: encrypted in transit (demo)</div>
                  </div>
                </div>

                <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
                  <div className="font-semibold">Safety note</div>
                  <div className="mt-1 text-blue-800/90">
                    If you suspect a life-threatening emergency, use the SOS button for immediate ambulance dispatch simulation.
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs text-slate-500">
                    By continuing, you agree this is informational only.
                  </div>
                  <Button onClick={onSubmit} disabled={!canSubmit}>
                    {busy ? "Analyzing..." : "Submit"}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </Container>
      </main>
    </div>
  );
}
