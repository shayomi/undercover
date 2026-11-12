import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { Claim } from "../lib/api";
import { claim, handlers, steps, stubApi } from "../test/stub-api";
import { ClaimPage } from "./claim-page";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const approved = {
  decision: "approve" as const,
  payout: 1250,
  reason: "The delay is covered. The costs are within the limit.",
  policy_section: "Section 3. Trip Delay",
  signed_off_by: null,
};

function routesFor(state: Claim, stepList = steps): Record<string, unknown> {
  return {
    "GET /api/claims/CLM-1001": state,
    "GET /api/claims/CLM-1001/steps": stepList,
    "GET /api/handlers": handlers,
  };
}

it("shows a waiting claim in full", async () => {
  stubApi(routesFor(claim, []));
  render(<ClaimPage claimId="CLM-1001" />);
  expect(
    await screen.findByText("My flight home from Rome was canceled."),
  ).toBeDefined();
  expect(screen.getByText("Airport hotel")).toBeDefined();
  expect(screen.getByText("Hotel receipt")).toBeDefined();
  expect(screen.getByText("Premium")).toBeDefined();
  expect(screen.getByText("Electronics plus")).toBeDefined();
  expect(screen.getByText(/Checked bag arrived 30 hours late/)).toBeDefined();
  expect(
    screen.getByText("The agent has not decided this claim yet."),
  ).toBeDefined();
  expect(
    screen.getByText("The agent has not worked on this claim yet."),
  ).toBeDefined();
  expect(screen.getByRole("button", { name: "Run agent" })).toBeDefined();
});

it("refreshes the agent's steps while it works", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const routes = routesFor(
    { ...claim, status: "in_progress" },
    steps.slice(0, 1),
  );
  stubApi(routes);
  render(<ClaimPage claimId="CLM-1001" />);
  expect(
    await screen.findByText("The agent is working on this claim."),
  ).toBeDefined();
  expect(screen.getByText("get_claim(claim_id=CLM-1001)")).toBeDefined();
  expect(screen.queryByText('{"claim_id":"CLM-1001"}')).toBeNull();

  routes["GET /api/claims/CLM-1001/steps"] = [
    ...steps,
    { id: 3, kind: "answer", text: "Approved $420.00." },
  ];
  await vi.advanceTimersByTimeAsync(1000);
  expect(await screen.findByText('{"claim_id":"CLM-1001"}')).toBeDefined();
  expect(screen.getByText("Approved $420.00.")).toBeDefined();
});

it("watches the claim once the agent is started", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const routes: Record<string, unknown> = {
    ...routesFor(claim, []),
    "POST /api/claims/CLM-1001/agent-run": { thread_id: "t" },
  };
  stubApi(routes);
  render(<ClaimPage claimId="CLM-1001" />);
  fireEvent.click(await screen.findByRole("button", { name: "Run agent" }));
  routes["GET /api/claims/CLM-1001"] = { ...claim, status: "in_progress" };
  await vi.advanceTimersByTimeAsync(1000);
  expect(
    await screen.findByText("The agent is working on this claim."),
  ).toBeDefined();

  const decided = {
    ...claim,
    status: "decided",
    decision: { ...approved, payout: 420 },
  };
  routes["GET /api/claims/CLM-1001"] = decided;
  routes["GET /api/claims/CLM-1001/steps"] = steps;
  await vi.advanceTimersByTimeAsync(1000);
  expect(await screen.findByText("Not paid yet.")).toBeDefined();

  routes["GET /api/claims/CLM-1001"] = { ...decided, payment: { amount: 420 } };
  routes["GET /api/claims/CLM-1001/steps"] = [
    ...steps,
    { id: 3, kind: "answer", text: "Approved and paid $420.00." },
  ];
  await vi.advanceTimersByTimeAsync(1000);
  expect(await screen.findByText("Approved and paid $420.00.")).toBeDefined();
  expect(screen.getByText(/^Paid/).textContent).toBe("Paid $420.00");
});

it("shows a decided and paid claim", async () => {
  stubApi(
    routesFor({
      ...claim,
      status: "decided",
      decision: { ...approved, payout: 420 },
      payment: { amount: 420 },
    }),
  );
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("Approved")).toBeDefined();
  expect(screen.getByText(approved.reason)).toBeDefined();
  expect(screen.getByText("Section 3. Trip Delay")).toBeDefined();
  expect(screen.getByText(/^Paid/).textContent).toBe("Paid $420.00");
  expect(screen.queryByRole("button")).toBeNull();
});

it("shows an approved claim that has not been paid", async () => {
  stubApi(
    routesFor({
      ...claim,
      status: "decided",
      decision: { ...approved, payout: 420 },
    }),
  );
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("Not paid yet.")).toBeDefined();
});

it("signs off a payout over the limit", async () => {
  const routes: Record<string, unknown> = {
    ...routesFor({ ...claim, status: "awaiting_sign_off", decision: approved }),
    "POST /api/claims/CLM-1001/sign-off": { status: "decided" },
  };
  const fetchMock = stubApi(routes);
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("Waiting for sign-off")).toBeDefined();
  const button = screen.getByRole("button", { name: "Sign off payment" });
  expect((button as HTMLButtonElement).disabled).toBe(true);
  await screen.findByRole("option", { name: /Dana Whitfield/ });
  expect(screen.queryByRole("option", { name: /Sam Junior/ })).toBeNull();

  routes["GET /api/claims/CLM-1001"] = {
    ...claim,
    status: "decided",
    decision: { ...approved, signed_off_by: "Dana Whitfield" },
    payment: { amount: 1250 },
  };
  const select = screen.getByRole("combobox", { name: /Handler/ });
  fireEvent.change(select, { target: { value: "HND-01" } });
  fireEvent.click(button);
  expect(await screen.findByText(/signed off by Dana Whitfield/)).toBeDefined();
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/claims/CLM-1001/sign-off",
    expect.objectContaining({ body: JSON.stringify({ handler_id: "HND-01" }) }),
  );
});

it("shows why a sign-off failed", async () => {
  stubApi(
    routesFor({ ...claim, status: "awaiting_sign_off", decision: approved }),
  );
  render(<ClaimPage claimId="CLM-1001" />);
  await screen.findByRole("option", { name: /Dana Whitfield/ });
  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "HND-01" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign off payment" }));
  expect((await screen.findByRole("alert")).textContent).toContain(
    "No stub for POST",
  );
});

it("shows an error step and a declined claim", async () => {
  stubApi(
    routesFor(
      {
        ...claim,
        status: "decided",
        decision: { ...approved, decision: "decline", payout: 0 },
        customer: { ...claim.customer, previous_claims: [] },
        policy: { ...claim.policy, add_ons: [] },
      },
      [{ id: 1, kind: "error", text: "The agent stopped: timeout" }],
    ),
  );
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("Declined")).toBeDefined();
  expect(screen.getByText("The agent stopped: timeout")).toBeDefined();
  expect(screen.getByText("No earlier claims.")).toBeDefined();
  expect(screen.getByText("None")).toBeDefined();
});

it("says when the claim cannot be loaded", async () => {
  stubApi({});
  render(<ClaimPage claimId="CLM-0000" />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Could not load CLM-0000",
  );
});
