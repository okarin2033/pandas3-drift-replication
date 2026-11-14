"""Counts of silent drift programs per task (E0a~E1 and E0a~E2), from results/per_program.jsonl.

Read-only. Run from the study folder:  python3 -I -B paper/v3/scripts/task_concentration.py
Output: paper/v3/scripts/task_concentration.tsv (one row per task with at least one silent program)
and a short summary on stdout. Field used: targets[pair].silent, targets[pair].drift, task_id, stratum,
family, model, targets[pair].primary_label.
"""
import json, collections, os

SRC = "results/per_program.jsonl"
OUT = "paper/v3/scripts/task_concentration.tsv"

silent = {p: collections.Counter() for p in ("E0a~E1", "E0a~E2")}
drift = {p: collections.Counter() for p in ("E0a~E1", "E0a~E2")}
models = {p: collections.defaultdict(set) for p in ("E0a~E1", "E0a~E2")}
labels = {p: collections.defaultdict(collections.Counter) for p in ("E0a~E1", "E0a~E2")}
meta = {}
with open(SRC) as f:
    for line in f:
        r = json.loads(line)
        meta[r["task_id"]] = (r["stratum"], r["family"] or r.get("generic_family") or "")
        for p in ("E0a~E1", "E0a~E2"):
            t = r["targets"][p]
            if t.get("drift"):
                drift[p][r["task_id"]] += 1
            if t.get("silent"):
                silent[p][r["task_id"]] += 1
                models[p][r["task_id"]].add(r["model"])
                labels[p][r["task_id"]][t.get("primary_label")] += 1

with open(OUT, "w") as o:
    o.write("pair\ttask_id\tstratum\tfamily\tsilent_programs\tdrift_programs\tmodels_with_silent\tprimary_labels\n")
    for p in ("E0a~E1", "E0a~E2"):
        for tid, n in sorted(silent[p].items(), key=lambda kv: (-kv[1], kv[0])):
            s, fam = meta[tid]
            lab = ";".join(f"{k}:{v}" for k, v in labels[p][tid].most_common())
            o.write(f"{p}\t{tid}\t{s}\t{fam}\t{n}\t{drift[p][tid]}\t{len(models[p][tid])}\t{lab}\n")

for p in ("E0a~E1",):
    for st in ("M", "A", "R"):
        items = sorted(((n, t) for t, n in silent[p].items() if meta[t][0] == st), reverse=True)
        tot = sum(n for n, _ in items)
        top = items[:10]
        print(p, st, "tasks", len(items), "silent", tot, "top10", top)
        if st == "M":
            fam_tasks = collections.Counter(meta[t][1] for _, t in items)
            print("  M tasks with silent drift per family:", dict(sorted(fam_tasks.items())))
            c = 0
            for i, (n, t) in enumerate(items, 1):
                c += n
                if i in (5, 10):
                    print(f"  top {i} tasks hold {c} of {tot}")
