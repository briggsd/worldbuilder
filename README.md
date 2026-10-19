# worldbuilder

A Claude Code plugin that builds a **world** for a project: a wide, shallow map of what exists and where, reached from the project's trailhead, so agents find existing work before they rebuild it.

It implements the world-building model from OpenRig's [How My AI Civilization Actually Works](https://www.youtube.com/watch?v=CYRJDTcTKhQ). Agents fail at onboarding before they search, because they don't know what to search for. The fix is a map that names everything at shallow depth (width for depth), with a traceable route from boot to every piece of knowledge (route-to-leaf reachability).

## The model, and what worldbuilder builds

The OpenRig model arranges a project's knowledge along four dimensions. worldbuilder builds the first three.

| Dimension | Question it answers | Status |
|---|---|---|
| Map (ontology) | What exists, and where? | Built: WORLD.md and the area maps |
| Navigation (topology) | How does an agent get from boot to it? | Built: trailhead, router skill, links, and `worldbuilder check` |
| Elevation (epistemology) | How established is it? Canon, insight, field note, observation, raw data | Built: level tags on entries and Canon sections. See [Elevation](#elevation-the-levels-of-knowledge) |
| Time and lore | What happened, and what did we learn from it? | Not built yet. See [Lore](#lore) |

## What it builds: the layers of the map

The map has five layers. Each one is wider and shallower than the files it points to, and each links down to the next, so an agent can walk from boot to any file in the project in a few hops.

| Layer | Path | Size | Job |
|---|---|---|---|
| 1. Trailhead | Marked block in `CLAUDE.md` or `AGENTS.md` | 4 lines | Tells every new session the map exists. Applied only after you approve it |
| 2. Router skill | `.claude/skills/world/SKILL.md` | Description under 60 words | Keeps the map findable mid-session and after compaction, when the trailhead has scrolled out of context |
| 3. World page | `world/WORLD.md` | At most 140 lines | The whole project on one page: project-wide canon, every area, its landmarks, the highways between areas, and the edges |
| 4. Area maps | `world/<area>.md` | At most 120 lines each | Every entity in one area, one line each, linked to its file or heading |
| 5. Territory | The project's own files | Unchanged | Where the detail lives. The world never copies it |

### 1. Trailhead

The entry point. Claude Code loads `CLAUDE.md` at the start of every session, and many other agents load `AGENTS.md`, so a short block there is the one pointer every agent sees. It names `world/WORLD.md` and the `world` skill, and says to read the map before creating anything. The `<!-- worldbuilder:start -->` and `<!-- worldbuilder:end -->` markers let a rebuild replace the block and let the eval strip it for the baseline.

### 2. Router skill

A skill named `world` whose description starts "Map of <project>" and names the areas in the words people use. Skill descriptions stay in context for the whole session, so the agent can still reach the map after the trailhead has been compacted away. The skill body is three steps: read WORLD.md, open the area map, and search the project when the map has nothing.

### 3. World page

`WORLD.md` is the top of the map. It has five parts:

- **How to use this map**: four rules for the agent reading it, including how to read level tags.
- **Canon**: the rules that hold across areas. See [Elevation](#elevation-the-levels-of-knowledge).
- **Areas**: a table with one row per area map, a one-line description, and 2 to 4 landmark links, so an agent can jump straight to the most important files.
- **Highways**: 3 to 8 routes that cross areas, such as a workflow, a data flow, or a pipeline. Each one names its start and its end. In a code repo, "add a resource type" runs from the model through the service and the API to the UI.
- **Edges**: what the map leaves out on purpose (generated output, archives, vendored code, migrations) and how to search it.

### 4. Area maps

One map per area agreed during the survey. Each map has the same sections:

- **Landmarks**: the 3 to 7 things an agent most needs to know exist here. Each one has a "Use when" line phrased as the task someone would ask for. That line is what stops an agent rebuilding the entity.
- **Canon**: the rules for working in this area, each with its source and evidence.
- **Everything else**: one line per remaining entity, grouped under subheadings when there are more than 15.
- **Routes out**: links to other area maps, and why a task here leads there.
- **Edges**: files the area covers but doesn't list one by one, and how to find things in them.

The frontmatter's `covers` lists the paths the map is responsible for. `worldbuilder check` uses it to flag a stale map and to count files no map covers.

### 5. Territory

The project's own files. An entry says only what exists, where, and when you'd need it. How a thing works stays in its file. This is **width for depth**: the map names everything and explains little, so it stays small enough to read in full and cheap to keep current.

### Walking the layers

An agent asked to "add a debug level to app log entries" in a large repo:

1. reads the trailhead in `AGENTS.md`,
2. opens `world/WORLD.md` and picks the shared-types area from the table,
3. opens `world/shared-types.md` and finds the log-type entry,
4. opens the enum file the entry links to and extends it instead of writing a new one.

`worldbuilder check` measures this walk: how much of the project is reachable by links from the trailheads, and in how many hops.

Everything is plain markdown, readable in an editor, GitHub, or Obsidian. The exact templates are in [skills/worldbuilder/references/world-format.md](skills/worldbuilder/references/world-format.md).

## Elevation: the levels of knowledge

The map tells an agent what exists. Elevation tells it how far to trust it. Knowledge matures upward through five levels:

| Level | What it is | Examples |
|---|---|---|
| Canon | What the project treats as established. Agents follow it without re-deriving it | A rule in `AGENTS.md` ("generate Postgres migrations, never hand-write them"), an accepted decision record, a settled convention |
| Insight | A lesson worth sharing with the whole team, drawn from several notes | A concept in a topic doc, a pattern named in a design doc |
| Field note | A written-up finding from one piece of work | A capture note, a postmortem, a PR description |
| Observation | One thing seen once, not yet confirmed | A line in a session log, a review comment, a "this looks stale" flag |
| Raw data | Material nobody has distilled | Logs, transcripts, and the markdown exhaust agents generate |

Two rules govern the ladder:

- **Canon measures how established something is, not how old it is.** A new discovery can become canon at once, while an old pattern can stay a field note because it only applies sometimes.
- **Higher levels rest on lower ones.** A piece of canon should link down to the insights and observations that justify it, so an agent can check why a rule exists before it bends it.

Without elevation every map entry looks equally trustworthy, and an agent can't tell a stale design note from a rule it must follow. worldbuilder adds elevation in three places:

- **Level tags.** Every map entry that points at prose carries a tag after its name: `- **Migration guide** [observation]: ...`. Code and config entries carry none. A doc the code contradicts is tagged `[observation]` and names what supersedes it.
- **Canon sections.** Each area map and WORLD.md has a `## Canon` section. Each rule is one instruction with a `Source:` link to where it is stated and an `Evidence:` link to the code, tests, CI, or examples that enforce it. Rules are chosen for the traps they prevent: the cases where a stale doc or the obvious approach points the other way.
- **Checks.** `worldbuilder check` counts tags per level and flags any canon rule that cites no evidence.

Cartographers assign levels by evidence, not tone. A rule is canon when a rules file states it, code or CI enforces it, or every example follows it. To add elevation to a world built before it existed, run the cartographers in `mode: elevate`.

## Lore

Lore is the fourth dimension: named stories of real failures, passed from one generation of agents to the next. One good story carries a lesson into situations no rule anticipated, and its name works as a shorthand. The OpenRig example is the "doghouse moonbase": an agent asked for a doghouse made one reasonable decision after another and built a moonbase. Saying "moonbase" brings the whole lesson back without retelling it.

worldbuilder builds no lore yet. The plan is a `world/lore/` folder of short, addressable stories, each linked from the area maps where the failure happens and taught again after compaction.

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

Canon probes (`"kind": "canon"`) test elevation. Each hands over work that an established rule governs, where a stale doc or older pattern points another way. The score is whether the agent followed the rule (touched the files it requires, wrote what it requires) or was misled (touched the path it rules out).

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
