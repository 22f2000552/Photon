import type { RFQDetail, RFQSummary, Vendor } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => request<{ status: string; llm: string }>("/api/health"),
  createRequirement: (text: string) =>
    request<{ rfq_id: number }>("/api/requirements", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  listRfqs: () => request<RFQSummary[]>("/api/rfqs"),
  getRfq: (id: number) => request<RFQDetail>(`/api/rfqs/${id}`),
  runScout: (id: number) => request(`/api/rfqs/${id}/scout`, { method: "POST" }),
  runOutreach: (id: number) => request(`/api/rfqs/${id}/outreach`, { method: "POST" }),
  addReply: (id: number, vendor_id: number, channel: string, text: string) =>
    request(`/api/rfqs/${id}/replies`, {
      method: "POST",
      body: JSON.stringify({ vendor_id, channel, text }),
    }),
  simulateReplies: (id: number) =>
    request<{ ingested: number; ghosted: number }>(`/api/rfqs/${id}/simulate-replies`, { method: "POST" }),
  generateShortlist: (id: number) => request(`/api/rfqs/${id}/shortlist`, { method: "POST" }),
  listVendors: () => request<Vendor[]>("/api/vendors"),
  getVendor: (id: number) => request<Vendor>(`/api/vendors/${id}`),
};