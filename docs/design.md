# Design direction

Goal: as functional and engaging as current short-form video apps, with mindfulness built in. Keep what makes the genre good, and drop the mechanics behind the harms in [background.md](background.md).

Sources: a 2026-11-24 review of short-form video apps and two screen-time apps (an intervention-delay app and a blocking/focus app), using public App Store screenshots, official sites and published research. We borrow **patterns** only. See "Don't copy" below.

## Concept: a feed with a sunset

Today's feed is a day, and a day ends.

- **"Today's 20"**: progress is a sun dot moving along a thin horizon line at the top of the screen, one step per video. It never resets or loops.
- **Break cards** are a pause in the shade: a breathing orb.
- **The recap is "Dusk"**: warm, settled, done. Nothing loads below it.
- **One shape, a plain filled circle**, is the mark, the progress dot and the breathing orb.

## Principles

1. **The feed is as fast as anyone's.** Full-screen vertical swipe, right action rail, caption bottom-left, tap to mute, double-tap to like. Swipes land in under 400 ms; preload ahead.
2. **Ending is the easy choice.** On break and cap screens the primary, warm, one-tap button ends the session and "keep watching" is a quiet text link. Research on a delay-and-dismiss intervention (PNAS 2023, Grüning et al.) found the one-tap dismiss option drove the effect, while a text-only "are you sure?" didn't. The app's developer co-authored that study; check figures in the paper before citing.
3. **No guilt.** Copy points to the user's own choices ("You set 25 minutes. You're at 24.") and frames gains, not shame. Never write a "No, I like wasting time"-style button.
4. **No variable rewards.** No public like or share counts, streaks, flames, leaderboards, confetti or surprise unlocks. Any acknowledgment is predictable and calm.
5. **Explain the algorithm.** Every video can answer "Why this?" in plain language, with controls that actually change the feed.
6. **Endings stay endings.** The recap has nothing below it, ever.
7. **Honesty.** Compare mode is labeled as a simulation.

## Visual language

| Token | Hex | Use |
|---|---|---|
| `ink` | `#0F1110` | Feed background (warm near-black) |
| `night` | `#1B1E1B` | Sheets and cards over the feed |
| `paper` | `#F5F0E6` | Text on video; light mindful surfaces |
| `mist` | `#B9B4A8` | Secondary text on dark |
| `stone` | `#6B675E` | Secondary text on paper |
| `sage` | `#A8C3A0` | Calm primary action on dark ("I'm good, end here") |
| `moss` | `#4A6646` | Primary action and text on paper |
| `ember` | `#EE7F5C` | The only warm accent: liked heart, sun dot, key numbers. Use sparingly |
| `sun` | `#F2C46D` | Breathing highlight, dawn and dusk gradients |
| `plum` | `#6E4A5E` | End of the dusk gradient |

- **Dusk gradient** (break, recap): `sun → ember → plum`.
- **Topic colors** (recap mix): sage `#A8C3A0`, lake `#8FB3C9`, ochre `#E7B36A`, heather `#C99AB8`, ember, stone `#9C9488`. Always labeled, never color alone.
- **Type:** Fraunces (soft serif) for reflective screens and big numbers; Inter for feed chrome; tabular figures for numbers.
- **Motion:** the feed is quick (about 220 ms snap). Mindful screens move at breath pace: 4 s in, 4 s out. Respect `prefers-reduced-motion`.

## Screens (build order), each mapped to a harm

| # | Screen | What | Harm |
|---|---|---|---|
| 1 | Feed chrome + horizon progress | Rail: Like, Send to a friend, Why this; no counts; double-tap to like; 2-line captions; horizon progress on finite feeds | Addictive loops, echo chambers |
| 2 | Break card | 3 breathing cycles, then "I'm good, end here" (primary) / "Keep watching" (link); rotating variants so it doesn't become wallpaper | Addictive loops |
| 3 | Dusk recap | Minutes, videos, sent to friends; topic mix bar; "new to you" line; one "worth it?" check; nothing below | Echo chambers, loops, connection |
| 4 | Why this sheet | Plain reason + "See less of this", "More things I haven't tried", "Not for me" | Echo chambers, harmful content |
| 5 | Time cap | Setup with presets; at the cap, one bounded "+5 min, once today" (parent mode: ask a parent) | Addictive loops |
| 6 | Intention prompt | "What are you here for?" before the feed; echoed on break and recap; weights the ranker | Loops, echo chambers |
| 7 | Do this together | Offline challenge cards; mutual reveal when both friends finish; no streaks or random-time pushes | Real-world connection |
| 8 | Sensitive content | Blurred first frame with the reason; Skip (primary) / Watch anyway; kids: Skip only | Harmful content |
| 9 | Parent controls | Situation cards ("School nights · 30 min · none after 9pm") | Harmful content, loops |

## Don't copy

Genre conventions are fine: vertical swipe, right rail, bottom sheets, breathing circles, intention prompts, "you've reached the end". **Not** fine:
- Other apps' logos, icons, wordmarks, feature names or exact copy lines.
- Distinctive trade dress: cyan/red glitch accents, spinning record discs, gem or crystal renders, hourglass illustrations, navy-and-periwinkle schemes, emoji intention grids.
- Real third-party app icons inside our UI.
- Reference screenshots in this repo. It's public.
