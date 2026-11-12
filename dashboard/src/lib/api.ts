export type Status =
  "waiting" | "in_progress" | "awaiting_sign_off" | "decided";
export type DecisionKind = "approve" | "decline" | "refer";

export interface ClaimRow {
  claim_id: string;
  claim_type: string;
  summary: string;
  customer_name: string;
  amount_claimed: number;
  submitted_on: string;
  status: Status;
  decision: DecisionKind | null;
  payout: number | null;
}

export interface Item {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface PreviousClaim {
  claim_id: string;
  filed_on: string;
  claim_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface Policy {
  policy_id: string;
  plan: string;
  add_ons: string[];
  purchased_on: string;
  trip: {
    destination: string;
    departs_on: string;
    returns_on: string;
    trip_cost: number;
  };
  travelers: string[];
}

export interface Decision {
  decision: DecisionKind;
  payout: number;
  reason: string;
  policy_section: string;
  signed_off_by: string | null;
}

export interface Claim {
  claim_id: string;
  claim_type: string;
  summary: string;
  story: string;
  submitted_on: string;
  incident_date: string;
  incident_location: string;
  amount_claimed: number;
  items: Item[];
  documents: ClaimDocument[];
  status: Status;
  policy: Policy;
  customer: { name: string; previous_claims: PreviousClaim[] };
  decision: Decision | null;
  payment: { amount: number } | null;
}

export interface Step {
  id: number;
  kind: "tool_call" | "tool_result" | "answer" | "error";
  text: string;
}

export interface Handler {
  handler_id: string;
  name: string;
  role: string;
  can_approve_over_limit: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = (await response.json()) as { detail: string };
    throw new Error(body.detail);
  }
  return (await response.json()) as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const api = {
  listClaims: () => request<ClaimRow[]>("/api/claims"),
  getClaim: (id: string) => request<Claim>(`/api/claims/${id}`),
  listSteps: (id: string) => request<Step[]>(`/api/claims/${id}/steps`),
  listHandlers: () => request<Handler[]>("/api/handlers"),
  getInstructions: () => request<{ text: string }>("/api/instructions"),
  runAgent: (id: string) => post<unknown>(`/api/claims/${id}/agent-run`, {}),
  signOff: (id: string, handlerId: string) =>
    post<unknown>(`/api/claims/${id}/sign-off`, { handler_id: handlerId }),
};
