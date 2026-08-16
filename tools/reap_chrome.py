#!/usr/bin/env python3
"""Kill LEAKED headless Chrome, leave working ones alone.

Two things leak browsers on this machine:
  1. `--headless --screenshot/--dump-dom` never self-exits in Chrome 150, so every run that
     forgets its `pkill` leaves a full browser (≈11 processes, ~1.5 GB) resident forever.
  2. Any driver killed mid-session leaves its Chrome reparented to launchd (PPID 1).

Each browser is a process GROUP, so killing the leader alone can strand its renderers. This
kills the group.

  python3 reap_chrome.py            # dry run: show what would go
  python3 reap_chrome.py --kill     # kill orphans (PPID 1) and anything older than --max-age
  python3 reap_chrome.py --kill --max-age 900
"""
import os, re, signal, subprocess, sys, time

MAX_AGE = 900
if "--max-age" in sys.argv: MAX_AGE = int(sys.argv[sys.argv.index("--max-age") + 1])
KILL = "--kill" in sys.argv

def etime_to_s(t):
    t = t.strip(); d = 0
    if "-" in t: d, t = t.split("-", 1); d = int(d)
    p = [int(x) for x in t.split(":")]
    while len(p) < 3: p.insert(0, 0)
    return d * 86400 + p[0] * 3600 + p[1] * 60 + p[2]

out = subprocess.run(["ps", "-Ao", "pid=,ppid=,pgid=,etime=,rss=,command="],
                     capture_output=True, text=True).stdout
tops, helpers, alive = [], 0, set()
for line in out.splitlines():
    m = re.match(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\d+)\s+(.*)", line)
    if not m: continue
    pid, ppid, pgid, et, rss, cmd = int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5]), m[6]
    alive.add(pid)
    if "Google Chrome" not in cmd: continue
    if "--type=" in cmd or "(Google Chrome He" in cmd: helpers += 1; continue
    if "--headless" not in cmd: continue        # never touch a real, human Chrome
    tops.append({"pid": pid, "ppid": ppid, "pgid": pgid, "age": etime_to_s(et), "rss": rss, "cmd": cmd})

print(f"headless browsers: {len(tops)}   helper processes: {helpers}")
doomed = []
for t in tops:
    orphan = t["ppid"] == 1 or t["ppid"] not in alive
    old = t["age"] > MAX_AGE
    legacy = ("--screenshot" in t["cmd"] or "--dump-dom" in t["cmd"])   # cannot self-exit
    why = "orphaned" if orphan else ("older than %ds" % MAX_AGE if old else ("legacy one-shot, age %ds" % t["age"] if legacy and t["age"] > 120 else None))
    mark = "REAP" if why else "keep"
    print(f"  [{mark}] pid {t['pid']:>6}  ppid {t['ppid']:>6}  age {t['age']:>5}s  {t['rss']//1024:>4}MB  {why or 'in use'}")
    if why: doomed.append(t)

if not KILL:
    print("\ndry run — nothing killed. add --kill")
    sys.exit(0)
for t in doomed:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try: os.killpg(t["pgid"], sig)
        except Exception:
            try: os.kill(t["pid"], sig)
            except Exception: pass
        time.sleep(0.4)
        try: os.kill(t["pid"], 0)
        except OSError: break
print(f"reaped {len(doomed)} browser(s)")
