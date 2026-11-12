import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { row, stubApi } from "../test/stub-api";
import { QueuePage } from "./queue-page";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("lists the claims with their state and amount", async () => {
  stubApi({
    "GET /api/claims": [
      row,
      {
        ...row,
        claim_id: "CLM-1002",
        status: "awaiting_sign_off",
        decision: "approve",
        payout: 1250,
      },
    ],
  });
  render(<QueuePage />);
  const link = await screen.findByRole("link", { name: "CLM-1001" });
  expect(link.getAttribute("href")).toBe("#/claims/CLM-1001");
  const table = screen.getByRole("table");
  expect(within(table).getAllByText("$1,250.00")).toHaveLength(3);
  expect(within(table).getByText("Waiting")).toBeDefined();
  expect(within(table).getByText("Waiting for sign-off")).toBeDefined();
  expect(within(table).getByText("Approved")).toBeDefined();
  expect(within(table).getAllByText("Trip delay")).toHaveLength(2);
  const counts = screen.getByRole("region", { name: "Claims by state" });
  expect(within(counts).getAllByText("1")).toHaveLength(2);
});

it("starts the agent on a waiting claim", async () => {
  const fetchMock = stubApi({
    "GET /api/claims": [row],
    "POST /api/claims/CLM-1001/agent-run": { thread_id: "t" },
  });
  render(<QueuePage />);
  fireEvent.click(await screen.findByRole("button", { name: "Run agent" }));
  await vi.waitFor(() => {
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/claims/CLM-1001/agent-run",
      expect.objectContaining({ method: "POST" }),
    );
  });
});

it("shows why the agent could not start", async () => {
  stubApi({ "GET /api/claims": [row] });
  render(<QueuePage />);
  fireEvent.click(await screen.findByRole("button", { name: "Run agent" }));
  expect((await screen.findByRole("alert")).textContent).toContain(
    "No stub for POST",
  );
});

it("says when the backend cannot be reached", async () => {
  stubApi({});
  render(<QueuePage />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Could not load the queue",
  );
});
