import { expect, test } from "@playwright/test";

const id = "123e4567-e89b-12d3-a456-426614174000";

test("retries a failed operational job and refreshes it to pending", async ({ page }) => {
  let retried = false;
  const operationalRecord = () => ({
    id,
    status: retried ? "pending" : "failed",
    error: retried ? null : "Worker unavailable",
    queued_at: "2026-08-23T10:00:00Z",
    created_at: "2026-08-23T10:00:00Z",
    updated_at: "2026-08-23T10:00:00Z",
    manual_retry_count: retried ? 1 : 0,
    last_manual_retry_at: retried ? "2026-08-23T10:05:00Z" : null,
    stale: false,
  });

  await page.route("**/api/ops/care-plans", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ results: [operationalRecord()] }),
    }),
  );
  await page.route(`**/api/ops/care-plans/${id}/retry`, (route) => {
    retried = true;
    return route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify(operationalRecord()),
    });
  });

  await page.goto("/ops");
  await expect(page.getByText("failed", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByText("pending", { exact: true })).toBeVisible();
  await expect(page.getByText("Job successfully resubmitted to the queue.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry" })).toHaveCount(0);
});
