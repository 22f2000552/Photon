import { AlertTriangle, Trophy } from "lucide-react";
import { clsx } from "clsx";
import type { ShortlistEntry } from "@/lib/types";
import { Card, CardContent, ScoreBar } from "@/components/ui";

const RANK_STYLES = [
  "border-emerald-300 bg-gradient-to-b from-emerald-50 to-white ring-1 ring-emerald-200",
  "border-zinc-200 bg-white",
  "border-zinc-200 bg-white",
];

export function Shortlist({ shortlist, explanation }: { shortlist: ShortlistEntry[]; explanation: string }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {shortlist.map((s, i) => (
          <Card key={s.vendor_id} className={clsx("relative", RANK_STYLES[i] ?? RANK_STYLES[2])}>
            <CardContent className="pt-5">
              <div className="mb-2 flex items-center justify-between">
                <span
                  className={clsx(
                    "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold",
                    i === 0 ? "bg-emerald-600 text-white" : "bg-zinc-100 text-zinc-600"
                  )}
                >
                  {s.rank}
                </span>
                {i === 0 && (
                  <span className="flex items-center gap-1 text-xs font-medium text-emerald-700">
                    <Trophy className="h-3.5 w-3.5" /> Recommended
                  </span>
                )}
              </div>
              <div className="text-base font-semibold">{s.vendor_name}</div>
              <div className="text-xs text-zinc-500">{s.city}</div>
              <div className="mt-2 text-2xl font-bold tabular-nums text-zinc-900">
                {s.normalized_price != null ? `₹${s.normalized_price.toLocaleString("en-IN")}` : "—"}
                <span className="ml-1 text-xs font-normal text-zinc-400">{s.normalized_basis}</span>
              </div>
              <div className="mt-3 space-y-1.5">
                <ScoreBar label="Price" value={s.scores.price} />
                <ScoreBar label="Delivery" value={s.scores.delivery} />
                <ScoreBar label="Docs" value={s.scores.docs} />
                <ScoreBar label="Reliability" value={s.scores.reliability} />
              </div>
              <ul className="mt-3 space-y-1 text-xs text-zinc-600">
                {s.reasons.slice(0, 3).map((r, j) => (
                  <li key={j}>• {r}</li>
                ))}
              </ul>
              {s.risks.length > 0 && (
                <div className="mt-2 flex items-start gap-1.5 rounded-md bg-amber-50 px-2.5 py-1.5 text-xs text-amber-700">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>{s.risks.join("; ")}</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      {explanation && (
        <Card>
          <CardContent className="py-4">
            <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-400">
              Analyst’s reasoning
            </h4>
            <p className="text-sm leading-relaxed text-zinc-700">{explanation}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
