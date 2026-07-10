"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Vendor } from "@/lib/types";
import { Badge, Card, CardContent, CardHeader, CardTitle, ChannelIconLabel, ScoreBar, Skeleton } from "@/components/ui";
import { VendorDrawer } from "@/components/vendor-drawer";

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[] | null>(null);
  const [drawer, setDrawer] = useState<number | null>(null);

  useEffect(() => {
    api.listVendors().then(setVendors).catch(() => setVendors([]));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold">Vendor pool</h1>
      {vendors === null ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {vendors.map((v) => (
            <Card
              key={v.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => setDrawer(v.id)}
            >
              <CardHeader>
                <CardTitle>{v.name}</CardTitle>
                <div className="text-xs text-zinc-400">
                  {v.city}, {v.state}
                </div>
              </CardHeader>
              <CardContent>
                <div className="mb-2 flex flex-wrap gap-1.5">
                  {v.categories.map((c) => (
                    <Badge key={c}>{c}</Badge>
                  ))}
                  {v.contacts.map((c) => (
                    <Badge key={c.id} variant="info">
                      <ChannelIconLabel channel={c.channel} />
                    </Badge>
                  ))}
                </div>
                {v.memory && <ScoreBar label="Reliability" value={v.memory.reliability_score} />}
                <p className="mt-2 line-clamp-2 text-xs text-zinc-500">{v.notes}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <VendorDrawer vendorId={drawer} onClose={() => setDrawer(null)} />
    </div>
  );
}
