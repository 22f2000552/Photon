"use client";

import { useState } from "react";
import { ArrowDownLeft, ArrowUpRight, Loader2, MessageSquarePlus, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { RFQMessage, Vendor } from "@/lib/types";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, ChannelIconLabel, Textarea } from "@/components/ui";

export function OutreachTracker({
  rfqId,
  messages,
  vendors,
  hasQuotes,
  onChanged,
  onVendorClick,
}: {
  rfqId: number;
  messages: RFQMessage[];
  vendors: Vendor[];
  hasQuotes: boolean;
  onChanged: () => void;
  onVendorClick: (id: number) => void;
}) {
  const [showReply, setShowReply] = useState(false);
  const [vendorId, setVendorId] = useState<number>(vendors[0]?.id ?? 0);
  const [channel, setChannel] = useState("whatsapp");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState<"simulate" | "reply" | null>(null);
  const vendorName = (id: number) => vendors.find((v) => v.id === id)?.name ?? `Vendor ${id}`;

  async function simulate() {
    setBusy("simulate");
    try {
      await api.simulateReplies(rfqId);
      onChanged();
    } finally {
      setBusy(null);
    }
  }

  async function submitReply() {
    if (!text.trim() || !vendorId) return;
    setBusy("reply");
    try {
      await api.addReply(rfqId, vendorId, channel, text.trim());
      setText("");
      setShowReply(false);
      onChanged();
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Outreach tracker</CardTitle>
        <div className="flex items-center gap-2">
          <Button variant="secondary" className="px-2.5 py-1.5 text-xs" onClick={() => setShowReply((s) => !s)}>
            <MessageSquarePlus className="h-3.5 w-3.5" /> Log a reply
          </Button>
          {!hasQuotes && (
            <Button className="px-2.5 py-1.5 text-xs" onClick={simulate} disabled={busy !== null}>
              {busy === "simulate" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
              Simulate vendor replies
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {showReply && (
          <div className="mb-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3">
            <div className="mb-2 flex flex-wrap gap-2">
              <select
                className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm"
                value={vendorId}
                onChange={(e) => setVendorId(Number(e.target.value))}
              >
                {vendors.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
              <select
                className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-sm"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
              >
                <option value="whatsapp">WhatsApp</option>
                <option value="email">Email</option>
                <option value="call_note">Call note</option>
                <option value="manual">Manual entry</option>
              </select>
            </div>
            <Textarea
              rows={2}
              placeholder='e.g. "372 per bag delivered, GST extra, 5 days"'
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <Button className="mt-2 px-3 py-1.5 text-xs" onClick={submitReply} disabled={busy !== null || !text.trim()}>
              {busy === "reply" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              Ingest & parse reply
            </Button>
          </div>
        )}

        {messages.length === 0 ? (
          <p className="text-sm text-zinc-500">No messages yet — run outreach first.</p>
        ) : (
          <ul className="space-y-2.5">
            {messages.map((m) => (
              <li key={m.id} className="flex items-start gap-2.5">
                {m.direction === "outbound" ? (
                  <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
                ) : (
                  <ArrowDownLeft className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5 text-xs">
                    <button
                      className="font-medium text-zinc-800 hover:underline"
                      onClick={() => onVendorClick(m.vendor_id)}
                    >
                      {vendorName(m.vendor_id)}
                    </button>
                    <Badge variant={m.direction === "outbound" ? "info" : "success"}>
                      {m.direction === "outbound" ? "sent via" : "replied via"}{" "}
                      <ChannelIconLabel channel={m.channel} />
                    </Badge>
                    {m.status === "needs_clarification" && (
                      <Badge variant="warning">needs clarification</Badge>
                    )}
                    <span className="text-zinc-400">
                      {new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                  <p className="mt-0.5 line-clamp-2 whitespace-pre-line text-sm text-zinc-600">{m.body}</p>
                  {m.status === "needs_clarification" && Array.isArray(m.meta?.clarify) && (
                    <p className="mt-0.5 text-xs text-amber-600">
                      Follow-up needed: {(m.meta.clarify as string[]).join("; ")}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
