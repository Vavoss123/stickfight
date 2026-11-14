"""Save screenshots of the main screens and of a fight at each stage, without a window.

    python -m tools.shots --out shots
    python -m tools.shots --out shots --size 1366x768   # also check how it fits other windows

Handy after UI changes: look through the folder instead of clicking through the game.
"""

import argparse
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

import updater

updater.check_async = lambda: None


def save(app, out, name):
    app.scene.draw(app.screen)
    app.toasts.draw(app.screen)
    pygame.image.save(app.screen, os.path.join(out, f"{name}.png"))


def run(app, secs, dt=1 / 30):
    for _ in range(int(secs / dt)):
        app.scene.update(dt)


def fight_shots(app, out):
    from engine.cpu import CPU
    from engine.roster import quick_fighters
    from ui.scenes.fight import FightScene, FightConfig
    r = quick_fighters()
    red, blue = r[0], r[1]
    scene = FightScene(app, FightConfig(red, blue, mode="cpu", level="normal"))
    app.scene = scene
    save(app, out, "fight_00_intro")
    brain = CPU("normal", seed=3)
    seen = {}
    dt = 1 / 30
    for step in range(30 * 60 * 12):
        ph = scene.phase
        if ph == "pick" and scene.picks[0] is None:
            n = seen.get("pick", 0)
            if n < 4:
                save(app, out, f"fight_pick_{n}")
            if n == 0 and scene.buttons[0]:
                b = scene.buttons[0][1]
                b.hover = True
                save(app, out, "fight_pick_hover")
                b.hover = False
            seen["pick"] = n + 1
            opts = scene.fight.options(0)
            scene._lock(0, opts.index(brain.choose(scene.fight, 0)))
        if ph == "anim":
            n = seen.get("anim", 0)
            if n in (8, 20, 40, 120, 300):
                save(app, out, f"fight_anim_{n}")
            seen["anim"] = n + 1
        if ph in ("round_end", "decision", "finished", "replay") and seen.get(ph, 0) == 15:
            save(app, out, f"fight_{ph}")
        seen[ph] = seen.get(ph, 0) + 1
        if ph == "round_end" and scene.can_continue:
            save(app, out, "fight_round_end_ready")
            scene._next_round()
        if ph == "finished" and scene.can_continue:
            save(app, out, "fight_finished_ready")
            scene._to_result()
            run(app, 0.5)
            save(app, out, "result")
            return
        scene.update(dt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="shots")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    random.seed(1)
    from main import App
    app = App()
    app.settings["skip_walkouts"] = True
    from ui.scenes.menu import MenuScene
    from ui.scenes.select import SelectScene
    if not args.only or args.only == "menus":
        app.scene = MenuScene(app)
        run(app, 1.0)
        save(app, args.out, "menu")
        app.scene = SelectScene(app, "cpu")
        run(app, 0.3)
        save(app, args.out, "select")
    if not args.only or args.only == "fight":
        fight_shots(app, args.out)


if __name__ == "__main__":
    main()
