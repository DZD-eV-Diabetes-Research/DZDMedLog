#!/usr/bin/env python3
"""Render a Gource video of the whole DZDMedLog story (all branches, all authors).

Besides the git history it adds GitHub activity as files under github/:
  issues and PRs appear when opened, flash when commented on and vanish when closed.
Releases become captions. Authors are merged by GitHub login and shown with their avatars.

usage: python3 docs/make_gource_video.py [--repo PATH] [--out FILE.mp4] [--seconds 120] [--no-github]
The video lands in the current directory; temp files go to ~/.cache/medlog-gource.
needs: git, gource, ffmpeg; gh (logged in) for the GitHub parts and avatars
"""
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import urllib.request

GH_REPO = "DZD-eV-Diabetes-Research/DZDMedLog"
TITLE = "DZDMedLog"
FPS = 30
SIZE = "1280x720"

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ap.add_argument("--out", default=os.path.abspath("medlog_gource_720p.mp4"))
ap.add_argument("--seconds", type=float, default=120)
ap.add_argument("--no-github", action="store_true", help="git history only, no issues/PRs/avatars/captions")
ap.add_argument("--log-only", action="store_true", help="only build the gource log in the work dir, do not render")
args = ap.parse_args()

for tool in ("git",) + (() if args.log_only else ("gource", "ffmpeg", "ffprobe")) + (() if args.no_github else ("gh",)):
    if not shutil.which(tool):
        sys.exit(f"missing tool: {tool}  (sudo apt install gource ffmpeg)")

work = os.path.expanduser("~/.cache/medlog-gource")
os.makedirs(os.path.join(work, "avatars"), exist_ok=True)


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def gh_json(path):
    out = run("gh", "api", "--paginate", "--slurp", path)
    return [item for page in json.loads(out) for item in page]


def ts(iso):
    return int(dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


# ---------- git history (all branches, renames as delete+add) ----------
print("reading git history ...")
raw = run("git", "-C", args.repo, "log", "--all", "--no-renames", "--name-status",
          "--format=%x00%ct|%aE|%aN|%H")
commits = []  # (time, email, name, sha, [(action, path)])
for block in raw.split("\x00")[1:]:
    lines = [l for l in block.splitlines() if l.strip()]
    t, email, name, sha = lines[0].split("|", 3)
    changes = []
    for l in lines[1:]:
        parts = l.split("\t")
        if parts[0][0] in "AMD":
            changes.append((parts[0][0], parts[-1]))
    commits.append((int(t), email.lower(), name, sha, changes))

# ---------- unify identities via GitHub login ----------
user_of = {}  # email -> display name
if not args.no_github:
    print("resolving GitHub logins for commit emails ...")
    sample = {}
    for t, email, name, sha, _ in commits:
        sample.setdefault(email, (sha, name))
    for email, (sha, name) in sample.items():
        login = None
        try:
            login = json.loads(run("gh", "api", f"repos/{GH_REPO}/commits/{sha}")).get("author") or {}
            login = login.get("login")
        except subprocess.CalledProcessError:
            pass
        user_of[email] = login or name
        print(f"  {email or '(none)':45} -> {user_of[email]}")
# fallback for anything unresolved: same name -> same person
for t, email, name, sha, _ in commits:
    user_of.setdefault(email, name)

events = []  # (time, user, action, path)
for t, email, name, sha, changes in commits:
    for action, path in changes:
        events.append((t, user_of[email], action, path))

# ---------- GitHub issues, PRs, comments, releases ----------
captions = []
if not args.no_github:
    print("reading issues, PRs and comments ...")
    issues = gh_json(f"repos/{GH_REPO}/issues?state=all&per_page=100")
    gh_events = []
    path_of = {}
    for it in issues:
        kind = "pulls" if "pull_request" in it else "issues"
        path = f"github/{kind}/{it['number']}.{'pr' if kind == 'pulls' else 'issue'}"
        path_of[it["number"]] = path
        gh_events.append((ts(it["created_at"]), it["user"]["login"], "A", path))
        if it.get("closed_at"):
            closer = (it.get("closed_by") or it["user"])["login"]
            gh_events.append((ts(it["closed_at"]), closer, "D", path))
    for c in gh_json(f"repos/{GH_REPO}/issues/comments?per_page=100"):
        num = int(c["issue_url"].rsplit("/", 1)[1])
        if num in path_of:
            gh_events.append((ts(c["created_at"]), c["user"]["login"], "M", path_of[num]))
    for c in gh_json(f"repos/{GH_REPO}/pulls/comments?per_page=100"):
        num = int(c["pull_request_url"].rsplit("/", 1)[1])
        if num in path_of:
            gh_events.append((ts(c["created_at"]), c["user"]["login"], "M", path_of[num]))
    # a comment on an already closed issue would re-add it; drop those so closed stays closed
    open_now = set()
    for e in sorted(gh_events, key=lambda e: (e[0], "AMD".index(e[2]))):
        if e[2] == "A":
            open_now.add(e[3])
        elif e[3] not in open_now:
            continue
        elif e[2] == "D":
            open_now.discard(e[3])
        events.append(e)

    for r in gh_json(f"repos/{GH_REPO}/releases?per_page=100"):
        if r.get("published_at") and not r.get("draft"):
            captions.append((ts(r["published_at"]), f"Release {r.get('name') or r['tag_name']}"))

    print("downloading avatars ...")
    for login in sorted({e[1] for e in events}):
        dest = os.path.join(work, "avatars", f"{login}.png")
        if os.path.exists(dest):
            continue
        try:
            urllib.request.urlretrieve(f"https://github.com/{login}.png?size=128", dest)
        except Exception as exc:  # unknown login (plain git name), no avatar then
            print(f"  no avatar for {login}: {exc}")

events.sort(key=lambda e: e[0])
log_path = os.path.join(work, "gource.log")
with open(log_path, "w") as f:
    for t, user, action, path in events:
        f.write(f"{t}|{user.replace('|', ' ')}|{action}|/{path}\n")
cap_path = os.path.join(work, "captions.txt")
with open(cap_path, "w") as f:
    for t, text in sorted(captions):
        f.write(f"{t}|{text}\n")

first, last = events[0][0], events[-1][0]
days = (last - first) / 86400
# play the story a bit faster than the target length; the second pass stretches it to exactly --seconds
spd = (args.seconds * 0.9) / days
print(f"{len(events)} events, {days:.0f} days, {spd:.3f} s/day, {len(captions)} captions")
if args.log_only:
    sys.exit(0)

# ---------- pass 1: gource -> lossless intermediate ----------
gource = [
    "gource", log_path, f"-{SIZE}",
    "--title", TITLE,
    "--seconds-per-day", f"{spd:.4f}",
    "--auto-skip-seconds", "0.5",
    "--stop-at-end",
    "--key",
    "--date-format", "%B %Y",
    "--hide", "mouse,progress,filenames",
    "--file-idle-time", "0",
    "--max-file-lag", "0.1",
    "--highlight-users",
    "--user-scale", "1.4",
    "--bloom-multiplier", "1.1",
    "--bloom-intensity", "0.6",
    "--background-colour", "0d1117",
    "--font-size", "18",
    "--dir-name-depth", "2",
    "--output-framerate", str(FPS),
    "-o", "-",
]
if os.listdir(os.path.join(work, "avatars")):
    gource += ["--user-image-dir", os.path.join(work, "avatars")]
if captions:
    gource += ["--caption-file", cap_path, "--caption-duration", "2.5", "--caption-size", "26",
               "--caption-colour", "7ee787"]
if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY") and shutil.which("xvfb-run"):
    gource = ["xvfb-run", "-a", "-s", f"-screen 0 {SIZE}x24"] + gource

raw_video = os.path.join(work, "raw.mkv")
print("pass 1: rendering with gource (a window opens, leave it alone) ...")
g = subprocess.Popen(gource, stdout=subprocess.PIPE)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-r", str(FPS), "-f", "image2pipe", "-vcodec", "ppm",
                "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "0", raw_video],
               stdin=g.stdout, check=True)
g.wait()

# ---------- pass 2: retime to exactly --seconds, encode for sharing ----------
dur = float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw_video))
factor = args.seconds / dur
print(f"pass 2: raw {dur:.1f}s -> {args.seconds:.0f}s (x{factor:.3f}) ...")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw_video,
                "-vf", f"setpts={factor:.6f}*PTS,fps={FPS},fade=t=in:st=0:d=1,fade=t=out:st={args.seconds - 1.5}:d=1.5",
                "-t", str(args.seconds), "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", args.out], check=True)
print("done:", args.out)
