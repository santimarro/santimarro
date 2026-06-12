"""Fetch GitHub stats for the profile README via gh CLI (no cloning).

Uses /repos/{repo}/stats/contributors: full-history additions/deletions/commits
per contributor. Endpoint returns 202 while GitHub computes; we retry.
Writes github-stats.json consumed by generate_github_profile.py.
"""

import json
import subprocess
import sys
import time

LOGIN = "santimarro"


def gh(args):
    r = subprocess.run(["gh", "api"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def repo_stats(name_with_owner, attempts=20):
    for i in range(attempts):
        out = gh([f"repos/{name_with_owner}/stats/contributors"])
        if out:
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, list):
                for c in data:
                    if (c.get("author") or {}).get("login") == LOGIN:
                        adds = sum(w["a"] for w in c["weeks"])
                        dels = sum(w["d"] for w in c["weeks"])
                        return c["total"], adds, dels
                return 0, 0, 0  # repo has commits, none by us
        time.sleep(3)  # 202: still computing
    return None  # gave up


def main():
    out = subprocess.run(
        ["gh", "repo", "list", LOGIN, "--limit", "200", "--json", "nameWithOwner,stargazerCount,diskUsage"],
        capture_output=True, text=True, check=True,
    ).stdout
    repos = json.loads(out)
    followers = int(gh(["users/" + LOGIN, "--jq", ".followers"]))

    commits = adds = dels = 0
    skipped = []
    for i, r in enumerate(repos, 1):
        name = r["nameWithOwner"]
        if not r.get("diskUsage"):  # empty repo: stats endpoint never resolves
            print(f"[{i}/{len(repos)}] {name}: empty, skipping", flush=True)
            continue
        s = repo_stats(name)
        if s is None:
            skipped.append(name)
            print(f"[{i}/{len(repos)}] {name}: SKIPPED (stats not ready)", flush=True)
            continue
        c, a, d = s
        commits += c
        adds += a
        dels += d
        print(f"[{i}/{len(repos)}] {name}: commits={c} +{a} -{d}", flush=True)

    stats = {
        "repos": len(repos),
        "stars": sum(r["stargazerCount"] for r in repos),
        "followers": followers,
        "commits": commits,
        "additions": adds,
        "deletions": dels,
        "net": adds - dels,
        "skipped": skipped,
    }
    with open("github-stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
    if skipped:
        print(f"WARNING: {len(skipped)} repos skipped, re-run to pick them up", file=sys.stderr)


if __name__ == "__main__":
    main()
