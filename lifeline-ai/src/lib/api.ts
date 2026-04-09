export type Urgency = "low" | "medium" | "high" | "emergency";

export type AnalyzeResult = {
  possible_condition: string;
  urgency: Urgency;
  recommended_department: string;
  temporary_precautions: string[];
  recommended_next_step: string;
  disclaimer: string;
  confidence_note: string;
  confidence_score: number;
  model_provider: string;
  model_name: string;
};

export type Hospital = {
  id: string;
  name: string;
  distance_km: number;
  eta_minutes: number;
  rating: number;
  specialties: string[];
  availability: "open" | "limited" | "busy";
  address: string;
  phone: string;
  lat: number;
  lng: number;
};

export type HospitalsResponse = {
  location: string;
  sort: "best_rated" | "closest" | "fastest_route";
  hospitals: Hospital[];
};

export type AppointmentRequest = {
  hospital_id: string;
  department: string;
  doctor: string;
  time_slot: string;
  patient_name: string;
  patient_phone: string;
};

export type Appointment = {
  id: string;
  hospital_id: string;
  hospital_name: string;
  department: string;
  doctor: string;
  time_slot: string;
  patient_name: string;
  patient_phone: string;
  status: "confirmed" | "cancelled";
  created_at_iso: string;
};

export type SosResponse = {
  status: "ambulance_dispatched";
  nearest_hospital: Hospital;
  eta_seconds: number;
  tracking_code: string;
  message: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function uploadFiles(files: File[]) {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Upload failed (${res.status})`);
  return (await res.json()) as { uploaded_files: string[] };
}

export async function analyze(payload: {
  symptoms: string;
  location: string;
  uploaded_files: string[];
}) {
  const fd = new FormData();
  fd.set("symptoms", payload.symptoms);
  fd.set("location", payload.location);
  fd.set("uploaded_files", JSON.stringify(payload.uploaded_files ?? []));
  const res = await fetch(`${API_BASE}/analyze`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Analyze failed (${res.status})`);
  return (await res.json()) as AnalyzeResult;
}

export async function getHospitals(
  location: string,
  sort: HospitalsResponse["sort"],
  lat?: number | null,
  lng?: number | null
) {
  const url = new URL(`${API_BASE}/hospitals`);
  url.searchParams.set("location", location);
  url.searchParams.set("sort", sort);
  if (typeof lat === "number" && typeof lng === "number") {
    url.searchParams.set("lat", String(lat));
    url.searchParams.set("lng", String(lng));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Hospitals failed (${res.status})`);
  return (await res.json()) as HospitalsResponse;
}

export async function createAppointment(req: AppointmentRequest) {
  const res = await fetch(`${API_BASE}/appointments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Appointment failed (${res.status})`);
  return (await res.json()) as { appointment: Appointment };
}

export async function sos(location: string, symptoms?: string) {
  const res = await fetch(`${API_BASE}/sos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location, symptoms }),
  });
  if (!res.ok) throw new Error(`SOS failed (${res.status})`);
  return (await res.json()) as SosResponse;
}

