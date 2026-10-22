"""Fighter codes: carry a career fighter to another computer for local games.

A code holds the fighter (name, style, stats, look, personality, deck and perks) packed
into bytes, with a checksum so a typo is caught instead of making a strange fighter.
It is written in Crockford base32 (no I, L, O or U to mix up) in groups of five:

    USC-1K3F0-9QX2A-...

Cards, styles and weight classes are stored by a short hash of their id, so codes keep
working when new cards are added. Friends' fighters entered on this computer are kept
in ~/.stickfight/friends.json.
"""

import json
import os
import struct
import zlib

from .cards import CARDS, MAX_LEVEL, MAX_PERKS
from .constants import STAT_NAMES, STAT_MAX, STAT_MIN
from .fighter import Profile, Stats
from .looks import HAIRS, TATTOOS
from .personality import NAMES as PERSONALITIES
from .roster import ARCHETYPES
from .weights import NAMES as WEIGHTS

VERSION = 1
PREFIX = "USC"
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"     # Crockford base32
FRIENDS_PATH = os.path.join(os.path.expanduser("~"), ".stickfight", "friends.json")
MAX_FRIENDS = 12
MAX_TEXT = 24          # bytes for a name, nickname or hometown


class CodeError(ValueError):
    """The code could not be read. The message says why, for the player."""


def _h(s):
    return zlib.crc32(s.encode("utf-8")) & 0xFFFF


def _lookup(table):
    return {_h(k): k for k in table}


def _text(s):
    return s.encode("utf-8")[:MAX_TEXT].decode("utf-8", "ignore").encode("utf-8")


def _inches(height):
    try:
        feet, inch = height.replace('"', "").split("'")
        return max(0, min(255, int(feet) * 12 + int(inch or 0)))
    except (ValueError, AttributeError):
        return 72


# Bytes

def pack(p):
    out = bytearray([VERSION])
    for s in (p.name, p.nickname, p.hometown):
        b = _text(s or "")
        out += bytes([len(b)]) + b
    out += struct.pack(">HHH", _h(p.archetype), _h(p.weight), _h(p.personality or ""))
    out.append(_inches(p.height))
    out += bytes(max(0, min(255, int(p.stats.get(s)))) for s in STAT_NAMES)
    out += bytes(int(c) & 255 for c in p.color[:3])
    if p.gloves:
        out += bytes([1]) + bytes(int(c) & 255 for c in p.gloves[:3])
    else:
        out.append(0)
    look = p.look or {}
    hair = HAIRS.index(look["hair"]) if look.get("hair") in HAIRS else 255
    tattoo = TATTOOS.index(look["tattoo"]) if look.get("tattoo") in TATTOOS else 255
    has_look = 1 if look else 0
    out += bytes([has_look, int(look.get("skin", 0)) & 255, hair, int(look.get("hair_color", 0)) & 255,
                  int(bool(look.get("beard"))), int(look.get("trim", 0)) & 255, tattoo])
    out += bytes(min(255, max(0, n)) for n in (p.wins, p.losses, p.draws))
    # Only the cards in use: the deck and the perks
    used = [(cid, False) for cid in p.deck.values()] + [(pid, True) for pid in p.perks]
    used = [(cid, perk) for cid, perk in used if cid in CARDS][:32]
    out.append(len(used))
    for cid, perk in used:
        level = max(1, min(MAX_LEVEL, int(p.cards.get(cid, 1))))
        out += struct.pack(">HB", _h(cid), level | (0x80 if perk else 0))
    out += struct.pack(">H", zlib.crc32(bytes(out)) & 0xFFFF)
    return bytes(out)


def unpack(data):
    if len(data) < 3 or struct.unpack(">H", data[-2:])[0] != zlib.crc32(data[:-2]) & 0xFFFF:
        raise CodeError("That code has a typo in it. Check it and try again.")
    if data[0] != VERSION:
        raise CodeError("That code is from a newer version of the game. Update to use it.")
    pos = 1

    def take(n):
        nonlocal pos
        if pos + n > len(data) - 2:
            raise CodeError("That code is cut short. Make sure you copied all of it.")
        chunk = data[pos:pos + n]
        pos += n
        return chunk

    texts = []
    for _ in range(3):
        n = take(1)[0]
        texts.append(take(n).decode("utf-8", "ignore").strip())
    name, nickname, hometown = texts
    if not name:
        raise CodeError("That code has no fighter in it.")
    arch, weight, pers = struct.unpack(">HHH", take(6))
    archetype = _lookup(ARCHETYPES).get(arch, "Striker")
    weight = _lookup(WEIGHTS).get(weight, "Welterweight")
    pers = _lookup(PERSONALITIES).get(pers, "")
    inches = take(1)[0] or 72
    raw = take(len(STAT_NAMES))
    stats = Stats(**{s: max(STAT_MIN, min(STAT_MAX, v)) for s, v in zip(STAT_NAMES, raw)})
    color = tuple(take(3))
    gloves = tuple(take(3)) if take(1)[0] else None
    has_look, skin, hair, hair_color, beard, trim, tattoo = take(7)
    look = {}
    if has_look:
        look = {"skin": skin, "hair": HAIRS[hair] if hair < len(HAIRS) else "short",
                "hair_color": hair_color, "beard": bool(beard), "trim": trim,
                "tattoo": TATTOOS[tattoo] if tattoo < len(TATTOOS) else "none"}
    wins, losses, draws = take(3)
    p = Profile(name=name, nickname=nickname, archetype=archetype, stats=stats, color=color,
                hometown=hometown, wins=wins, losses=losses, draws=draws,
                height=f"{inches // 12}'{inches % 12}\"", weight=weight, personality=pers,
                gloves=gloves, look=look)
    by_hash = _lookup(CARDS)
    for _ in range(take(1)[0]):
        h, flags = struct.unpack(">HB", take(3))
        cid = by_hash.get(h)
        if cid is None:
            continue                       # a card this version does not have
        card = CARDS[cid]
        level = max(1, min(MAX_LEVEL, flags & 0x7F))
        if flags & 0x80:
            if card.is_perk and cid not in p.perks and len(p.perks) < MAX_PERKS:
                p.perks.append(cid)
                p.cards[cid] = level
        elif card.move is not None and card.move.slot not in p.deck:
            p.deck[card.move.slot] = cid
            p.cards[cid] = level
    return p


# Text

def _b32(data):
    bits = "".join(f"{b:08b}" for b in data)
    bits += "0" * (-len(bits) % 5)
    return "".join(ALPHABET[int(bits[k:k + 5], 2)] for k in range(0, len(bits), 5))


def _unb32(s):
    bits = "".join(f"{ALPHABET.index(ch):05b}" for ch in s)
    return bytes(int(bits[k:k + 8], 2) for k in range(0, len(bits) - 7, 8))


def encode(profile):
    """The code for a fighter, ready to show or copy."""
    body = _b32(pack(profile))
    groups = [body[k:k + 5] for k in range(0, len(body), 5)]
    return "-".join([PREFIX] + groups)


def decode(code):
    """A Profile from a code. Raises CodeError with a message for the player."""
    s = "".join(ch for ch in (code or "").upper() if ch.isalnum())
    if s.startswith(PREFIX):
        s = s[len(PREFIX):]
    s = s.replace("I", "1").replace("L", "1").replace("O", "0")
    if not s:
        raise CodeError("Type or paste a fighter code first.")
    if any(ch not in ALPHABET for ch in s):
        raise CodeError("That is not a fighter code. They only use letters and numbers.")
    return unpack(_unb32(s))


# Friends entered on this computer

def load_friends(path=FRIENDS_PATH):
    """[(code, Profile)] for every saved code that still reads."""
    try:
        with open(path, encoding="utf-8") as f:
            codes = json.load(f)
    except (OSError, ValueError):
        return []
    out = []
    for code in codes if isinstance(codes, list) else []:
        try:
            out.append((code, decode(code)))
        except (CodeError, TypeError):
            continue
    return out


def add_friend(code, path=FRIENDS_PATH):
    """Read the code and keep it. Returns the Profile, or raises CodeError."""
    p = decode(code)
    codes = [c for c, f in load_friends(path) if f.name != p.name]
    codes.insert(0, code.strip().upper())
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(codes[:MAX_FRIENDS], f, indent=1)
    except OSError:
        pass
    return p


def remove_friend(name, path=FRIENDS_PATH):
    codes = [c for c, f in load_friends(path) if f.name != name]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(codes, f, indent=1)
    except OSError:
        pass
