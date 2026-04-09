"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getHospitals, Hospital } from "@/lib/api";
import { Button, Card, Container, Pill, TopNav } from "@/components/ui";
import { SOSButton } from "@/components/SOSButton";

function Stars({ rating }: { rating: number }) {
  const full = Math.round(rating);
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 5 }).map((_, i) => (
        <span key={i} className={i < full ? "text-amber-500" : "text-slate-200"}>
          ★
        </span>
      ))}
      <span className="ml-2 text-xs font-semibold text-slate-600">{rating.toFixed(1)}</span>
    </div>
  );
}

function AvailabilityPill({ v }: { v: Hospital["availability"] }) {
  if (v === "busy") return <Pill className="bg-orange-500 text-white">Busy</Pill>;
  if (v === "limited") return <Pill className="bg-blue-600 text-white">Limited</Pill>;
  return <Pill className="bg-emerald-600 text-white">Open</Pill>;
}

export default function HospitalsPage() {
  const sp = useSearchParams();
  const initialLocation = sp.get("location") || "Downtown";

  const [location, setLocation] = useState(initialLocation);
  const [sort, setSort] = useState<"best_rated" | "closest" | "fastest_route">("closest");
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [geo, setGeo] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHospitals(location, sort, geo?.lat ?? null, geo?.lng ?? null)
      .then((r) => {
        if (cancelled) return;
        setHospitals(r.hospitals);
      })
      .catch(() => {
        if (cancelled) return;
        setHospitals([]);
      });
    return () => {
      cancelled = true;
    };
  }, [location, sort, geo]);

  function enableGeolocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((p) => {
      const lat = p.coords.latitude;
      const lng = p.coords.longitude;
      setGeo({ lat, lng });
      // Update textual location for visibility
      setLocation(`${lat.toFixed(4)},${lng.toFixed(4)}`);
      // Immediately fetch hospitals for this location
      getHospitals(`${lat.toFixed(4)},${lng.toFixed(4)}`, sort, lat, lng).then((r) => setHospitals(r.hospitals)).catch(() => {});
    });
  }

  const bounds = useMemo(() => {
    if (!hospitals.length) return null;
    const lats = hospitals.map((h) => h.lat);
    const lngs = hospitals.map((h) => h.lng);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    return { minLat, maxLat, minLng, maxLng };
  }, [hospitals]);

  return (
    <div className="min-h-full bg-gradient-to-b from-white to-slate-50">
      <TopNav />
      <main className="py-10 sm:py-14">
        <Container>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <Pill className="bg-blue-50 text-blue-700">Nearby hospital finder</Pill>
              <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">Hospitals near you</h1>
              <p className="mt-2 text-slate-600">
                Compare <span className="font-semibold">best rated</span>, <span className="font-semibold">closest</span>, or{" "}
                <span className="font-semibold">fastest route</span>.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="text-xs font-semibold text-slate-600">Location</div>
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  aria-label="Location"
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-600">Sort</div>
                <div className="mt-2 flex gap-2">
                  <Button variant={sort === "best_rated" ? "primary" : "secondary"} onClick={() => setSort("best_rated")}>
                    Best rated
                  </Button>
                  <Button variant={sort === "closest" ? "primary" : "secondary"} onClick={() => setSort("closest")}>
                    Closest
                  </Button>
                  <Button variant={sort === "fastest_route" ? "primary" : "secondary"} onClick={() => setSort("fastest_route")}>
                    Fastest
                  </Button>
                </div>
              </div>
            </div>
            <div className="sm:ml-auto">
              <Button variant="secondary" onClick={enableGeolocation}>
                Use my location
              </Button>
            </div>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-4">
              {!hospitals.length && <div className="text-sm text-slate-600">Loading hospitals…</div>}
              {hospitals.map((h) => {
                const erWait = Math.max(8, Math.round(h.eta_minutes * 1.2 + (5 - h.rating) * 4));
                const doctorMins = Math.max(6, Math.round(h.eta_minutes * 0.65));
                const beds = h.availability === "open" ? "Beds: 12 available" : h.availability === "limited" ? "Beds: 4 available" : "Beds: 1 available";
                return (
                <Card key={h.id}>
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between group">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="text-lg font-extrabold text-slate-900">{h.name}</div>
                        <AvailabilityPill v={h.availability} />
                        <Pill className="bg-emerald-100 text-emerald-800">Verified hospital</Pill>
                      </div>
                      <Stars rating={h.rating} />
                      <div className="text-sm text-slate-600">{h.address}</div>
                      <div className="flex flex-wrap gap-2 text-xs">
                        <Pill className="bg-blue-50 text-blue-700">Doctor available in {doctorMins} mins</Pill>
                        <Pill className="bg-slate-100 text-slate-700">ER wait {erWait} mins</Pill>
                        <Pill className="bg-violet-100 text-violet-700">{beds}</Pill>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {h.specialties.slice(0, 5).map((s) => (
                          <Pill key={s} className="bg-slate-100 text-slate-700">
                            {s} • verified specialist
                          </Pill>
                        ))}
                      </div>
                    </div>
                    <div className="grid gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 transition group-hover:-translate-y-0.5">
                      <div className="text-xs font-semibold text-slate-600">Distance</div>
                      <div className="text-sm font-extrabold text-slate-900">{h.distance_km.toFixed(1)} km</div>
                      <div className="text-xs font-semibold text-slate-600">ETA</div>
                      <div className="text-sm font-extrabold text-slate-900">{h.eta_minutes} min</div>
                      {geo && (
                        <a
                          className="text-xs font-semibold text-blue-700 hover:underline"
                          target="_blank"
                          rel="noreferrer"
                          href={`https://www.google.com/maps/dir/?api=1&origin=${geo.lat},${geo.lng}&destination=${h.lat},${h.lng}&travelmode=driving`}
                        >
                          Open live route
                        </a>
                      )}
                      <a className="text-xs font-semibold text-blue-700 hover:underline" href={`tel:${h.phone}`}>
                        Call {h.phone}
                      </a>
                    </div>
                  </div>
                </Card>
              )})}
            </div>

            <div className="space-y-6">
              <Card>
                <div className="text-sm font-semibold text-slate-900">Map (demo)</div>
                <p className="mt-2 text-sm text-slate-600">
                  Demo map pins. In production, replace with Google Maps / Mapbox. Pins are plotted from mock hospital coordinates.
                </p>
                <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
                  <div className="relative h-[280px] w-full">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.18),transparent_35%),radial-gradient(circle_at_70%_70%,rgba(16,185,129,0.18),transparent_40%)]" />
                    <div className="absolute inset-0 p-4">
                      {bounds && hospitals.map((h) => {
                        const x = ((h.lng - bounds.minLng) / (bounds.maxLng - bounds.minLng || 1)) * 100;
                        const y = (1 - (h.lat - bounds.minLat) / (bounds.maxLat - bounds.minLat || 1)) * 100;
                        return (
                          <div
                            key={h.id}
                            className="absolute -translate-x-1/2 -translate-y-1/2"
                            style={{ left: `${x}%`, top: `${y}%` }}
                            title={h.name}
                          >
                            <div className="grid h-9 w-9 place-items-center rounded-full bg-blue-600 text-white shadow-md">
                              +
                            </div>
                          </div>
                        );
                      })}
                      <div className="absolute bottom-3 left-3 rounded-xl bg-white/90 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm">
                        {sort === "best_rated" ? "Best rated" : sort === "fastest_route" ? "Fastest route" : "Closest"}
                      </div>
                    </div>
                  </div>
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

