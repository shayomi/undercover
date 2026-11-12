import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { stubApi } from "../test/stub-api";
import { InstructionsPage } from "./instructions-page";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the agent's instructions, read only", async () => {
  stubApi({
    "GET /api/instructions": { text: "You are the UnderCover Agent." },
  });
  render(<InstructionsPage />);
  expect(
    await screen.findByText("You are the UnderCover Agent."),
  ).toBeDefined();
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(screen.queryByRole("button")).toBeNull();
});

it("says when the instructions cannot be loaded", async () => {
  stubApi({});
  render(<InstructionsPage />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Could not load the instructions",
  );
});
