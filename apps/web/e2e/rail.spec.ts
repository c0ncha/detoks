import { expect, test } from "@playwright/test";
import { expectClipPlaying, playingCard } from "./helpers";

async function onScreenCard(page: import("@playwright/test").Page) {
  return page.locator(`[data-index="${await playingCard(page)}"]`);
}

test("double-tapping a clip likes it", async ({ page }) => {
  await page.goto("/feed?user=george&ranker=detoks");
  await expectClipPlaying(page);
  const card = await onScreenCard(page);

  await card.locator("video").dblclick();
  await expect(card.getByRole("button", { name: "Like" })).toHaveAttribute("aria-pressed", "true");
});

test("the rail offers Like, Send to a friend and Why this, with no public counts", async ({ page }) => {
  await page.goto("/feed?user=george&ranker=detoks");
  await expectClipPlaying(page);
  const card = await onScreenCard(page);

  for (const name of ["Like", "Send to a friend", "Why this"]) {
    await expect(card.getByRole("button", { name })).toBeVisible();
  }
  await expect(card.getByRole("button", { name: "Like" })).not.toContainText(/\d/);
});

test("Why this explains what shaped the pick", async ({ page }) => {
  await page.goto("/feed?user=george&ranker=detoks");
  await expectClipPlaying(page);
  const card = await onScreenCard(page);

  await card.getByRole("button", { name: "Why this" }).click();
  const sheet = page.getByRole("dialog", { name: "Why this video" });
  await expect(sheet).toBeVisible();
  await expect(sheet).toContainText("relevance");
});
