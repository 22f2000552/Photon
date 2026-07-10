"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { RFQSummary } from "@/lib/types";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton, StatusChip, Textarea } from "@/components/ui";

const EXAMPLE =
  "Need 500 bags of OPC 53 cement in Prayagraj by 15 August, budget ₹390 per bag delivered, BIS certificate mandatory";

export default function Dashboard() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [rfqs, setRfqs] = useState<RFQSummary[] | null>(null);
  const [llmMode, setLlmMode] = useState("");

  const load = useCallback(async () => {
    try {
      const [list, health] = await Promise.all([api.listRfqs(), api.health()]);
      setRfqs(list);
      setLlmMode(health.llm);
      setError("");
    } catch {
      setError("Backend not reachable at http://localhost:8000 — start it with `python run.py`.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function create() {
    if (!text.trim()) return;
    setCreating(true);
    setError("");
    try {
      const { rfq_id } = await api.createRequirement(text.trim());
      router.push(`/rfq/${rfq_id}`);
    } catch (e) {
      setError(String(e));
      setCreating(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50 to-white">
        <CardContent className="py-6">
          <div className="mb-1 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-emerald-600" />
            <h2 className="text-base font-semibold">What do you need to buy?</h2>
            {llmMode && (
              <Badge variant={llmMode.startsWith("groq") ? "success" : "info"}>{llmMode}</Badge>
            )}
          </div>
          <p className="mb-3 text-sm text-zinc-500">
            Describe your requirement in plain language. RFQ Copilot will parse it, scout your
            vendor pool, and reach out on the right channel — WhatsApp, email, or a call note.
          </p>
          <Textarea
            rows={3}
            value={text}
            placeholder={EXAMPLE}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="mt-3 flex items-center gap-3">
            <Button onClick={create} disabled={creating || !text.trim()}>
              {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              {creating ? "Scouting vendors…" : "Start RFQ"}
            </Button>
            <button
              className="text-xs text-emerald-700 underline-offset-2 hover:underline"
              onClick={() => setText(EXAMPLE)}
            >
              Use example
            </button>
          </div>
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Your RFQs</CardTitle>
          <span className="text-xs text-zinc-400">{rfqs?.length ?? "…"} total</span>
        </CardHeader>
        <CardContent className="p-0">
          {rfqs === null ? (
            <div className="space-y-3 p-5">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          ) : rfqs.length === 0 ? (
            <p className="p-5 text-sm text-zinc-500">
              No RFQs yet — type a requirement above to start your first one.
            </p>
          ) : (
            <ul className="divide-y divide-zinc-100">
              {rfqs.map((rfq) => (
                <li
                  key={rfq.id}
                  className="flex cursor-pointer items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-zinc-50"
                  onClick={() => router.push(`/rfq/${rfq.id}`)}
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">
                      {rfq.requirement.quantity
                        ? `${rfq.requirement.quantity} ${rfq.requirement.unit} ${rfq.requirement.grade || rfq.requirement.product}`
                        : rfq.requirement.raw_text}
                      {rfq.requirement.location && (
                        <span className="text-zinc-400"> · {rfq.requirement.location}</span>
                      )}
                    </div>
                    <div className="mt-0.5 text-xs text-zinc-400">
                      {rfq.contacted_count} vendors contacted · {rfq.quote_count} quotes ·{" "}
                      {new Date(rfq.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                    </div>
                  </div>
                  <StatusChip status={rfq.status} />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
