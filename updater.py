"""Checks GitHub for a newer release and, in the .exe build, installs it.

Everything network related runs on a background thread. The menu reads `state` to
show what is going on. Any failure just leaves the game as it is.

Installing: the new exe is downloaded next to the running one, the running exe is
renamed to Stickfight.old.exe (Windows allows renaming a running exe, not replacing
it), the new one takes its name and gets launched, and the game quits. The next start
deletes the old file.
"""

import hashlib
import json
import os
import subprocess
import sys
import threading
import urllib.request
import webbrowser

from version import VERSION

REPO = "Vavoss123/stickfight"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"

FROZEN = getattr(sys, "frozen", False)   # True inside the PyInstaller exe
EXE = sys.executable if FROZEN else None

# status: idle, checking, current, available, downloading, restarting, failed
state = {"status": "idle", "latest": None, "asset": None, "progress": 0.0, "error": ""}


def parse_version(s):
    """'v1.2.3' -> (1, 2, 3). Anything that isn't a number counts as 0."""
    out = []
    for part in s.strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out)


def is_newer(latest, current=VERSION):
    return parse_version(latest) > parse_version(current)


def _get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": f"Stickfight/{VERSION}",
                                               "Accept": "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=timeout)


def cleanup_old():
    """Delete the exe left behind by the last update."""
    if FROZEN:
        old = _old_path()
        try:
            if os.path.exists(old):
                os.remove(old)
        except OSError:
            pass


def _old_path():
    base, ext = os.path.splitext(EXE)
    return f"{base}.old{ext}"


def check_async():
    if state["status"] in ("checking", "downloading", "restarting"):
        return
    state["status"] = "checking"
    threading.Thread(target=_check, daemon=True).start()


def _check():
    try:
        with _get(API) as r:
            rel = json.load(r)
        tag = rel.get("tag_name", "")
        asset = next((a for a in rel.get("assets", [])
                      if a.get("name", "").lower().endswith(".exe")), None)
        state["latest"] = tag
        state["asset"] = asset
        state["status"] = "available" if tag and is_newer(tag) else "current"
    except Exception as e:  # offline, rate limited, no releases yet
        state["status"] = "current"
        state["error"] = str(e)


def start_update():
    """Called when the player presses U on the menu."""
    if state["status"] != "available":
        return
    if not FROZEN or not state["asset"] or os.name != "nt":
        # Running from source, or no exe in the release: send them to the page.
        webbrowser.open(RELEASES_PAGE)
        return
    state["status"] = "downloading"
    state["progress"] = 0.0
    threading.Thread(target=_download_and_swap, daemon=True).start()


def _download_and_swap():
    asset = state["asset"]
    new_path = EXE + ".new"
    try:
        size = asset.get("size") or 0
        sha = hashlib.sha256()
        got = 0
        with _get(asset["browser_download_url"], timeout=30) as r, open(new_path, "wb") as f:
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                sha.update(chunk)
                got += len(chunk)
                if size:
                    state["progress"] = got / size
        if size and got != size:
            raise IOError("download was cut short")
        digest = asset.get("digest") or ""
        if digest.startswith("sha256:") and digest[7:].lower() != sha.hexdigest():
            raise IOError("download is corrupted")

        old = _old_path()
        if os.path.exists(old):
            os.remove(old)
        os.replace(EXE, old)
        try:
            os.replace(new_path, EXE)
        except OSError:
            os.replace(old, EXE)   # put the working exe back
            raise
        state["status"] = "restarting"
    except Exception as e:
        state["status"] = "failed"
        state["error"] = str(e)
        try:
            os.remove(new_path)
        except OSError:
            pass


def relaunch():
    """Start the freshly installed exe. The caller then quits the game."""
    env = dict(os.environ)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"   # new exe unpacks its own files
    subprocess.Popen([EXE], env=env, close_fds=True)
