"""Record a knockout and its slow motion replay as a GIF for the README.

Plays AI against AI fights in the real fight screen, without a window, until one ends
in a knockout, then saves the end of it.

    python -m tools.make_gif --out docs/ko.gif
"""

import argparse
import os
import sys
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from PIL import Image

import updater

updater.check_async = lambda: None

FPS = 15
SIZE = (640, 360)
BEFORE = 2.5      # seconds kept before the finish


def grab(surf):
    small = pygame.transform.smoothscale(surf, SIZE)
    return Image.frombytes("RGB", SIZE, pygame.image.tobytes(small, "RGB"))


def record(app, red, blue, max_tries=40):
    from engine.ai import AI
    from ui.scenes.fight import FightScene, FightConfig
    dt = 1 / FPS
    for attempt in range(max_tries):
        scene = FightScene(app, FightConfig(red, blue, mode="ai", level="hard"))
        app.scene = scene
        brain = AI("hard", seed=attempt, personality="pressure")
        frames = deque(maxlen=int(BEFORE * FPS))
        after = []
        replayed = False
        for _ in range(FPS * 60 * 20):
            if scene.phase == "pick" and scene.picks[0] is None:
                opts = scene.fight.options(0)
                scene._lock(0, opts.index(brain.choose(scene.fight, 0)))
            if scene.phase == "round_end" and scene.can_continue:
                scene._next_round()
            scene.update(dt)
            scene.draw(app.screen)
            if scene.phase == "replay":
                replayed = True
            if scene.fight.over and scene.fight.result.method not in ("KO", "TKO"):
                break
            if replayed or (scene.fight.over and scene.phase in ("finished", "replay")):
                after.append(grab(app.screen))
                if replayed and scene.phase == "finished" and scene.can_continue:
                    for _ in range(FPS):          # one more second on the result
                        scene.update(dt)
                        scene.draw(app.screen)
                        after.append(grab(app.screen))
                    return list(frames) + after
            else:
                frames.append(grab(app.screen))
        print(f"  fight {attempt + 1}: no knockout, trying again")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/ko.gif")
    args = ap.parse_args()
    from main import App
    from engine.roster import quick_fighters, division
    app = App()
    app.settings["skip_walkouts"] = True
    r = quick_fighters() + division()
    red = next(p for p in r if p.name == "Tommy Byrne")
    blue = next(p for p in r if p.name == "Dan Reyes")
    frames = record(app, red, blue)
    if not frames:
        sys.exit("no knockout found")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
    pal[0].save(args.out, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0,
                optimize=True)
    print(f"{len(frames)} frames, {os.path.getsize(args.out) / 1e6:.1f} MB -> {args.out}")


if __name__ == "__main__":
    main()
