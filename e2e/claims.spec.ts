import { expect, test, type APIRequestContext } from "@playwright/test";

async function decide(
  request: APIRequestContext,
  claimId: string,
  decision: Record<string, unknown>,
) {
  expect((await request.post(`/api/claims/${claimId}/start`)).ok()).toBe(true);
  const response = await request.post(`/api/claims/${claimId}/decision`, {
    data: {
      reason: "The loss is covered. The amount is within the plan's limits.",
      policy_section: "Section 5. Baggage and Personal Effects",
      ...decision,
    },
  });
  expect(response.ok()).toBe(true);
}

test("the queue lists the claims and opens one", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Claims queue" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(25);
  await page.getByRole("link", { name: "CLM-1001" }).click();
  await expect(page).toHaveURL(/#\/claims\/CLM-1001$/);
  await expect(page.getByText(/My flight home from Rome/)).toBeVisible();
  await expect(page.getByText("Airport hotel, one night")).toBeVisible();
  await expect(
    page.getByText("Meridian Air cancellation notice"),
  ).toBeVisible();
  await expect(page.getByText("POL-2001")).toBeVisible();
  await expect(
    page.getByText(/Checked bag arrived 30 hours late/),
  ).toBeVisible();
});

test("a decision shows on the claim and in the queue", async ({
  page,
  request,
}) => {
  await decide(request, "CLM-1009", { decision: "approve", payout: 300 });
  expect(
    (
      await request.post("/api/claims/CLM-1009/payment", {
        data: { amount: 300 },
      })
    ).ok(),
  ).toBe(true);

  await page.goto("/#/claims/CLM-1009");
  const decision = page.locator(".decision");
  await expect(decision.getByText("Approved")).toBeVisible();
  await expect(decision.getByText("$300.00").first()).toBeVisible();
  await expect(
    decision.getByText("Section 5. Baggage and Personal Effects"),
  ).toBeVisible();
  await expect(decision.getByText("Paid $300.00")).toBeVisible();

  await page.goto("/");
  const row = page.getByRole("row", { name: /CLM-1009/ });
  await expect(row.getByText("Decided")).toBeVisible();
  await expect(row.getByText("Approved")).toBeVisible();
});

test("a payout over $1,000 waits for a handler's sign-off", async ({
  page,
  request,
}) => {
  await decide(request, "CLM-1011", { decision: "approve", payout: 1250 });
  const blocked = await request.post("/api/claims/CLM-1011/payment", {
    data: { amount: 1250 },
  });
  expect(blocked.status()).toBe(409);
  expect(await blocked.json()).toEqual({
    detail: "Needs a handler's sign-off",
  });

  await page.goto("/#/claims/CLM-1011");
  const heading = page.locator(".claim-heading");
  await expect(heading.getByText("Waiting for sign-off")).toBeVisible();
  await page
    .getByRole("combobox", { name: /Handler/ })
    .selectOption({ label: "Dana Whitfield, Senior Claims Handler" });
  await page.getByRole("button", { name: "Sign off payment" }).click();
  await expect(
    page.getByText("Paid $1,250.00 · signed off by Dana Whitfield"),
  ).toBeVisible();
  await expect(heading.getByText("Decided")).toBeVisible();
});

test("the agent's instructions are read only", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Agent instructions" }).click();
  await expect(page.getByText(/You are the UnderCover Agent/)).toBeVisible();
  await expect(page.getByRole("textbox")).toHaveCount(0);
});
