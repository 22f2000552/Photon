/* Compact shadcn-style primitives: Card, Badge, Button, Textarea, Skeleton, ScoreBar */
import { clsx } from "clsx";
import type { ButtonHTMLAttributes, HTMLAttributes, TextareaHTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx("rounded-xl border border-zinc-200 bg-white shadow-sm", className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("border-b border-zinc-100 px-5 py-4", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={clsx("text-sm font-semibold text-zinc-900", className)} {...props} />;
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("px-5 py-4", className)} {...props} />;
}

const badgeVariants: Record<string, string> = {
  default: "bg-zinc-100 text-zinc-700 border-zinc-200",
  success: "bg-emerald-50 text-emerald-700 border-emerald-200",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  danger: "bg-red-50 text-red-700 border-red-200",
  info: "bg-blue-50 text-blue-700 border-blue-200",
  violet: "bg-violet-50 text-violet-700 border-violet-200",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof badgeVariants }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
        badgeVariants[variant],
        className
      )}
      {...props}
    />
  );
}

const buttonVariants: Record<string, string> = {
  primary: "bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-emerald-300",
  secondary: "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 disabled:opacity-50",
  ghost: "text-zinc-600 hover:bg-zinc-100 disabled:opacity-50",
};

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: keyof typeof buttonVariants }) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed",
        buttonVariants[variant],
        className
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={clsx(
        "w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm placeholder:text-zinc-400",
        "focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100",
        className
      )}
      {...props}
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("animate-pulse rounded-md bg-zinc-200", className)} />;
}

export function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const v = value ?? 0;
  const color = v >= 75 ? "bg-emerald-500" : v >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 shrink-0 text-zinc-500">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-100">
        <div className={clsx("h-full rounded-full", color)} style={{ width: `${v}%` }} />
      </div>
      <span className="w-8 text-right font-medium tabular-nums text-zinc-700">{v.toFixed(0)}</span>
    </div>
  );
}

export function StatusChip({ status }: { status: string }) {
  const map: Record<string, { variant: keyof typeof badgeVariants; label: string }> = {
    draft: { variant: "default", label: "Draft" },
    scouting: { variant: "info", label: "Scouting" },
    outreach: { variant: "warning", label: "Outreach sent" },
    collecting: { variant: "violet", label: "Collecting quotes" },
    analyzed: { variant: "success", label: "Shortlist ready" },
  };
  const entry = map[status] ?? { variant: "default" as const, label: status };
  return <Badge variant={entry.variant}>{entry.label}</Badge>;
}

export function ChannelIconLabel({ channel }: { channel: string }) {
  const labels: Record<string, string> = {
    whatsapp: "WhatsApp",
    email: "Email",
    phone: "Phone",
    call_note: "Call note",
    upload: "File upload",
    manual: "Manual entry",
  };
  return <span>{labels[channel] ?? channel}</span>;
}