import { Suspense } from "react";
import HospitalsClient from "./HospitalsClient";

export const metadata = {
  title: "Hospitals Near You | LifeLine AI",
  description: "Find the best rated, closest, or fastest route to nearby hospitals.",
};

export default function HospitalsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-slate-600 text-sm">
          Loading hospitals…
        </div>
      }
    >
      <HospitalsClient />
    </Suspense>
  );
}
