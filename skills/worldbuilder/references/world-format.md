# World format

Every file below lives in the target project. All of it is plain markdown a human can read and edit.

The governing rule is **width for depth**: name everything, explain little. An entry says what exists, where it is, and when you'd need it. How it works stays in the territory (the files the entry links to).

## Links

Use the style `survey.link_style` reports, so the map renders where the human already reads the project.

- `wiki`: `[[path/to/file#Heading|label]]`, path from the project root, no `.md`.
- `markdown`: `[label](../path/to/file.md#heading-slug)`, relative to `world/`.

Link to the heading when one file holds several entities. Every link must resolve. `worldbuilder check` lists the ones that don't as broken roads.

## Elevation

Elevation says how established a piece of knowledge is, so an agent knows what to follow and what to treat as a lead. Every entry whose target is prose knowledge (a doc, README, note, decision, convention, rule file, log) carries one level tag right after its bold name: `- **Entity** [insight]: ...`. Entries for code, config, and assets carry no tag, because code is what it is.

| Tag | Level | Assign it when |
|---|---|---|
| `[canon]` | Canon | The project treats it as established: a rule file agents must follow, an accepted decision, a convention that code, CI, or tests enforce |
| `[insight]` | Insight | A lesson or pattern drawn from several pieces of work and written for the whole team |
| `[note]` | Field note | A written-up finding from one piece of work: a design doc, capture, postmortem, a README describing one component |
| `[observation]` | Observation | Seen once and unconfirmed, or stale: contradicted by canon, describing code that no longer exists, or outdated. Add "superseded by <link>" when canon replaces it |
| `[data]` | Raw data | Undistilled material: logs, transcripts, generated reports, session exhaust |

Canon measures how established something is, not how old it is. Judge by evidence: a rule written in a trailhead or rules file, enforced by code (a registry, a lint rule, a test, a CI check), or followed by every example in the territory. When a doc and the code disagree, the code wins, and the doc is an observation.

### Canon section

Each area map, and WORLD.md for project-wide rules, has a `## Canon` section listing the rules an agent must follow when working there. Each rule is one line:

```markdown
- **<Rule name>**: <the rule, as an instruction>. Source: <link to where it is stated>. Evidence: <links to the code, tests, CI, or examples that enforce or follow it>.
```

Every canon rule cites evidence, so an agent can see why the rule holds before it bends it. `worldbuilder check` flags a rule with no `Evidence:` link. Prefer rules an agent would get wrong without being told: the ones where a stale doc, an older pattern, or the obvious approach points the other way. Name that trap in the rule ("not the `migration-create.sh` script, which writes to a path that no longer exists"). Leave out rules the trailhead already states word for word, and link to the trailhead instead. An area with no canon says "None found." under the heading.

## world/WORLD.md (at most 140 lines)

```markdown
---
world: <project name>
built: <survey "generated" timestamp>
generator: worldbuilder <version>
---

# <Project> world map

<Two sentences: what this project is and what kind of work happens in it.>

## How to use this map

- Each area below has its own map. Open the one your task touches before you create anything, and extend what exists.
- An entry tells you something exists and where. Open the file it links to for how it works.
- When the map has nothing on your task, search the project, and tell the human what the map missed.
- Tags give each doc's level: `[canon]` rules are established, so follow them over anything lower. `[insight]` and `[note]` are reliable leads. `[observation]` and `[data]` are unconfirmed or stale, so check them against the code first.

## Canon

<Project-wide rules in the Canon section format, 3-10 lines.>

## Areas

| Area | What lives there | Landmarks |
|---|---|---|
| <link to world/<id>> | <one line> | <2-4 links to the area's most important entities> |

## Highways

<3-8 bullets. The routes that cross areas: a workflow, a data flow, a pipeline. Each names its start, its end, and links both.>

## Edges

<What this map leaves out (generated output, archives, imports, vendored code) and how to search it.>
```

## world/<area-id>.md (at most 120 lines)

```markdown
---
area: <area id>
title: <area name>
covers: [<path>, <path>]
built: <survey "generated" timestamp>
---

# <Area name>

<One or two sentences: what this area is for and when an agent needs it.>

## Landmarks

<The 3-7 things an agent most needs to know exist here.>
- **<Entity>** [<level>, prose only]: <what it is, in under 20 words>. <link>. Use when: <the task that should lead here>.

## Canon

<The rules for working in this area, in the Canon section format. "None found." when there are none.>

## Everything else

<One line per remaining entity. Group under ### subheadings when there are more than 15.>
- **<Entity>**: <what it is>. <link>

## Routes out

- <link to another area map>: <why a task here leads there>.

## Edges

<Files in `covers` that are not mapped one by one (generated output, archives, raw data) and how to find things in them.>
```

`covers` lists the directories (or files) this map is responsible for. `worldbuilder check` uses it to flag the map as stale when a covered file changes after `built`, and to count files no map covers.

An entity is anything an agent could rebuild by mistake or needs to find: a system, a workflow, a decision, a convention, a reference doc, a tool, a template, a person or team note. The "Use when" line is the part that prevents rebuilding, so phrase it as the task someone would ask for, in their words.

## Router skill: <project>/.claude/skills/world/SKILL.md

```markdown
---
name: world
description: Map of <project>: what exists and where, across <4-8 area names>. Read before adding, building, or changing anything here, when looking for existing work, or when unsure where something lives.
---

# <Project> world map

1. Read [world/WORLD.md](../../../world/WORLD.md).
2. Open the map for the area your task touches. Follow its Canon rules, then open the files its entries link to.
3. When the map has nothing on your task, search the project. Report any existing work the map missed, so the map can be fixed.
```

The description is the pointer that has to win mid-session, after compaction, when the trailhead has scrolled away. Lead with "Map of <project>", name the areas in the words people use, and keep it under 60 words.

## Trailhead block

Patch the root `CLAUDE.md` if it exists, otherwise the root `AGENTS.md`, otherwise create `CLAUDE.md`. Put the block near the top, after the title. The markers let the eval build a baseline without it and let a rebuild replace it.

The block carries the project-wide canon itself, because the trailhead is the one file every agent reads. On a large project agents read the trailhead and often skip the map, so a rule that lives only in WORLD.md or an area map rarely reaches them. Keep the block under 15 lines.

```markdown
<!-- worldbuilder:start -->
## World map

This project has a map of what exists and where: <link to world/WORLD.md> (also the `world` skill). Before creating or changing anything, open the area map for that part of the project and follow its Canon rules. Those rules are where stale docs and older patterns point the wrong way.

Rules that hold everywhere (sources and evidence in <link to WORLD.md#canon>):

- <one WORLD.md canon rule as a single instruction, naming the files or command it requires, no links>
<!-- worldbuilder:end -->
```

Take the rules from WORLD.md's Canon section, most costly trap first, at most 8. Leave out rules the trailhead already states outside the block.

### Trailhead conflicts

The trailhead outranks every map, so a stale line in it misleads agents even when a map has the right rule. worldbuilder never edits the trailhead outside its block. When a line outside the block is contradicted by the code, list it for the user with the evidence, so they can fix it.

## world/config.json (optional)

```json
{"exclude": ["generated/"], "trailheads": [], "max_hops": 3, "eval_exclude": ["_templates/"],
 "areas": [{"id": "core", "title": "Core", "covers": ["src/core"]}]}
```

`exclude` removes paths from the territory entirely. `trailheads` overrides the defaults (root `CLAUDE.md`/`AGENTS.md` and every `.claude/skills/*/SKILL.md`). `areas` records the confirmed area list so a refresh reuses it.
