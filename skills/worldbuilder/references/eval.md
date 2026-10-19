# Eval: does the world change what agents do?

The world exists for one failure: an agent handed work never thinks to look, and rebuilds something the project already has. The eval reproduces that. Fresh headless agents get build tasks whose right starting point already exists in the project, once in a copy with the world and once in a copy without it. Nobody tells them to look. The tool trace shows whether they opened the existing work before building.

Both copies sit outside the project so no parent `CLAUDE.md` leaks in. The baseline copy drops `world/`, `.claude/skills/world/`, and the marked trailhead block. Everything else is identical, including the prompt. Each build-task run gets its own copy-on-write clone of its arm, so one run's writes never reach another, and the clone is deleted afterwards.

Find mode (`"kind": "find"`) is the older probe type: it asks whether something exists. Asking primes every agent to search, so on a small project both arms score near 100%. Use it only to check that the map's entries point at the right files.

## Steps

1. **Sample targets.** `worldbuilder eval sample --n 12 --seed <any int>`. This picks random existing files and headings, spread across areas, from the survey rather than from the maps. Sampling from the maps would only test what the maps already contain. Output: `world/.eval/targets.json`.
2. **Write probes.** Launch `worldbuilder:world-probe-writer` with the targets path, the output path `world/.eval/probes.json`, and mode `task`. Read the probes. Replace any probe that names its target's file or title, or that asks whether something exists rather than handing over work.
3. **Prepare arms.** `worldbuilder eval prepare`. It prints the eval directory.
4. **Confirm cost.** Runs = probes × 2 arms × trials. Build tasks run longer than questions because the agent does the work. Tell the user the run count, the model, and a cost range, and get a yes before running.
5. **Run.** `worldbuilder eval run --dir <eval dir> --probes world/.eval/probes.json [--model <model>] [--trials N] [--jobs 4]`. Run it in the background. Agents get Read, Grep, Glob, Skill, and Edit/Write inside their clone, and no shell. A rerun skips runs that already have results.
6. **Score.** `worldbuilder eval score --dir <eval dir> --probes world/.eval/probes.json [--trials N]`. Copy `<eval dir>/report.md` to `world/.eval/report-<YYYY-MM-DD>.md`.

## Reading the result

Before reading anything else, confirm the run happened: "Runs present" equals expected, and "parsed" equals "runs" in both arms. A missing or unparsed run is an error, not a miss. Report it as one.

- **Found** is the share of runs that opened an expected file. This is the headline number.
- **Rebuilt** counts runs that created files without ever opening the existing work. This is the failure the world prevents.
- **Map used** counts runs that opened `world/` or the `world` skill. In the world arm it shows whether the trailhead works at all.
- **Tokens, cost, turns** show what the world costs. A world that raises found and cuts rebuilt is worth some extra turns.
- With 12 probes and one trial, a difference of one or two probes is noise. Say so. Recommend `--trials 3` before acting on a small difference.

## Diagnosing each world-arm miss

The report gives a first-pass diagnosis for each world-arm miss. Confirm it by reading the run's trace (`results/<probe>-world-<trial>.json`, the `stdout` field holds one JSON event per line):

- **Missing knowledge**: no map names the expected file. Fix: add an entry to that area's map.
- **Broken road**: the file is on a map but the agent never opened the map or the router skill. Fix: sharpen the trailhead block or the router skill's description.
- **Weak entry**: the agent read the map and still went elsewhere. Fix: rewrite the entry's "Use when" line in the words the task used.
- **Bad probe**: the expected file isn't really the right starting point for the task. Fix the probe and don't count the miss against the world.

Report the misses grouped by these four, with the fix for each.
