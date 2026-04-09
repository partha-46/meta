"use client";

import { useEffect, useMemo, useState } from "react";
import { Button, Card, Container, Pill, TopNav } from "@/components/ui";
import { Appointment, createAppointment, getHospitals, Hospital } from "@/lib/api";
import { SOSButton } from "@/components/SOSButton";

const DOCTORS: Record<string, string[]> = {
  Cardiology: ["Dr. Meera Iyer", "Dr. Rahul Menon", "Dr. Sana Patel"],
  Emergency: ["Dr. Arjun Rao", "Dr. Kavya Nair"],
  "General Medicine": ["Dr. Neha Singh", "Dr. Vikram Das"],
  ENT: ["Dr. Ananya Shah"],
};

function timeSlots() {
  return [
    "Today 10:30 AM",
    "Today 12:00 PM",
    "Today 4:30 PM",
    "Tomorrow 9:30 AM",
    "Tomorrow 2:00 PM",
  ];
}

export default function BookPage() {
  const [location, setLocation] = useState("Downtown");
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [hospitalId, setHospitalId] = useState<string>("");
  const [department, setDepartment] = useState<string>("General Medicine");
  const [doctor, setDoctor] = useState<string>("");
  const [timeSlot, setTimeSlot] = useState<string>(timeSlots()[0]);
  const [patientName, setPatientName] = useState<string>("");
  const [patientPhone, setPatientPhone] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [confirmation, setConfirmation] = useState<Appointment | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHospitals(location, "closest").then((r) => {
      if (cancelled) return;
      setHospitals(r.hospitals);
      setHospitalId((prev) => prev || r.hospitals[0]?.id || "");
    });
    return () => {
      cancelled = true;
    };
  }, [location]);

  useEffect(() => {
    const list = DOCTORS[department] ?? ["Dr. Available Clinician"];
    setDoctor(list[0]);
  }, [department]);

  const selectedHospital = useMemo(() => hospitals.find((h) => h.id === hospitalId) ?? null, [hospitals, hospitalId]);
  const departments = useMemo(() => Object.keys(DOCTORS), []);
  const doctors = useMemo(() => DOCTORS[department] ?? [], [department]);

  const canBook =
    hospitalId &&
    department &&
    doctor &&
    timeSlot &&
    patientName.trim().length >= 2 &&
    patientPhone.trim().length >= 6 &&
    !busy;

  async function book() {
    if (!canBook) return;
    setBusy(true);
    try {
      const res = await createAppointment({
        hospital_id: hospitalId,
        department,
        doctor,
        time_slot: timeSlot,
        patient_name: patientName.trim(),
        patient_phone: patientPhone.trim(),
      });
      setConfirmation(res.appointment);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-full bg-gradient-to-b from-white to-slate-50">
      <TopNav />
      <main className="py-10 sm:py-14">
        <Container>
          <div>
            <Pill className="bg-blue-50 text-blue-700">Appointment booking</Pill>
            <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">Book a visit</h1>
            <p className="mt-2 text-slate-600">Select hospital, department, doctor, and a time slot. Demo uses mock availability.</p>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Location</div>
                    <input
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                    />
                    <div className="mt-2 text-xs text-slate-500">Tip: try Downtown / Westside / Northside</div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Hospital</div>
                    <select
                      value={hospitalId}
                      onChange={(e) => setHospitalId(e.target.value)}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                    >
                      {hospitals.map((h) => (
                        <option key={h.id} value={h.id}>
                          {h.name} • {h.eta_minutes} min
                        </option>
                      ))}
                    </select>
                    {selectedHospital && (
                      <div className="mt-2 text-xs text-slate-500">{selectedHospital.address}</div>
                    )}
                  </div>

                  <div>
                    <div className="text-sm font-semibold text-slate-900">Department</div>
                    <select
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                    >
                      {departments.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Doctor</div>
                    <select
                      value={doctor}
                      onChange={(e) => setDoctor(e.target.value)}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                    >
                      {doctors.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                    <div className="mt-2 text-xs font-semibold text-emerald-700">Specialist verified</div>
                  </div>

                  <div className="sm:col-span-2">
                    <div className="text-sm font-semibold text-slate-900">Time slot</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {timeSlots().map((t) => (
                        <button
                          key={t}
                          onClick={() => setTimeSlot(t)}
                          className={`rounded-xl border px-3 py-2 text-sm font-semibold ${
                            timeSlot === t
                              ? "border-blue-200 bg-blue-600 text-white"
                              : "border-slate-200 bg-white text-slate-800 hover:bg-slate-50"
                          }`}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="text-sm font-semibold text-slate-900">Patient details</div>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div>
                    <div className="text-xs font-semibold text-slate-600">Full name</div>
                    <input
                      value={patientName}
                      onChange={(e) => setPatientName(e.target.value)}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                      placeholder="Your name"
                    />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-600">Phone</div>
                    <input
                      value={patientPhone}
                      onChange={(e) => setPatientPhone(e.target.value)}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                      placeholder="+1 555 0123"
                    />
                  </div>
                </div>
                <div className="mt-5 flex justify-end">
                  <Button onClick={book} disabled={!canBook}>
                    {busy ? "Booking..." : "Confirm appointment"}
                  </Button>
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <div className="text-sm font-semibold text-slate-900">Reminder</div>
                <p className="mt-2 text-sm text-slate-600">
                  If symptoms are severe (chest pain, breathing trouble, unresponsive), use SOS instead of booking.
                </p>
                <div className="mt-4">
                  <Button variant="danger" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
                    Emergency guidance
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </Container>
      </main>

      {confirmation && (
        <div className="fixed inset-0 z-50 grid place-items-end bg-slate-900/50 p-4 sm:place-items-center">
          <div className="w-full max-w-md animate-fade-up">
            <Card>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-lg font-extrabold text-slate-900">Appointment confirmed</div>
                  <div className="mt-1 text-sm text-slate-600">Confirmation ID: {confirmation.id}</div>
                </div>
                <button
                  className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                  onClick={() => setConfirmation(null)}
                >
                  Close
                </button>
              </div>
              <div className="mt-5 space-y-2 text-sm text-slate-800">
                <div>
                  <span className="font-semibold">Hospital:</span> {confirmation.hospital_name}
                </div>
                <div>
                  <span className="font-semibold">Department:</span> {confirmation.department}
                </div>
                <div>
                  <span className="font-semibold">Doctor:</span> {confirmation.doctor}
                </div>
                <div>
                  <span className="font-semibold">Time:</span> {confirmation.time_slot}
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <Button onClick={() => setConfirmation(null)}>Done</Button>
              </div>
            </Card>
          </div>
        </div>
      )}

      <SOSButton />
    </div>
  );
}

