# Eval: does the world change what agents find?

The eval asks fresh headless agents task-shaped questions whose answers already exist in the project, once in a copy with the world and once in a copy without it. Both copies sit outside the project so no parent `CLAUDE.md` leaks in. The baseline copy drops `world/`, `.claude/skills/world/`, and the marked trailhead block. Everything else is identical, including the prompt.

## Steps

1. **Sample targets.** `worldbuilder eval sample --n 10 --seed <any int>`. This picks random existing files and headings, spread across areas, from the survey rather than from the maps. Sampling from the maps would only test what the maps already contain. Output: `world/.eval/targets.json`.
2. **Write probes.** Launch `worldbuilder:world-probe-writer` with the targets path and the output path `world/.eval/probes.json`. It writes one probe per target plus two negatives (things the project genuinely lacks). Read the probes. Discard any probe whose question names the target's file or title, and have the writer replace it.
3. **Prepare arms.** `worldbuilder eval prepare`. It prints the eval directory.
4. **Confirm cost.** Runs = probes × 2 arms × trials. Tell the user the run count and the model, and get a yes before running. Each run is a full headless Claude session.
5. **Run.** `worldbuilder eval run --dir <eval dir> --probes world/.eval/probes.json [--model <model>] [--trials N] [--jobs 4]`. Run it in the background. It skips runs that already have results, so re-running it finishes an interrupted eval.
6. **Score.** `worldbuilder eval score --dir <eval dir> --probes world/.eval/probes.json [--trials N]`. Copy `<eval dir>/report.md` to `world/.eval/report-<YYYY-MM-DD>.md`.

## Reading the result

Before reading accuracy, confirm the run happened: "Runs present" equals expected, and "parsed" equals "runs" in both arms. A missing or unparsed run is an error, not a miss. Report it as one.

- **Accuracy** is the share of runs that cited an expected file (or, for negatives, answered `existing: false`).
- **Tokens, cost, turns** show what finding it cost. A world that keeps accuracy flat while cutting turns still helps.
- With 12 probes and one trial, a difference of one or two probes is noise. Say so. Recommend `--trials 3` before acting on a small difference.

## Diagnosing each world-arm miss

For every probe the world arm got wrong, read its result file (`results/<probe>-world-<trial>.json`, the `result` field) and decide which failure it is:

- **Missing knowledge**: the expected file is on no map (`grep -r <path> world/` finds nothing). Fix: add an entry to that area's map.
- **Broken road**: the file is on a map but the agent never opened `world/WORLD.md` or the router skill. Fix: sharpen the trailhead block or the router skill's description.
- **Weak entry**: the agent read the map entry and still went elsewhere. Fix: rewrite the entry's "Use when" line in the words the probe used.
- **Bad probe**: the expected answer is wrong or ambiguous. Fix the probe and don't count the miss against the world.

Report the misses grouped by these four, with the fix for each.
