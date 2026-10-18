---
name: worldbuilder
description: Build or refresh a world map of a project (repo, docs folder, Obsidian vault) so agents find existing work before rebuilding it. Use when asked to map a project, onboard agents to a codebase or vault, run worldbuilder, check a world map for broken roads or staleness, or test whether the map helps agents.
---

# Worldbuilder

You build a **world** for one project: a wide, shallow map in `world/` that every agent reaches from the project's trailhead, so an agent knows what already exists before it searches. Subagents map the areas. The `worldbuilder` CLI does the exact parts: listing the territory, following links, finding broken roads, running the eval.

The map is a guide to the territory, never a copy of it. Every entry links to a real file, and `worldbuilder check` proves it.

## Hard rules

- You write only inside `world/`, `.claude/skills/world/`, and the marked block in the trailhead file. Report problems in the project's own files (dead links, orphans) to the user and leave those files as they are.
- The trailhead edit changes how every future agent boots in this project. Show the user the exact block and file, and apply it only after they say yes.
- The eval spends money. Get a yes on the run count before `worldbuilder eval run`.

Format for every file you or a subagent writes: [references/world-format.md](references/world-format.md).

## Step 0: New world or refresh?

Find the project root (the user names it, or the current directory). If `world/WORLD.md` exists, this is a **refresh**: run `worldbuilder check`, and rebuild only the areas it marks STALE, the areas holding uncovered files, and any area map with broken roads. Then go to Step 2 with that list. Otherwise start at Step 1.

## Step 1: Survey and agree on areas

1. `worldbuilder survey`. It writes `world/.survey.json` and prints the proposed areas, link style, trailheads, and project skills.
2. Turn the proposal into an area list. Merge areas under about 5 files into a neighbor. Put generated output, archives, imports, and eval workspaces under one "edges" area, or into `exclude` when they shouldn't be in the territory at all. Name each area the way the project's people would.
3. Show the user the list (id, name, covers, file count) in one table and ask for changes. Record the agreed list and any excludes in `world/config.json`. If you changed excludes, run `worldbuilder survey` again.

Done when every file in the survey falls under some area's `covers` or under `exclude`, and the user has agreed to the list.

## Step 2: Map each area

Launch one `worldbuilder:world-cartographer` per area, all in one message so they run in parallel. Give each: the project root, area id, title, covers, the survey's `generated` timestamp and `link_style`, the full list of area ids and titles (for routes out), and the output path `world/<area-id>.md`. For a refresh, also give the existing map path so it updates rather than starting over.

Done when every area has a map and `worldbuilder check` lists no broken roads in `world/`.

## Step 3: Write WORLD.md

Read every area map's intro and Landmarks. Write `world/WORLD.md`: one row per area, the highways that cross areas, and the edges. It names everything and explains nothing. Stay under 120 lines.

Done when `worldbuilder check` shows no world issues and every area map is linked from WORLD.md.

## Step 4: Router skill and trailhead

1. Write `.claude/skills/world/SKILL.md` from the template. Its description names the areas in the words the project uses.
2. Draft the trailhead block. Show the user the target file and the block, and wait for a yes. Then insert it near the top of that file, replacing any existing `worldbuilder:start` block.

Done when `worldbuilder check` shows `world/WORLD.md` at hop 1 from the trailhead file.

## Step 5: Check

Run `worldbuilder check` and read it as the before/after picture of the project's roads:

- reach percentages, and files deeper than `max_hops`
- unreachable directories
- dead links and dead heading anchors in the project's own files
- orphans
- stale or uncovered files

Fix anything inside `world/`. Summarize the rest for the user in a short list, largest first. Those are the broken roads in their territory.

## Step 6: Eval

Follow [references/eval.md](references/eval.md). Report the per-arm table, then each world-arm miss diagnosed as missing knowledge, broken road, weak entry, or bad probe, with the fix for each.

## Finish

Report in under 15 lines:

- the areas mapped
- WORLD.md and map line counts
- reach before and after the trailhead block
- the eval result, with its run count and noise caveat
- the top fixes the user should consider

`world/.survey.json`, `world/.check.json`, and `world/.eval/` are working files. Tell the user they can gitignore them.
