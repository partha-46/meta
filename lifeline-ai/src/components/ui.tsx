import Link from "next/link";
import { ReactNode } from "react";

export function Container({ children }: { children: ReactNode }) {
  return <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8">{children}</div>;
}

export function Card({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-3xl border border-slate-200/90 bg-white shadow-[0_8px_30px_rgba(2,6,23,0.06)] transition hover:shadow-[0_12px_36px_rgba(2,6,23,0.09)]">
      <div className="p-5 sm:p-6 md:p-7">{children}</div>
    </div>
  );
}

export function Button({
  children,
  onClick,
  type = "button",
  variant = "primary",
  disabled,
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
}) {
  const base =
    "inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed";
  const styles =
    variant === "danger"
      ? "bg-red-600 text-white shadow-md shadow-red-600/25 hover:-translate-y-0.5 hover:bg-red-700"
      : variant === "secondary"
        ? "bg-white text-slate-900 border border-slate-200 hover:-translate-y-0.5 hover:bg-slate-50"
        : "bg-blue-600 text-white shadow-md shadow-blue-600/20 hover:-translate-y-0.5 hover:bg-blue-700";
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${styles}`}>
      {children}
    </button>
  );
}

export function Pill({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${className}`}>
      {children}
    </span>
  );
}

export function TopNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/85 backdrop-blur">
      <Container>
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 text-white font-black shadow-md shadow-blue-600/25">
              LL
            </div>
            <div className="leading-tight">
              <div className="text-sm font-extrabold tracking-tight text-slate-900">LifeLine AI</div>
              <div className="text-xs text-slate-500">Emergency assistance MVP</div>
            </div>
          </Link>
          <nav className="flex items-center gap-2 text-sm">
            <Link className="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900" href="/hospitals">
              Hospitals
            </Link>
            <Link className="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900" href="/book">
              Book
            </Link>
          </nav>
        </div>
      </Container>
    </header>
  );
}

