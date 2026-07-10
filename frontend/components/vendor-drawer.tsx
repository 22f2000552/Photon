"use client";

import { useEffect, useState } from "react";
import { Award, Clock, Ghost, Mail, MessageCircle, Phone, ThumbsDown, ThumbsUp, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Vendor } from "@/lib/types";
import { Badge, ScoreBar, Skeleton } from "@/components/ui";

const EVENT_META: Record<string, { icon: React.ReactNode; tone: string }> = {
  replied_fast: { icon: <Clock className="h-3.5 w-3.5" />, tone: "text-emerald-600" },
  replied_slow: { icon: <Clock className="h-3.5 w-3.5" />, tone: "text-amber-600" },
  ghosted: { icon: <Ghost className="h-3.5 w-3.5" />, tone: "text-red-600" },
  on_time_delivery: { icon: <ThumbsUp className="h-3.5 w-3.5" />, tone: "text-emerald-600" },
  late_delivery: { icon: <ThumbsDown className="h-3.5 w-3.5" />, tone: "text-red-600" },
  cert_verified: { icon: <Award className="h-3.5 w-3.5" />, tone: "text-emerald-600" },
  cert_issue: { icon: <Award className="h-3.5 w-3.5" />, tone: "text-red-600" },
  clear_commitment: { icon: <ThumbsUp className="h-3.5 w-3.5" />, tone: "text-emerald-600" },
  evasive_answer: { icon: <ThumbsDown className="h-3.5 w-3.5" />, tone: "text-amber-600" },
};

const CHANNEL_ICON: Record<string, React.ReactNode> = {
  whatsapp: <MessageCircle className="h-3.5 w-3.5 text-emerald-600" />,
  email: <Mail className="h-3.5 w-3.5 text-blue-600" />,
  phone: <Phone className="h-3.5 w-3.5 text-zinc-500" />,
};

export function VendorDrawer({ vendorId, onClose }: { vendorId: number | null; onClose: () => void }) {
  const [vendor, setVendor] = useState<Vendor | null>(null);

  useEffect(() => {
    setVendor(null);
    if (vendorId != null) {
      api.getVendor(vendorId).then(setVendor).catch(() => {});
    }
  }, [vendorId]);

  if (vendorId == null) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <aside className="absolute right-0 top-0 h-full w-full max-w-md overflow-y-auto bg-white shadow-2xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-zinc-100 bg-white px-5 py-4">
          <h3 className="text-sm font-semibold">Vendor profile</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-zinc-100">
            <X className="h-4 w-4" />
          </button>
        </div>

        {vendor === null ? (
          <div className="space-y-3 p-5">
            <Skeleton className="h-6 w-2/3" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : (
          <div className="space-y-5 p-5">
            <div>
              <div className="text-lg font-semibold">{vendor.name}</div>
              <div className="text-sm text-zinc-500">
                {vendor.city}, {vendor.state}
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {vendor.categories.map((c) => (
                  <Badge key={c}>{c}</Badge>
                ))}
                {vendor.gst_number ? (
                  <Badge variant="info">GST {vendor.gst_number}</Badge>
                ) : (
                  <Badge variant="warning">GST missing</Badge>
                )}
              </div>
              {vendor.notes && <p className="mt-2 text-xs text-zinc-500">{vendor.notes}</p>}
            </div>

            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">Contacts</h4>
              <ul className="space-y-1.5">
                {vendor.contacts.map((c) => (
                  <li key={c.id} className="flex items-center gap-2 text-sm">
                    {CHANNEL_ICON[c.channel] ?? <Phone className="h-3.5 w-3.5" />}
                    <span>{c.value}</span>
                    {c.is_preferred && <Badge variant="success">preferred</Badge>}
                  </li>
                ))}
                {vendor.contacts.length === 0 && (
                  <li className="text-sm text-zinc-400">No contacts on file</li>
                )}
              </ul>
            </div>

            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">Certificates</h4>
              <ul className="space-y-1.5">
                {vendor.certificates.map((c) => (
                  <li key={c.id} className="flex items-center gap-2 text-sm">
                    <Award className="h-3.5 w-3.5 text-zinc-400" />
                    <span>
                      {c.cert_type} {c.number || "(no number)"}
                    </span>
                    <Badge variant={c.status === "valid" ? "success" : "danger"}>{c.status}</Badge>
                  </li>
                ))}
                {vendor.certificates.length === 0 && (
                  <li className="text-sm text-zinc-400">No certificates on file</li>
                )}
              </ul>
            </div>

            {vendor.memory && (
              <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-4">
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
                  Vendor memory
                </h4>
                <ScoreBar label="Reliability" value={vendor.memory.reliability_score} />
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-zinc-600">
                  <div>Past RFQs: {vendor.memory.rfq_count}</div>
                  <div>
                    Avg response:{" "}
                    {vendor.memory.avg_response_hours != null
                      ? `${vendor.memory.avg_response_hours}h`
                      : "—"}
                  </div>
                  <div>Ghosted: {vendor.memory.ghost_count}x</div>
                </div>
              </div>
            )}

            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
                Reliability timeline
              </h4>
              <ul className="space-y-2.5 border-l border-zinc-200 pl-4">
                {(vendor.events ?? []).map((e) => {
                  const meta = EVENT_META[e.event_type] ?? {
                    icon: <Clock className="h-3.5 w-3.5" />,
                    tone: "text-zinc-500",
                  };
                  return (
                    <li key={e.id} className="relative text-sm">
                      <span className={`absolute -left-[22px] top-0.5 ${meta.tone}`}>{meta.icon}</span>
                      <span className="font-medium">{e.event_type.replaceAll("_", " ")}</span>
                      <span
                        className={`ml-1.5 text-xs ${e.impact >= 0 ? "text-emerald-600" : "text-red-600"}`}
                      >
                        {e.impact >= 0 ? "+" : ""}
                        {e.impact}
                      </span>
                      {e.detail && <div className="text-xs text-zinc-500">{e.detail}</div>}
                      <div className="text-[10px] text-zinc-400">
                        {new Date(e.created_at).toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </div>
                    </li>
                  );
                })}
                {(vendor.events ?? []).length === 0 && (
                  <li className="text-sm text-zinc-400">No history yet — memory builds with each RFQ.</li>
                )}
              </ul>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}