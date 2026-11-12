import { expect, it } from "vitest";
import { decisionLabel, humanize, money, statusLabel } from "./format";

it("formats money in US dollars", () => {
  expect(money(1250)).toBe("$1,250.00");
  expect(money(0)).toBe("$0.00");
});

it("labels states and decisions in plain English", () => {
  expect(statusLabel("awaiting_sign_off")).toBe("Waiting for sign-off");
  expect(statusLabel("in_progress")).toBe("In progress");
  expect(decisionLabel("refer")).toBe("Referred");
});

it("turns codes into words", () => {
  expect(humanize("trip_delay")).toBe("Trip delay");
});
