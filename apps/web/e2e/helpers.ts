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

/** Index of the feed card whose clip is playing, or -1 (e.g. on a break or end card). */
export async function playingCard(page: Page): Promise<number> {
  return page.evaluate(() => {
    const v = [...document.querySelectorAll("video")].find((el) => !el.paused);
    const card = v?.closest<HTMLElement>("[data-index]");
    return card ? Number(card.dataset.index) : -1;
  });
}

/** Swipe up to the next card, as a viewer would, and wait until the swipe has landed. */
export async function swipeToNext(page: Page) {
  const before = await playingCard(page);
  const { height } = page.viewportSize()!;
  await page.mouse.move(10, height / 2);
  await page.mouse.wheel(0, height);
  await expect.poll(() => playingCard(page), { timeout: 10_000 }).not.toBe(before);
}
