"use client";

import { Fragment, useState } from "react";
import { ChevronDown, ChevronUp, FileCheck2, FileX2 } from "lucide-react";
import type { Quote, Vendor } from "@/lib/types";
import { Badge, Card, CardContent, CardHeader, CardTitle, ScoreBar } from "@/components/ui";

function yesNo(v: boolean | null, yes: string, no: string) {
  if (v === null) return <Badge variant="warning">unknown</Badge>;
  return v ? <Badge variant="success">{yes}</Badge> : <Badge variant="danger">{no}</Badge>;
}

export function QuoteTable({
  quotes,
  vendors,
  onVendorClick,
}: {
  quotes: Quote[];
  vendors: Vendor[];
  onVendorClick: (id: number) => void;
}) {
  const [open, setOpen] = useState<number | null>(null);
  const vendorName = (id: number) => vendors.find((v) => v.id === id)?.name ?? `Vendor ${id}`;
  const sorted = [...quotes].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99));

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Leveled quote comparison</CardTitle>
        <span className="text-xs text-zinc-400">
          all prices normalized to {quotes[0]?.normalized_basis || "a common basis"}
        </span>
      </CardHeader>
      <CardContent className="overflow-x-auto p-0">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-zinc-100 text-left text-[11px] uppercase tracking-wide text-zinc-400">
              <th className="px-5 py-2.5 font-medium">Vendor</th>
              <th className="px-3 py-2.5 font-medium">As quoted</th>
              <th className="px-3 py-2.5 font-medium">Leveled price</th>
              <th className="px-3 py-2.5 font-medium">GST</th>
              <th className="px-3 py-2.5 font-medium">Freight</th>
              <th className="px-3 py-2.5 font-medium">Delivery</th>
              <th className="px-3 py-2.5 font-medium">Docs</th>
              <th className="px-3 py-2.5 font-medium">Score</th>
              <th className="px-3 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((q) => (
              <Fragment key={q.id}>
                <tr className="border-b border-zinc-50 hover:bg-zinc-50/60">
                  <td className="px-5 py-3">
                    <button
                      className="font-medium text-zinc-800 hover:underline"
                      onClick={() => onVendorClick(q.vendor_id)}
                    >
                      {q.rank ? `#${q.rank} ` : ""}
                      {vendorName(q.vendor_id)}
                    </button>
                    {q.flags.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {q.flags.slice(0, 2).map((f) => (
                          <Badge key={f} variant="warning">
                            {f}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3 text-zinc-600">
                    {q.price != null ? `₹${q.price.toLocaleString("en-IN")}` : "—"}
                    {q.unit_basis && <span className="text-xs text-zinc-400"> /{q.unit_basis}</span>}
                  </td>
                  <td className="px-3 py-3 font-semibold tabular-nums">
                    {q.normalized_price != null ? `₹${q.normalized_price.toLocaleString("en-IN")}` : "—"}
                  </td>
                  <td className="px-3 py-3">{yesNo(q.gst_included, "incl.", "extra")}</td>
                  <td className="px-3 py-3">{yesNo(q.freight_included, "incl.", "extra")}</td>
                  <td className="px-3 py-3 text-zinc-600">
                    {q.delivery_date
                      ? new Date(q.delivery_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })
                      : q.delivery_days != null
                        ? `${q.delivery_days} days`
                        : "—"}
                    {q.delivery_vague && <Badge variant="danger" className="ml-1">vague</Badge>}
                  </td>
                  <td className="px-3 py-3">
                    {q.cert_attached ? (
                      <FileCheck2 className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <FileX2 className="h-4 w-4 text-zinc-300" />
                    )}
                  </td>
                  <td className="px-3 py-3 font-semibold tabular-nums">
                    {q.overall_score != null ? q.overall_score.toFixed(0) : "—"}
                  </td>
                  <td className="px-3 py-3">
                    <button
                      className="rounded p-1 text-zinc-400 hover:bg-zinc-100"
                      onClick={() => setOpen(open === q.id ? null : q.id)}
                    >
                      {open === q.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </td>
                </tr>
                {open === q.id && (
                  <tr className="border-b border-zinc-100 bg-zinc-50/70">
                    <td colSpan={9} className="px-5 py-4">
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <h5 className="mb-1.5 text-xs font-semibold uppercase text-zinc-400">Raw reply</h5>
                          <p className="rounded-md bg-white px-3 py-2 text-sm italic text-zinc-600">
                            “{q.raw_text}”
                          </p>
                          <h5 className="mb-1.5 mt-3 text-xs font-semibold uppercase text-zinc-400">
                            Normalization steps
                          </h5>
                          <ul className="list-inside list-disc space-y-0.5 text-xs text-zinc-600">
                            {q.normalization_notes.map((n, i) => (
                              <li key={i}>{n}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h5 className="mb-1.5 text-xs font-semibold uppercase text-zinc-400">
                            Score breakdown & evidence
                          </h5>
                          <div className="space-y-1.5">
                            <ScoreBar label="Price" value={q.price_score} />
                            <ScoreBar label="Delivery" value={q.delivery_score} />
                            <ScoreBar label="Docs" value={q.doc_score} />
                            <ScoreBar label="Reliability" value={q.reliability_score} />
                          </div>
                          <ul className="mt-2 space-y-1 text-xs text-zinc-500">
                            {Object.entries(q.score_evidence).map(([k, v]) => (
                              <li key={k}>
                                <span className="font-medium text-zinc-600">{k}:</span> {v}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
