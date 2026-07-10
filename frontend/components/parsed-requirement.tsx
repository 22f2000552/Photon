import { CalendarDays, IndianRupee, MapPin, Package, ShieldCheck, Truck } from "lucide-react";
import type { Requirement } from "@/lib/types";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";

function Item({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="mt-0.5 text-zinc-400">{icon}</span>
      <div>
        <div className="text-[11px] uppercase tracking-wide text-zinc-400">{label}</div>
        <div className="text-sm font-medium text-zinc-800">{value || "—"}</div>
      </div>
    </div>
  );
}

export function ParsedRequirement({ req }: { req: Requirement }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Understood requirement</CardTitle>
        <Badge variant={req.parse_source === "llm" ? "success" : "info"}>
          parsed by {req.parse_source === "llm" ? "LLM" : "rules engine"} ·{" "}
          {(req.parse_confidence * 100).toFixed(0)}% confidence
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="mb-4 rounded-lg bg-zinc-50 px-3 py-2 text-sm italic text-zinc-600">
          “{req.raw_text}”
        </p>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <Item
            icon={<Package className="h-4 w-4" />}
            label="Product"
            value={[req.quantity ? `${req.quantity} ${req.unit}` : "", req.grade || req.product]
              .filter(Boolean)
              .join(" · ")}
          />
          <Item icon={<MapPin className="h-4 w-4" />} label="Location" value={req.location} />
          <Item
            icon={<CalendarDays className="h-4 w-4" />}
            label="Deadline"
            value={
              req.deadline
                ? new Date(req.deadline).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })
                : ""
            }
          />
          <Item
            icon={<IndianRupee className="h-4 w-4" />}
            label="Budget"
            value={req.budget_amount ? `₹${req.budget_amount.toLocaleString("en-IN")} ${req.budget_basis}` : ""}
          />
          <Item
            icon={<ShieldCheck className="h-4 w-4" />}
            label="Certificates"
            value={req.certifications.join(", ")}
          />
          <Item icon={<Truck className="h-4 w-4" />} label="Delivery" value={req.delivery_terms} />
        </div>
      </CardContent>
    </Card>
  );
}
