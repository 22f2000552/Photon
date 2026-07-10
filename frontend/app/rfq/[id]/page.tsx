"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, BarChart3, Loader2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { RFQDetail } from "@/lib/types";
import { Button, Card, CardContent, Skeleton, StatusChip } from "@/components/ui";
import { ParsedRequirement } from "@/components/parsed-requirement";
import { ScoutResults } from "@/components/scout-results";
import { OutreachTracker } from "@/components/outreach-tracker";
import { QuoteTable } from "@/components/quote-table";
import { Shortlist } from "@/components/shortlist";
import { VendorDrawer } from "@/components/vendor-drawer";

const STEPS = ["Requirement", "Scout", "Outreach", "Quotes", "Shortlist"];

function stepIndex(rfq: RFQDetail): number {
  if (rfq.shortlist.length > 0) return 4;
  if (rfq.quotes.length > 0) return 3;
  if (rfq.messages.some((m) => m.direction === "outbound")) return 2;
  if (rfq.scout_result.length > 0) return 1;
  return 0;
}

export default function RFQPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const [rfq, setRfq] = useState<RFQDetail | null>(null);
  const [drawerVendor, setDrawerVendor] = useState<number | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setRfq(await api.getRfq(id));
      setError("");
    } catch (e) {
      setError(String(e));
    }
  }, [id]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 8000); // keep the tracker fresh while replies come in
    return () => clearInterval(timer);
  }, [load]);

  async function analyze() {
    setAnalyzing(true);
    try {
      await api.generateShortlist(id);
      await load();
    } finally {
      setAnalyzing(false);
    }
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-red-600">{error}</CardContent>
      </Card>
    );
  }
  if (rfq === null) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const active = stepIndex(rfq);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href="/" className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-100">
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <h1 className="text-lg font-semibold">RFQ #{rfq.id}</h1>
          <StatusChip status={rfq.status} />
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" className="px-2.5 py-1.5 text-xs" onClick={load}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>
          {rfq.quotes.length > 0 && (
            <Button className="px-3 py-1.5 text-xs" onClick={analyze} disabled={analyzing}>
              {analyzing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <BarChart3 className="h-3.5 w-3.5" />}
              {rfq.shortlist.length > 0 ? "Re-run analyst" : "Generate shortlist"}
            </Button>
          )}
        </div>
      </div>

      {/* Pipeline stepper */}
      <div className="flex items-center gap-0 overflow-x-auto">
        {STEPS.map((step, i) => (
          <div key={step} className="flex items-center">
            <div
              className={`flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium ${
                i <= active ? "bg-emerald-100 text-emerald-800" : "bg-zinc-100 text-zinc-400"
              }`}
            >
              <span
                className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] ${
                  i <= active ? "bg-emerald-600 text-white" : "bg-zinc-300 text-white"
                }`}
              >
                {i + 1}
              </span>
              {step}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`h-px w-6 ${i < active ? "bg-emerald-400" : "bg-zinc-200"}`} />
            )}
          </div>
        ))}
      </div>

      {rfq.shortlist.length > 0 && <Shortlist shortlist={rfq.shortlist} explanation={rfq.explanation} />}

      <ParsedRequirement req={rfq.requirement} />
      <ScoutResults candidates={rfq.scout_result} onVendorClick={setDrawerVendor} />
      <OutreachTracker
        rfqId={rfq.id}
        messages={rfq.messages}
        vendors={rfq.vendors}
        hasQuotes={rfq.quotes.length > 0}
        onChanged={load}
        onVendorClick={setDrawerVendor}
      />
      {rfq.quotes.length > 0 && (
        <QuoteTable quotes={rfq.quotes} vendors={rfq.vendors} onVendorClick={setDrawerVendor} />
      )}

      <VendorDrawer vendorId={drawerVendor} onClose={() => setDrawerVendor(null)} />
    </div>
  );
}
