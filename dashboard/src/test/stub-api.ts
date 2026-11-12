import { vi } from "vitest";
import type { Claim, ClaimRow, Handler, Step } from "../lib/api";

/** Stub fetch with replies keyed by "METHOD /path". Tests may change `routes` between calls. */
export function stubApi(routes: Record<string, unknown>) {
  const fetchMock = vi.fn((input: string, init?: RequestInit) => {
    const key = `${init?.method ?? "GET"} ${input}`;
    const found = key in routes;
    const body = found ? routes[key] : { detail: `No stub for ${key}` };
    const status = found ? 200 : 404;
    return Promise.resolve(new Response(JSON.stringify(body), { status }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export const row: ClaimRow = {
  claim_id: "CLM-1001",
  claim_type: "trip_delay",
  summary: "Flight home canceled by the airline",
  customer_name: "Maya Patel",
  amount_claimed: 1250,
  submitted_on: "2026-06-24",
  status: "waiting",
  decision: null,
  payout: null,
};

export const claim: Claim = {
  claim_id: "CLM-1001",
  claim_type: "trip_delay",
  summary: "Flight home canceled by the airline",
  story: "My flight home from Rome was canceled.",
  submitted_on: "2026-06-24",
  incident_date: "2026-06-18",
  incident_location: "Rome, Italy",
  amount_claimed: 420,
  items: [
    { description: "Airport hotel", category: "accommodation", amount: 245 },
  ],
  documents: [
    { name: "Hotel receipt", type: "receipt", content: "One night, $245.00." },
  ],
  status: "waiting",
  policy: {
    policy_id: "POL-2001",
    plan: "premium",
    add_ons: ["electronics_plus"],
    purchased_on: "2026-04-22",
    trip: {
      destination: "Rome, Italy",
      departs_on: "2026-06-10",
      returns_on: "2026-06-18",
      trip_cost: 3100,
    },
    travelers: ["Maya Patel"],
  },
  customer: {
    name: "Maya Patel",
    previous_claims: [
      {
        claim_id: "CLM-0412",
        filed_on: "2024-08-19",
        claim_type: "baggage_delay",
        summary: "Checked bag arrived 30 hours late",
        outcome: "approved",
        amount_paid: 140,
      },
    ],
  },
  decision: null,
  payment: null,
};

export const steps: Step[] = [
  { id: 1, kind: "tool_call", text: "get_claim(claim_id=CLM-1001)" },
  { id: 2, kind: "tool_result", text: '{"claim_id":"CLM-1001"}' },
];

export const handlers: Handler[] = [
  {
    handler_id: "HND-01",
    name: "Dana Whitfield",
    role: "Senior Claims Handler",
    can_approve_over_limit: true,
  },
  {
    handler_id: "HND-03",
    name: "Sam Junior",
    role: "Claims Handler",
    can_approve_over_limit: false,
  },
];
