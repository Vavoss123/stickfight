"""Drawing a fight card."""

import pygame

from engine.cards import CARDS, group_of, perk_text, leveled
from engine.constants import STRIKE, GRAPPLE, SUB, DEFEND, FEINT
from engine.moves import MOVES

from .choreo import ACTION
from .common import GOLD, WHITE, GREY, text, text_block
from .stickman import Figure

RARITY_COLOR = {"common": (170, 175, 185), "rare": (80, 150, 255), "legendary": GOLD,
                "basic": (90, 92, 104)}
CLASS_BG = {STRIKE: (92, 36, 34), GRAPPLE: (30, 52, 100), SUB: (70, 36, 100), DEFEND: (26, 80, 52),
            FEINT: (86, 64, 30)}
CLASS_WORD = {STRIKE: "strike", GRAPPLE: "grapple", SUB: "submission", DEFEND: "defence", FEINT: "feint"}
PERK_BG = (24, 74, 78)

_fig = Figure(0, 0, 1, (200, 200, 210), glove=(200, 60, 60), scale=0.55)


def _pose_for(card_id):
    if card_id in CARDS and CARDS[card_id].is_perk:
        return "victory"
    m = MOVES.get(card_id) or CARDS[card_id].move
    seq = ACTION.get(m.anim)
    if not seq:
        return "stance"
    # The most telling frame is the one where the blow lands, usually the second
    return seq[min(1, len(seq) - 1)][0]


def draw_card(surf, rect, card_id, level=1, owned=True, selected=False, equipped=False):
    """card_id may be a basic move key, a move card or a perk."""
    rect = pygame.Rect(rect)
    card = CARDS.get(card_id)
    basic = card is None
    rarity = "basic" if basic else card.rarity
    if card and card.is_perk:
        bg = PERK_BG
    else:
        m = MOVES[card_id] if basic else card.move
        bg = CLASS_BG[m.cls]
    if not owned:
        bg = tuple(int(c * 0.45) for c in bg)
    pygame.draw.rect(surf, bg, rect, border_radius=10)
    border = RARITY_COLOR[rarity]
    pygame.draw.rect(surf, border, rect, 4 if rarity == "legendary" else 3, border_radius=10)
    if selected:
        pygame.draw.rect(surf, WHITE, rect.inflate(8, 8), 2, border_radius=12)

    small = rect.w < 170
    pad = 8 if small else 10
    name = MOVES[card_id].name if basic else card.name
    text(surf, name, (rect.x + pad, rect.y + pad), 15 if small else 18, WHITE, bold=True,
         max_width=rect.w - pad * 2 - (30 if not basic else 0))
    # Level pips
    if not basic and owned:
        for n in range(3):
            c = GOLD if n < level else (60, 60, 70)
            pygame.draw.circle(surf, c, (rect.right - pad - 4 - (2 - n) * 11, rect.y + pad + 8), 4)

    # Type line
    if card and card.is_perk:
        kind = "Perk"
    else:
        m = MOVES[card_id] if basic else card.move
        kind = f"{group_of(m.slot)} {CLASS_WORD[m.cls]}"
    y = rect.y + pad + (20 if small else 24)
    text(surf, kind, (rect.x + pad, y), 12 if small else 13, (200, 200, 210))
    if card and card.move:
        text(surf, f"Replaces {MOVES[card.move.slot].name}", (rect.x + pad, y + 15), 11 if small else 12,
             GREY, max_width=rect.w - pad * 2)

    # Little fighter doing the move
    _fig.scale = 0.42 if small else 0.55
    _fig.set_pose(_pose_for(card_id))
    _fig.x = rect.centerx - (6 if not small else 4)
    _fig.y = rect.y + (118 if small else 150)
    _fig.glove = border if not basic else (200, 60, 60)
    _fig.draw(surf)

    # Numbers
    y = rect.y + (124 if small else 158)
    if card and card.is_perk:
        body = perk_text(card, max(1, level))
    else:
        m = MOVES[card_id] if basic else leveled(card.move, max(1, level))
        bits = []
        if m.cls == STRIKE:
            bits.append(f"DMG {m.dmg:.0f}")
            bits.append(f"ACC {int(m.acc * 100)}%")
        elif m.bonus:
            bits.append(f"+{int(m.bonus * 100)}% success")
        bits.append(f"STA {abs(int(m.cost))}" if m.cost > 0 else f"STA +{abs(int(m.cost))}")
        text(surf, "  ".join(bits), (rect.x + pad, y), 12 if small else 13, GOLD, bold=True,
             max_width=rect.w - pad * 2)
        y += 18
        body = (card.desc if card else m.desc)
    if not small or rect.h > 200:
        text_block(surf, body, (rect.x + pad, y), 12 if small else 13, rect.w - pad * 2,
                   WHITE, "topleft", line_gap=1)

    # Footer
    foot = "Basic" if basic else rarity.capitalize()
    if not owned:
        foot = "Not owned"
    if equipped:
        foot = "Equipped"
    text(surf, foot, (rect.centerx, rect.bottom - pad - 14), 12, border if owned else GREY, "midtop",
         bold=True)
