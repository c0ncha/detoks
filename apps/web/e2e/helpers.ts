import { expect, type Page } from "@playwright/test";

/** Seconds played by the clip currently on screen (the one that isn't paused). */
export async function playingTime(page: Page): Promise<number> {
  return page.evaluate(() => {
    const v = [...document.querySelectorAll("video")].find((el) => !el.paused);
    return v ? v.currentTime : -1;
  });
}

export async function expectClipPlaying(page: Page, atLeastSeconds = 0.5) {
  await expect.poll(() => playingTime(page), { timeout: 15_000 }).toBeGreaterThan(atLeastSeconds);
}
