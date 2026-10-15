"""Fonts, colours and small drawing helpers shared by every screen."""

from collections import OrderedDict

import pygame

W, H = 1280, 720
FLOOR_Y = 600
CX = W // 2

RED = (214, 48, 49)
BLUE = (41, 128, 255)
GOLD = (240, 196, 60)
WHITE = (240, 240, 240)
GREY = (150, 155, 165)
DARK = (18, 20, 28)
PANEL = (24, 27, 38)
GREEN = (70, 200, 110)
CORNER = (RED, BLUE)

_fonts = {}
# Rendered text and panels are kept and reused instead of being rebuilt every frame.
# Both are capped so long sessions do not keep growing.
_text_cache = OrderedDict()
_fit_cache = {}
_panel_cache = OrderedDict()
TEXT_CACHE_SIZE = 300
PANEL_CACHE_SIZE = 40
PANEL_CACHE_MAX_AREA = 300 * 300   # big overlays are cheap to fill and costly to keep


def _cached(cache, key, limit, make):
    hit = cache.get(key)
    if hit is not None:
        cache.move_to_end(key)
        return hit
    hit = cache[key] = make()
    if len(cache) > limit:
        cache.popitem(last=False)
    return hit


def font(size, bold=False, display=False):
    key = (size, bold, display)
    if key not in _fonts:
        if display:
            names = "impact,arialblack,arial"
        else:
            names = "segoeui,arial,helvetica"
        _fonts[key] = pygame.font.SysFont(names, size, bold=bold)
    return _fonts[key]


def text(surf, s, pos, size=20, color=WHITE, anchor="topleft", bold=False, display=False,
         shadow=True, alpha=255, max_width=None):
    """Draw one line. With max_width the font shrinks until the line fits."""
    s = str(s)
    if max_width:
        key = (s, size, bold, display, max_width)
        fit = _fit_cache.get(key)
        if fit is None:
            fit = size
            while fit > 10 and font(fit, bold, display).size(s)[0] > max_width:
                fit -= 1
            if len(_fit_cache) > 2000:
                _fit_cache.clear()
            _fit_cache[key] = fit
        size = fit

    def make():
        f = font(size, bold, display)
        sh = f.render(s, True, (0, 0, 0))
        sh.set_alpha(150)
        return f.render(s, True, color), sh

    img, sh = _cached(_text_cache, (s, size, tuple(color), bold, display), TEXT_CACHE_SIZE, make)
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    r = img.get_rect(**{anchor: pos})
    if shadow:
        if alpha < 255:
            sh = sh.copy()
            sh.set_alpha(int(150 * alpha / 255))
        surf.blit(sh, r.move(2, 2))
    surf.blit(img, r)
    return r


def wrap(s, size, max_width, bold=False):
    """Split text into lines that fit max_width."""
    f = font(size, bold)
    lines, cur = [], ""
    for word in str(s).split():
        trial = f"{cur} {word}".strip()
        if cur and f.size(trial)[0] > max_width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def text_block(surf, s, pos, size, max_width, color=WHITE, anchor="midtop", bold=False,
               line_gap=4):
    """Draw wrapped text. Returns the y just below the last line."""
    x, y = pos
    for ln in wrap(s, size, max_width, bold):
        r = text(surf, ln, (x, y), size, color, anchor, bold=bold)
        y = r.bottom + line_gap
    return y


def panel(surf, rect, color=PANEL, alpha=220, radius=10, border=None):
    rect = pygame.Rect(rect)

    def make():
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
        if border:
            pygame.draw.rect(s, (*border, 255), s.get_rect(), 2, border_radius=radius)
        return s

    if rect.w * rect.h > PANEL_CACHE_MAX_AREA:
        surf.blit(make(), rect)
        return rect
    key = (rect.size, tuple(color), alpha, radius, tuple(border) if border else None)
    surf.blit(_cached(_panel_cache, key, PANEL_CACHE_SIZE, make), rect)
    return rect


def bar(surf, rect, frac, color, back=(40, 42, 52), flip=False, ghost=None):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, back, rect, border_radius=4)
    frac = max(0.0, min(1.0, frac))
    if ghost is not None and ghost > frac:
        g = max(0.0, min(1.0, ghost))
        gw = int(rect.w * g)
        gr = pygame.Rect(rect.right - gw if flip else rect.x, rect.y, gw, rect.h)
        pygame.draw.rect(surf, (240, 230, 200), gr, border_radius=4)
    w = int(rect.w * frac)
    r = pygame.Rect(rect.right - w if flip else rect.x, rect.y, w, rect.h)
    if w > 0:
        pygame.draw.rect(surf, color, r, border_radius=4)
    pygame.draw.rect(surf, (0, 0, 0), rect, 2, border_radius=4)


def lighten(c, f=1.3):
    return tuple(min(255, int(v * f)) for v in c)


class Button:
    def __init__(self, rect, label, key=None, sub="", color=(52, 58, 78), enabled=True,
                 size=22, sub_size=15, wrap=False):
        self.rect = pygame.Rect(rect)
        self.wrap = wrap     # long labels go on two lines instead of shrinking
        self.sub_size = sub_size
        self.label = label
        self.key = key
        self.sub = sub
        self.color = color
        self.enabled = enabled
        self.size = size
        self.hover = False
        self.selected = False
        self.badge = None   # colour of a corner mark, for signature cards

    def handle(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def _lines(self, fit):
        """The label on one line, or on two if it is too wide and has a space to break at."""
        if font(self.size, True).size(self.label)[0] <= fit or " " not in self.label:
            return [self.label]
        words = self.label.split()
        best = min(range(1, len(words)), key=lambda n: abs(len(" ".join(words[:n])) - len(" ".join(words[n:]))))
        return [" ".join(words[:best]), " ".join(words[best:])]

    def draw(self, surf):
        c = self.color if self.enabled else (40, 42, 50)
        if self.hover and self.enabled:
            c = lighten(c, 1.25)
        border = GOLD if self.selected else (0, 0, 0)
        pygame.draw.rect(surf, c, self.rect, border_radius=8)
        pygame.draw.rect(surf, border, self.rect, 3 if self.selected else 2, border_radius=8)
        col = WHITE if self.enabled else (110, 110, 120)
        fit = self.rect.w - 14
        if self.key and not self.sub:
            fit -= 4 if self.wrap else 24  # leave room for the key letter in the corner
        lines = self._lines(fit) if self.wrap and not self.sub else None
        if lines and len(lines) == 2:
            cx = self.rect.centerx + (5 if self.key else 0)
            for k, ln in enumerate(lines):
                text(surf, ln, (cx, self.rect.centery + (k - 0.5) * (self.size - 1)), self.size - 2, col,
                     "center", bold=True, max_width=fit)
        elif self.sub:
            gap = 10 if self.sub_size >= 15 else 7
            text(surf, self.label, (self.rect.centerx, self.rect.centery - gap), self.size,
                 col, "center", bold=True, max_width=fit)
            text(surf, self.sub, (self.rect.centerx, self.rect.centery + gap + 4 * (self.sub_size >= 15)),
                 self.sub_size, GREY, "center", max_width=fit)
        else:
            c = (self.rect.centerx + (8 if self.key else 0), self.rect.centery)
            text(surf, self.label, c, self.size, col, "center", bold=True, max_width=fit)
        if self.key:
            # Punctuation keys (, . ; /) are tiny at letter size
            big = not self.key.isalnum()
            text(surf, self.key, (self.rect.x + 8, self.rect.y + (1 if big else 5)), 20 if big else 15, GOLD,
                 bold=True)
        if self.badge:
            r = self.rect
            pygame.draw.polygon(surf, self.badge, [(r.right - 16, r.y + 2), (r.right - 3, r.y + 2),
                                                   (r.right - 3, r.y + 15)])
