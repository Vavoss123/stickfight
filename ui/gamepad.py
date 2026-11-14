"""Controllers, through SDL's game controller mapping so the buttons are in the same
place on any pad (Xbox names: on PlayStation A is cross, B circle, X square, Y triangle).

In a fight the face buttons and the d-pad pick moves directly, so picks stay as hidden
as they are on the keyboard. Everywhere else the pad is turned into key presses: the
d-pad and left stick are the arrow keys, A and Start are Enter, B and Back are Escape.
"""

import pygame

try:
    from pygame._sdl2 import controller
except ImportError:   # very old pygame: no controllers, the game still runs
    controller = None

B = pygame
PICK_BUTTONS = [B.CONTROLLER_BUTTON_A, B.CONTROLLER_BUTTON_B, B.CONTROLLER_BUTTON_X,
                B.CONTROLLER_BUTTON_Y, B.CONTROLLER_BUTTON_DPAD_UP, B.CONTROLLER_BUTTON_DPAD_RIGHT,
                B.CONTROLLER_BUTTON_DPAD_DOWN, B.CONTROLLER_BUTTON_DPAD_LEFT,
                B.CONTROLLER_BUTTON_LEFTSHOULDER, B.CONTROLLER_BUTTON_RIGHTSHOULDER] if controller else []
# The triggers are axes, so they get made up button numbers
TRIGGER_LT, TRIGGER_RT = 1001, 1002
if controller:
    PICK_BUTTONS += [TRIGGER_LT, TRIGGER_RT]
PICK_LABELS = ["A", "B", "X", "Y", "Up", "Rt", "Dn", "Lt", "LB", "RB", "LT", "RT"]
# The same buttons as a PlayStation pad prints them
PS_SHAPES = ["✕", "○", "□", "△"]
PS_REST = ["Up", "Rt", "Dn", "Lt", "L1", "R1", "L2", "R2"]
PS_WORDS = ("dualsense", "dualshock", "playstation", "ps3", "ps4", "ps5")


def is_playstation(pad_name):
    n = (pad_name or "").lower()
    return any(w in n for w in PS_WORDS) or n.startswith("wireless controller")


def ps_labels():
    """The PlayStation labels. The face buttons are drawn as shapes (see common.pad_shape)."""
    return PS_SHAPES + PS_REST

AS_KEYS = {
    "dpad_up": pygame.K_UP, "dpad_down": pygame.K_DOWN, "dpad_left": pygame.K_LEFT,
    "dpad_right": pygame.K_RIGHT, "a": pygame.K_RETURN, "b": pygame.K_ESCAPE,
    "start": pygame.K_RETURN, "back": pygame.K_ESCAPE,
}
if controller:
    _NAMES = {B.CONTROLLER_BUTTON_DPAD_UP: "dpad_up", B.CONTROLLER_BUTTON_DPAD_DOWN: "dpad_down",
              B.CONTROLLER_BUTTON_DPAD_LEFT: "dpad_left", B.CONTROLLER_BUTTON_DPAD_RIGHT: "dpad_right",
              B.CONTROLLER_BUTTON_A: "a", B.CONTROLLER_BUTTON_B: "b",
              B.CONTROLLER_BUTTON_START: "start", B.CONTROLLER_BUTTON_BACK: "back"}
    EVENTS = {pygame.CONTROLLERDEVICEADDED, pygame.CONTROLLERDEVICEREMOVED,
              pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERAXISMOTION}
else:
    _NAMES = {}
    EVENTS = set()

STICK = 0.6   # how far the stick goes before it counts as a press


def name(button):
    return _NAMES.get(button)


class Pads:
    def __init__(self):
        self.pads = {}      # instance id -> Controller
        self.order = []     # instance ids in the order they were plugged in
        self.stick = {}     # instance id -> (x, y) direction the stick is held in
        self.playstation = set()   # instance ids of PlayStation pads, for their button names
        if controller is None:
            return
        try:
            controller.init()
            for i in range(controller.get_count()):
                self._add(i)
        except pygame.error:
            pass

    def _add(self, device_index):
        try:
            c = controller.Controller(device_index)
        except pygame.error:
            return
        iid = c.as_joystick().get_instance_id()
        if iid not in self.pads:
            self.pads[iid] = c
            self.order.append(iid)
            try:
                if is_playstation(c.name):
                    self.playstation.add(iid)
            except (AttributeError, pygame.error):
                pass

    def labels(self, slot):
        """Button names for the pad in this slot, in pick order."""
        iid = self.order[slot] if slot is not None and slot < len(self.order) else None
        return ps_labels() if iid in self.playstation else PICK_LABELS

    @property
    def count(self):
        return len(self.order)

    def slot(self, iid):
        """0 for the first pad plugged in, 1 for the second."""
        return self.order.index(iid) if iid in self.order else None

    def handle(self, e):
        """Keep track of pads. Returns (slot, button) for a press, a key for stick moves,
        or None."""
        if e.type == pygame.CONTROLLERDEVICEADDED:
            self._add(e.device_index)
            return None
        if e.type == pygame.CONTROLLERDEVICEREMOVED:
            self.pads.pop(e.instance_id, None)
            self.playstation.discard(e.instance_id)
            if e.instance_id in self.order:
                self.order.remove(e.instance_id)
            return None
        if e.type == pygame.CONTROLLERBUTTONDOWN:
            s = self.slot(e.instance_id)
            return ("button", s, e.button) if s is not None else None
        if e.type == pygame.CONTROLLERAXISMOTION and e.axis in (B.CONTROLLER_AXIS_TRIGGERLEFT,
                                                                 B.CONTROLLER_AXIS_TRIGGERRIGHT):
            key = (e.instance_id, e.axis)
            down = e.value > 16000
            was = self.stick.get(key, False)
            self.stick[key] = down
            s = self.slot(e.instance_id)
            if down and not was and s is not None:
                return ("button", s, TRIGGER_LT if e.axis == B.CONTROLLER_AXIS_TRIGGERLEFT else TRIGGER_RT)
            return None
        if e.type == pygame.CONTROLLERAXISMOTION and e.axis in (B.CONTROLLER_AXIS_LEFTX, B.CONTROLLER_AXIS_LEFTY):
            v = e.value / 32767
            x, y = self.stick.get(e.instance_id, (0, 0))
            if e.axis == B.CONTROLLER_AXIS_LEFTX:
                new = (1 if v > STICK else -1 if v < -STICK else 0, y)
                key = {1: pygame.K_RIGHT, -1: pygame.K_LEFT}.get(new[0]) if new[0] != x else None
            else:
                new = (x, 1 if v > STICK else -1 if v < -STICK else 0)
                key = {1: pygame.K_DOWN, -1: pygame.K_UP}.get(new[1]) if new[1] != y else None
            self.stick[e.instance_id] = new
            return ("key", key) if key else None
        return None


def key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0)
