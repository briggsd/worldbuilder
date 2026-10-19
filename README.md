# worldbuilder

A Claude Code plugin that builds a **world** for a project: a wide, shallow map of what exists and where, reached from the project's trailhead, so agents find existing work before they rebuild it.

It implements the world-building model from OpenRig's [How My AI Civilization Actually Works](https://www.youtube.com/watch?v=CYRJDTcTKhQ). Agents fail at onboarding before they search, because they don't know what to search for. The fix is a map that names everything at shallow depth (width for depth), with a traceable route from boot to every piece of knowledge (route-to-leaf reachability).

## What it builds

In the target project:

| Path | What it is |
|---|---|
| `world/WORLD.md` | One page naming every area, its landmarks, the highways between areas, and the edges of the map |
| `world/<area>.md` | One map per area. Every entry links to a real file or heading and says when you'd need it |
| `.claude/skills/world/SKILL.md` | A router skill whose description keeps the map discoverable mid-session and after compaction |
| A marked block in `CLAUDE.md` or `AGENTS.md` | The trailhead pointer. Applied only after you approve it |

Everything is plain markdown, readable in an editor, GitHub, or Obsidian.

## Install

```
claude plugin marketplace add ~/workspace/worldbuilder
claude plugin install worldbuilder@worldbuilder
```

Or for one session: `claude --plugin-dir ~/workspace/worldbuilder`.

## Use

In the project, ask Claude to build a world map (or invoke `/worldbuilder:worldbuilder`). It surveys the project, agrees areas with you, maps each area with parallel subagents, writes WORLD.md and the router skill, proposes the trailhead block, checks the roads, and runs the eval if you agree to the cost. Ask again later to refresh: only stale or changed areas are remapped.

The CLI is on the agent's PATH while the plugin is loaded:

| Command | What it does |
|---|---|
| `worldbuilder survey` | Lists the territory (git-aware), parses headings and links, proposes areas. Writes `world/.survey.json` |
| `worldbuilder check` | Follows links from the trailheads. Reports reach, hop depth, unreachable directories, dead links and heading anchors, orphans, stale maps, uncovered files, and broken roads in the world itself. `--strict` exits 1 on world problems |
| `worldbuilder eval sample` | Picks random existing targets across areas, from the survey rather than the maps |
| `worldbuilder eval prepare` | Copies the project outside itself into a `world` arm and a `baseline` arm without the world |
| `worldbuilder eval run` | Runs each probe in both arms with headless `claude -p`, build tasks in per-run clones. Resumable |
| `worldbuilder eval score` | Scores runs, writes `report.md` and `summary.json` |

## The eval

The eval reproduces the failure the world prevents: an agent handed work never thinks to look, and rebuilds what exists. Each probe is a build task ("draft…", "set up…", "write a script that…") whose right starting point already exists in the project. Nobody tells the agent to look. Each task runs in a copy with the world and a copy without it, each run in its own copy-on-write clone so writes never leak between runs. The score comes from the tool trace: did the agent open the existing work (found), did it create files without opening it (rebuilt), and did it use the map. The report also gives a first-pass diagnosis of each world-arm miss.

The older find probes (`"kind": "find"`) ask whether something exists. Asking primes every agent to search, so they mostly measure grep.

Runs use `--setting-sources project,local` by default so your user plugins and settings don't add noise. Pass `--user-settings` to include them.

## Known limits

- Reachability follows links only. An agent can still find an unlinked file by search, so "unreachable" means no road, not invisible.
- Staleness compares file modification times with each map's `built` time, so touching a file without changing it marks its map stale.
- Wiki-link resolution follows Obsidian's rules closely but not exactly (it picks the shortest matching path for a bare name).
- Small evals are noisy. With about 12 probes and one trial, one or two probes of difference means nothing.

## Develop

```
python3 -m unittest tests/test_worldbuilder.py -v
claude plugin validate .
```
