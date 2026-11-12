import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./app";
import { claim, row, steps, stubApi } from "./test/stub-api";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

function go(hash: string) {
  act(() => {
    window.location.hash = hash;
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
}

it("routes between the queue, a claim and the instructions", async () => {
  stubApi({
    "GET /api/claims": [row],
    "GET /api/claims/CLM-1001": claim,
    "GET /api/claims/CLM-1001/steps": steps,
    "GET /api/instructions": { text: "You are the UnderCover Agent." },
  });
  render(<App />);
  expect(
    await screen.findByRole("heading", { name: "Claims queue" }),
  ).toBeDefined();

  go("#/claims/CLM-1001");
  expect(
    await screen.findByText("My flight home from Rome was canceled."),
  ).toBeDefined();

  go("#/instructions");
  expect(
    await screen.findByText("You are the UnderCover Agent."),
  ).toBeDefined();
  const link = screen.getByRole("link", { name: "Agent instructions" });
  expect(link.getAttribute("aria-current")).toBe("page");
});
