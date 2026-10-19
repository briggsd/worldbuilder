import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

WB = str(Path(__file__).resolve().parents[1] / "bin" / "worldbuilder")
wb = SourceFileLoader("worldbuilder", WB).load_module()

STUB = """#!/usr/bin/env python3
import json, os, sys
q = sys.stdin.read()
arm = os.path.basename(os.getcwd())
if "NEGATIVE" in q:
    ans = {"existing": arm != "world", "found": [], "answer": "x"}
else:
    ans = {"existing": True, "found": ["notes/b.md#Section"] if arm == "world" else ["lonely/c.md"], "answer": "x"}
print(json.dumps({"result": "I looked around.\\n" + json.dumps(ans), "total_cost_usd": 0.01, "num_turns": 3,
                  "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 100,
                            "cache_creation_input_tokens": 0}}))
"""

TASK_STUB = """#!/usr/bin/env python3
import json, os, sys
q = sys.stdin.read()
cwd = os.path.realpath(os.getcwd())
world = "-world-" in os.path.basename(cwd)
calls = []
if world:
    calls += [("Skill", {"skill": "world"}), ("Read", {"file_path": cwd + "/world/WORLD.md"})]
    if "b thing" in q:
        calls.append(("Read", {"file_path": cwd + "/notes/b.md"}))
else:
    calls.append(("Read", {"file_path": cwd + "/notes/a.md"}))
    open(os.path.join(cwd, "new.md"), "w").write("rebuilt")
    calls.append(("Write", {"file_path": cwd + "/new.md", "content": "rebuilt"}))
calls.append(("Write", {"file_path": "/tmp/elsewhere.md", "content": "x"}))
for name, inp in calls:
    print(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}))
print(json.dumps({"type": "result", "result": "done", "total_cost_usd": 0.02, "num_turns": len(calls),
                  "usage": {"input_tokens": 1, "output_tokens": 1}}))
"""


class WorldbuilderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "proj"
        self.root.mkdir()
        self.write("CLAUDE.md", "# Project\n\nStart at [[notes/a]]. Code lives in [code](code/).\n")
        self.write("notes/a.md", "# A\n\n## Overview\n\nSee [b](b.md#Section) and [gone](missing.md) and [bad](b.md#Missing).\n"
                                 "```\n[[notes/in-fence]]\n```\n")
        self.write("notes/b.md", "---\ntitle: B\n---\n# B\n\n## Section\n\nBody about b.\n")
        self.write("notes/CLAUDE.md", "# Notes rules\n")
        self.write("lonely/c.md", "# C\n\n## Thing\n\nNobody links here.\n")
        self.write("code/x.py", "print(1)\n")
        self.write("node_modules/dep.js", "x\n")
        self.git("init", "-q")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def git(self, *a):
        subprocess.run(["git", *a], cwd=self.root, check=True, capture_output=True)

    def wb(self, *a, check=True, env=None):
        r = subprocess.run([sys.executable, WB, *a], cwd=self.root, capture_output=True, text=True,
                           env={**os.environ, **(env or {})})
        if check and r.returncode != 0:
            self.fail(f"worldbuilder {' '.join(a)} failed: {r.stderr}")
        return r

    def check(self, *a):
        return json.loads(self.wb("check", "--json", *a).stdout)

    def add_world(self, built="2000-01-01T00:00:00+00:00", map_body="- **B**: b. [[notes/b#Section]]\n"):
        self.write("world/WORLD.md", "# World\n\n| Area | x |\n|---|---|\n| [[world/notes]] | notes |\n")
        self.write("world/notes.md", f"---\narea: notes\ncovers: [notes]\nbuilt: {built}\n---\n# Notes\n\n{map_body}")

    # ------------------------------------------------------------ survey

    def test_survey_lists_territory_and_excludes(self):
        self.wb("survey")
        s = json.loads((self.root / "world" / ".survey.json").read_text())
        paths = {f["path"] for f in s["files"]}
        self.assertIn("notes/a.md", paths)
        self.assertNotIn("node_modules/dep.js", paths)
        self.assertEqual(s["trailheads"], ["CLAUDE.md"])
        self.assertEqual({a["path"] for a in s["areas"]}, {".", "code", "lonely", "notes"})
        b = next(f for f in s["files"] if f["path"] == "notes/b.md")
        self.assertEqual(b["title"], "B")
        self.assertEqual(b["links_in"], 2)  # two links from a.md

    def test_survey_splits_large_directories(self):
        for i in range(5):
            self.write(f"big/one/f{i}.md", "# x\n")
            self.write(f"big/two/f{i}.md", "# x\n")
        areas = {a["path"] for a in wb.propose_areas(wb.list_files(self.root, wb.DEFAULT_EXCLUDES), max_files=6)}
        self.assertIn("big/one", areas)
        self.assertIn("big/two", areas)

    # ------------------------------------------------------------ check

    def test_check_reach_dead_links_and_anchors(self):
        r = self.check()
        self.assertEqual(r["hops"], {"0": 1, "1": 2, "2": 1})  # CLAUDE.md; a + notes/CLAUDE.md; b
        self.assertEqual(r["unreachable"], {"lonely": ["lonely/c.md"]})
        self.assertEqual([d["target"] for d in r["dead_links"]], ["missing.md"])
        self.assertEqual([d["anchor"] for d in r["dead_anchors"]], ["Missing"])
        self.assertIn("lonely/c.md", r["orphans"])
        self.assertIsNone(r["world"])

    def test_directory_link_covers_files(self):
        r = self.check()
        all_unreachable = [f for fs in r["unreachable"].values() for f in fs]
        self.assertNotIn("code/x.py", all_unreachable)

    def test_links_in_code_fences_are_ignored(self):
        r = self.check()
        self.assertNotIn("notes/in-fence", [d["target"] for d in r["dead_links"]])

    def test_world_stale_and_issues(self):
        self.add_world()
        r = self.check()
        m = r["world"]["maps"][0]
        self.assertEqual(m["map"], "world/notes.md")
        self.assertGreater(m["changed_since_built"], 0)
        self.assertEqual(r["world"]["issues"], [])
        self.assertIn("lonely/c.md", r["world"]["uncovered"])

    def test_world_fresh_map_is_not_stale(self):
        self.add_world(built=wb.now_iso())
        time.sleep(0.01)
        r = self.check()
        self.assertEqual(r["world"]["maps"][0]["changed_since_built"], 0)

    def test_eval_reports_are_not_area_maps(self):
        self.add_world()
        self.write("world/.eval/report-2026-01-01.md", "# worldbuilder eval\n")
        r = self.check()
        self.assertEqual([m["map"] for m in r["world"]["maps"]], ["world/notes.md"])
        self.assertEqual(r["world"]["issues"], [])

    def test_world_broken_road_fails_strict(self):
        self.add_world(map_body="- **Ghost**: gone. [[notes/ghost]]\n")
        self.assertEqual(self.wb("check", "--strict", check=False).returncode, 1)
        self.add_world()
        self.assertEqual(self.wb("check", "--strict", check=False).returncode, 0)

    def test_world_missing_frontmatter_is_an_issue(self):
        self.add_world()
        self.write("world/notes.md", "# Notes\n")
        r = self.check()
        self.assertTrue(any("frontmatter missing" in i for i in r["world"]["issues"]))

    def test_map_name_colliding_with_project_link_is_an_issue(self):
        self.add_world()
        self.write("lonely/c.md", "# C\n\nSee [[notes]] for more.\n")
        r = self.check()
        self.assertTrue(any("name collision" in i for i in r["world"]["issues"]))

    def test_trailhead_block_puts_world_at_hop_one(self):
        self.add_world()
        self.write("CLAUDE.md", f"# P\n{wb.MARK_START}\nSee [[world/WORLD]].\n{wb.MARK_END}\n")
        r = self.check()
        self.assertEqual(r["trailheads"], ["CLAUDE.md"])
        report = wb.reach(*self._graph_for_reach())
        self.assertEqual(report[0]["world/WORLD.md"], 1)

    def _graph_for_reach(self):
        files = wb.list_files(self.root, wb.DEFAULT_EXCLUDES)
        _, _, edges = wb.build_graph(self.root, files)
        return files, edges, ["CLAUDE.md"]

    # ------------------------------------------------------------ resolver

    def test_wiki_resolution_by_name_and_suffix(self):
        idx = wb.Index(["notes/b.md", "deep/x/notes/b.md", "Projects/p/CLAUDE.md"])
        self.assertEqual(idx.resolve("a.md", {"kind": "wiki", "target": "b"}), ("file", "notes/b.md"))
        self.assertEqual(idx.resolve("a.md", {"kind": "wiki", "target": "x/notes/b"}), ("file", "deep/x/notes/b.md"))
        self.assertEqual(idx.resolve("a.md", {"kind": "wiki", "target": "Projects/p/CLAUDE"}), ("file", "Projects/p/CLAUDE.md"))
        self.assertEqual(idx.resolve("a.md", {"kind": "wiki", "target": "Projects/p"}), ("dir", "Projects/p"))
        self.assertEqual(idx.resolve("a.md", {"kind": "wiki", "target": "nope"})[0], "dead")
        self.assertEqual(idx.resolve("a.md", {"kind": "md", "target": "https://x.y"})[0], "external")

    # ------------------------------------------------------------ eval

    def test_prepare_strips_world_from_baseline(self):
        self.add_world()
        self.write(".claude/skills/world/SKILL.md", "---\nname: world\ndescription: map\n---\n")
        self.write("CLAUDE.md", f"# P\n{wb.MARK_START}\nSee [[world/WORLD]].\n{wb.MARK_END}\nkeep me\n")
        out = Path(self.tmp.name) / "eval"
        self.wb("eval", "prepare", "--out", str(out))
        self.assertTrue((out / "world/world/WORLD.md").exists())
        self.assertTrue((out / "world/.claude/skills/world/SKILL.md").exists())
        self.assertFalse((out / "baseline/world").exists())
        self.assertFalse((out / "baseline/.claude/skills/world").exists())
        base = (out / "baseline/CLAUDE.md").read_text()
        self.assertNotIn("worldbuilder", base)
        self.assertIn("keep me", base)

    def test_prepare_keeps_gitignored_router(self):
        self.add_world()
        self.write(".gitignore", ".claude/\n")
        self.write(".claude/skills/world/SKILL.md", "---\nname: world\ndescription: map\n---\n")
        self.write(".claude/settings.local.json", "{}\n")
        out = Path(self.tmp.name) / "eval"
        self.wb("eval", "prepare", "--out", str(out))
        self.assertTrue((out / "world/.claude/skills/world/SKILL.md").exists())
        self.assertFalse((out / "world/.claude/settings.local.json").exists())

    def test_prepare_rejects_out_inside_project(self):
        self.add_world()
        r = self.wb("eval", "prepare", "--out", str(self.root / "x"), check=False)
        self.assertEqual(r.returncode, 2)

    def test_sample_is_deterministic(self):
        self.wb("survey")
        self.wb("eval", "sample", "--n", "2", "--seed", "7")
        a = (self.root / "world/.eval/targets.json").read_text()
        self.wb("eval", "sample", "--n", "2", "--seed", "7")
        self.assertEqual(a, (self.root / "world/.eval/targets.json").read_text())
        t = json.loads(a)["targets"]
        self.assertEqual(len(t), 2)
        self.assertNotIn("CLAUDE.md", [x["path"] for x in t])

    def test_sample_skips_binary_files(self):
        for i in range(6):
            (self.root / f"code/blob{i}.zip").write_bytes(b"PK\x03\x04\x00\x00binary")
        self.wb("survey")
        self.wb("eval", "sample", "--n", "20", "--seed", "1")
        paths = [x["path"] for x in json.loads((self.root / "world/.eval/targets.json").read_text())["targets"]]
        self.assertIn("code/x.py", paths)
        self.assertFalse([p for p in paths if p.endswith(".zip")])

    def test_run_and_score_with_stub(self):
        self.add_world()
        out = Path(self.tmp.name) / "eval"
        self.wb("eval", "prepare", "--out", str(out))
        stub = Path(self.tmp.name) / "claude-stub"
        stub.write_text(STUB)
        stub.chmod(0o755)
        probes = Path(self.tmp.name) / "probes.json"
        probes.write_text(json.dumps({"probes": [
            {"id": "p01", "question": "how do I do b?", "expect": ["notes/b.md"], "negative": False},
            {"id": "n01", "question": "NEGATIVE thing", "expect": [], "negative": True}]}))
        env = {"WORLDBUILDER_CLAUDE": str(stub)}
        self.wb("eval", "run", "--dir", str(out), "--probes", str(probes), "--jobs", "2", env=env)
        self.assertEqual(len(list((out / "results").glob("*.json"))), 4)
        again = self.wb("eval", "run", "--dir", str(out), "--probes", str(probes), env=env)
        self.assertIn("0 runs to do", again.stdout)
        self.wb("eval", "score", "--dir", str(out), "--probes", str(probes))
        s = json.loads((out / "summary.json").read_text())
        self.assertEqual(s["present"], 4)
        self.assertEqual(s["arms"]["world"]["accuracy_pct"], 100.0)
        self.assertEqual(s["arms"]["baseline"]["accuracy_pct"], 0.0)
        self.assertEqual(s["arms"]["world"]["mean_tokens"], 115)

    def test_task_runs_are_isolated_and_scored_from_the_trace(self):
        self.add_world()
        out = Path(self.tmp.name) / "eval"
        self.wb("eval", "prepare", "--out", str(out))
        stub = Path(self.tmp.name) / "claude-task-stub"
        stub.write_text(TASK_STUB)
        stub.chmod(0o755)
        probes = Path(self.tmp.name) / "probes.json"
        probes.write_text(json.dumps({"probes": [
            {"id": "p01", "kind": "task", "task": "Write up the b thing for the team.", "expect": ["notes/b.md"]},
            {"id": "p02", "kind": "task", "task": "Summarize the lonely note.", "expect": ["lonely/c.md"]}]}))
        env = {"WORLDBUILDER_CLAUDE": str(stub)}
        self.wb("eval", "run", "--dir", str(out), "--probes", str(probes), "--jobs", "2", env=env)
        self.assertFalse((out / "baseline/new.md").exists())
        self.assertFalse(list((out / "work").iterdir()))
        rec = json.loads((out / "results/p01-baseline-1.json").read_text())
        self.assertTrue(rec["workdir"].endswith("p01-baseline-1"))
        self.wb("eval", "score", "--dir", str(out), "--probes", str(probes))
        s = json.loads((out / "summary.json").read_text())["kinds"]["task"]
        self.assertEqual((s["world"]["correct"], s["world"]["map_used"], s["world"]["rebuilt"]), (1, 2, 0))
        self.assertEqual((s["baseline"]["correct"], s["baseline"]["map_used"], s["baseline"]["rebuilt"]), (0, 0, 2))
        report = (out / "report.md").read_text()
        self.assertIn("p02: missing knowledge", report)

    def test_task_score_counts_shell_reads_and_edits_of_the_target(self):
        def run(*calls):
            lines = [json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": n, "input": i}]}}) for n, i in calls]
            lines.append(json.dumps({"type": "result", "num_turns": 1}))
            return {"workdir": "/w", "stdout": "\n".join(lines)}
        p = {"id": "p01", "kind": "task", "expect": ["docs/My Note.md"]}
        s = wb.score_task_run(p, run(("Bash", {"command": "cat world/WORLD.md docs/My\\ Note.md"})))
        self.assertEqual((s["found"], s["map_used"]), (True, True))
        s = wb.score_task_run(p, run(("Bash", {"command": "ls networld/x"})))
        self.assertEqual((s["found"], s["map_used"]), (False, False))
        s = wb.score_task_run(p, run(("Edit", {"file_path": "/w/docs/My Note.md"})))
        self.assertTrue(s["found"])
        s = wb.score_task_run(p, run(("Write", {"file_path": "/w/new.md"})))
        self.assertEqual((s["found"], s["rebuilt"]), (False, True))

    def test_canon_score_needs_the_rule_followed_and_the_stale_path_avoided(self):
        def run(*calls):
            lines = [json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": n, "input": i}]}}) for n, i in calls]
            lines.append(json.dumps({"type": "result", "num_turns": 1}))
            return {"workdir": "/w", "stdout": "\n".join(lines)}
        p = {"id": "c01", "kind": "canon", "expect": ["db/Index.ts"], "avoid": ["Model/Migrations"],
             "require_text": [r"AddColumn"], "avoid_text": [r"synchronize:\s*true"]}
        reg = ("Edit", {"file_path": "/w/db/Index.ts", "new_string": "import AddColumn"})
        s = wb.score_task_run(p, run(reg))
        self.assertEqual((s["followed"], s["misled"], s["correct"]), (True, False, True))
        s = wb.score_task_run(p, run(("Read", {"file_path": "/w/db/Index.ts"})))
        self.assertEqual((s["followed"], s["correct"]), (False, False))
        s = wb.score_task_run(p, run(reg, ("Write", {"file_path": "/w/Model/Migrations/1.ts", "content": "x"})))
        self.assertEqual((s["followed"], s["misled"], s["correct"]), (True, True, False))
        s = wb.score_task_run(p, run(reg, ("Edit", {"file_path": "/w/db/Config.ts", "new_string": "synchronize: true"})))
        self.assertEqual((s["misled"], s["correct"]), (True, False))

    def test_check_reports_elevation_and_unsupported_canon(self):
        self.add_world(map_body="- **B** [note]: b. [[notes/b#Section]]\n- **A** [canon]: a. [[notes/a]]\n\n"
                                "## Canon\n\n- **Rule one**: do x. Source: [[notes/a]]. Evidence: [[notes/b]]\n"
                                "- **Rule two**: do y. Source: [[notes/a]].\n\n## Edges\n\n- `[data]` is ignored in code.\n")
        self.wb("check", "--json")
        w = json.loads((self.root / "world/.check.json").read_text())["world"]
        m = w["maps"][0]
        self.assertEqual((m["canon_rules"], m["levels"]["canon"], m["levels"]["note"], m["levels"]["data"]), (2, 1, 1, 0))
        self.assertEqual([i for i in w["issues"] if "evidence" in i], ["world/notes.md:14: canon rule cites no evidence"])

    def test_eval_runs_disallow_the_shell(self):
        class A: max_turns = 5; model = None; user_settings = False
        for task in (False, True):
            cmd = wb.claude_cmd(A, task)
            self.assertEqual(cmd[cmd.index("--disallowedTools") + 1], "Bash")

    def test_rel_to_workdir_handles_private_prefix(self):
        self.assertEqual(wb.rel_to_workdir("/private/var/x/run/a.md", "/var/x/run"), "a.md")
        self.assertEqual(wb.rel_to_workdir("/var/x/run/a.md", "/private/var/x/run"), "a.md")
        self.assertIsNone(wb.rel_to_workdir("/var/x/other/a.md", "/var/x/run"))
        self.assertEqual(wb.rel_to_workdir("notes/a.md", "/var/x/run"), "notes/a.md")

    def test_score_counts_unparsed_runs_as_errors(self):
        p = {"id": "p01", "expect": ["a.md"]}
        self.assertEqual(wb.score_run(p, {"stdout": "not json", "stderr": "boom"})["ok"], False)
        meta = json.dumps({"result": "no json here"})
        s = wb.score_run(p, {"stdout": meta})
        self.assertFalse(s["ok"])
        self.assertIn("no answer JSON", s["error"])

    def test_norm_path_variants(self):
        self.assertEqual(wb.norm_path("[[Notes/B]]"), "notes/b")
        self.assertEqual(wb.norm_path("./notes/b.md#Section"), "notes/b")
        self.assertEqual(wb.norm_path("`notes/b.md`"), "notes/b")


if __name__ == "__main__":
    unittest.main()
