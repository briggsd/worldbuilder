# World format

Every file below lives in the target project. All of it is plain markdown a human can read and edit.

The governing rule is **width for depth**: name everything, explain little. An entry says what exists, where it is, and when you'd need it. How it works stays in the territory (the files the entry links to).

## Links

Use the style `survey.link_style` reports, so the map renders where the human already reads the project.

- `wiki`: `[[path/to/file#Heading|label]]`, path from the project root, no `.md`.
- `markdown`: `[label](../path/to/file.md#heading-slug)`, relative to `world/`.

Link to the heading when one file holds several entities. Every link must resolve. `worldbuilder check` lists the ones that don't as broken roads.

## world/WORLD.md (at most 120 lines)

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

## Areas

| Area | What lives there | Landmarks |
|---|---|---|
| <link to world/<id>> | <one line> | <2-4 links to the area's most important entities> |

## Highways

<3-8 bullets. The routes that cross areas: a workflow, a data flow, a pipeline. Each names its start, its end, and links both.>

## Edges

<What this map leaves out (generated output, archives, imports, vendored code) and how to search it.>
```

## world/<area-id>.md (at most 100 lines)

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
- **<Entity>**: <what it is, in under 20 words>. <link>. Use when: <the task that should lead here>.

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
2. Open the map for the area your task touches, then the files its entries link to.
3. When the map has nothing on your task, search the project. Report any existing work the map missed, so the map can be fixed.
```

The description is the pointer that has to win mid-session, after compaction, when the trailhead has scrolled away. Lead with "Map of <project>", name the areas in the words people use, and keep it under 60 words.

## Trailhead block

Patch the root `CLAUDE.md` if it exists, otherwise the root `AGENTS.md`, otherwise create `CLAUDE.md`. Put the block near the top, after the title. The markers let the eval build a baseline without it and let a rebuild replace it.

```markdown
<!-- worldbuilder:start -->
## World map

This project has a map of what exists and where: <link to world/WORLD.md> (also the `world` skill). Read it before creating anything new, so you extend existing work instead of rebuilding it.
<!-- worldbuilder:end -->
```

## world/config.json (optional)

```json
{"exclude": ["generated/"], "trailheads": [], "max_hops": 3, "eval_exclude": ["_templates/"],
 "areas": [{"id": "core", "title": "Core", "covers": ["src/core"]}]}
```

`exclude` removes paths from the territory entirely. `trailheads` overrides the defaults (root `CLAUDE.md`/`AGENTS.md` and every `.claude/skills/*/SKILL.md`). `areas` records the confirmed area list so a refresh reuses it.
