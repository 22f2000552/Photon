import { AlertTriangle, CheckCircle2, History } from "lucide-react";
import type { ScoutCandidate } from "@/lib/types";
import { Badge, Card, CardContent, CardHeader, CardTitle, ChannelIconLabel } from "@/components/ui";

export function ScoutResults({
  candidates,
  onVendorClick,
}: {
  candidates: ScoutCandidate[];
  onVendorClick: (id: number) => void;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Scout — vendor candidates</CardTitle>
        <span className="text-xs text-zinc-400">
          {candidates.filter((c) => c.qualified).length} qualified of {candidates.length} found
        </span>
      </CardHeader>
      <CardContent className="p-0">
        {candidates.length === 0 ? (
          <p className="p-5 text-sm text-zinc-500">No vendors matched this requirement.</p>
        ) : (
          <ul className="divide-y divide-zinc-100">
            {candidates.map((c) => (
              <li
                key={c.vendor_id}
                className="cursor-pointer px-5 py-3.5 transition-colors hover:bg-zinc-50"
                onClick={() => onVendorClick(c.vendor_id)}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {c.qualified ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500" />
                    )}
                    <span className="text-sm font-medium">{c.name}</span>
                    <span className="text-xs text-zinc-400">{c.city}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <History className="h-3.5 w-3.5" />
                    reliability {c.reliability_score.toFixed(0)}/100 · {c.past_rfqs} past RFQs
                  </div>
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5 pl-6">
                  {c.channels.map((ch) => (
                    <Badge key={ch} variant="info">
                      <ChannelIconLabel channel={ch} />
                    </Badge>
                  ))}
                  <Badge>profile {(c.profile_completeness * 100).toFixed(0)}%</Badge>
                  {c.certificates.map((cert, i) => (
                    <Badge key={i} variant={cert.status === "valid" ? "success" : "warning"}>
                      {cert.type} {cert.status}
                    </Badge>
                  ))}
                  {c.flags.map((f) => (
                    <Badge key={f} variant="danger">
                      {f}
                    </Badge>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
