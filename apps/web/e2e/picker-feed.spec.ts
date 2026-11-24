import { expect, test } from "@playwright/test";
import { expectClipPlaying } from "./helpers";

test("viewer picks a persona and a ranker, and the first clip plays", async ({ page }) => {
  await page.goto("/");
  await page.getByText("George", { exact: true }).click();
  await page.getByRole("link", { name: "Detoks feed" }).click();

  await expect(page).toHaveURL(/\/feed\?user=george&ranker=detoks/);
  await expectClipPlaying(page);
});
