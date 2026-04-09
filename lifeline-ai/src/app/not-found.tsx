import Link from "next/link";
import { Container, TopNav } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="min-h-full bg-gradient-to-b from-white to-slate-50">
      <TopNav />
      <main className="py-16">
        <Container>
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <div className="text-2xl font-extrabold text-slate-900">Page not found</div>
            <p className="mt-2 text-slate-600">Return to symptom input to continue the demo.</p>
            <Link
              href="/"
              className="mt-6 inline-flex rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              Go home
            </Link>
          </div>
        </Container>
      </main>
    </div>
  );
}

