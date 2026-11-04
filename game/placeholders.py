"""Sprites dibujados por código. Se usan cuando falta el archivo real, así el juego
siempre se ve decente aunque no tengas ninguna imagen cargada."""
import math
import random
import pygame


def _dark(c, n=60):
    return tuple(max(0, v - n) for v in c)


def _light(c, n=60):
    return tuple(min(255, v + n) for v in c)


def creature(size, color, label=""):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    for ex in (0.2, 0.58):  # orejas
        pts = [(w * ex, h * 0.3), (w * (ex + 0.2), h * 0.3), (w * (ex + 0.1), h * 0.03)]
        pygame.draw.polygon(s, color, pts)
        pygame.draw.polygon(s, _dark(color), pts, 2)
    body = pygame.Rect(int(w * .08), int(h * .2), int(w * .84), int(h * .76))
    pygame.draw.ellipse(s, color, body)
    pygame.draw.ellipse(s, _dark(color), body, 3)
    for ex in (0.45, 0.72):  # ojos (miran a la derecha)
        pygame.draw.circle(s, (255, 255, 255), (int(w * ex), int(h * .42)), max(3, int(w * .09)))
        pygame.draw.circle(s, (20, 20, 20), (int(w * ex + 2), int(h * .42)), max(2, int(w * .045)))
    if label:
        f = pygame.font.Font(None, int(h * .4))
        t = f.render(label[0].upper(), True, _dark(color, 100))
        s.blit(t, t.get_rect(center=(w * .5, h * .74)))
    return s


def rocket(size, variant="grunt"):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    boss = variant == "giovanni"
    suit = (60, 50, 70) if boss else (235, 235, 235)
    pygame.draw.rect(s, (40, 40, 50), (w * .28, h * .68, w * .18, h * .3))   # piernas
    pygame.draw.rect(s, (40, 40, 50), (w * .54, h * .68, w * .18, h * .3))
    torso = pygame.Rect(int(w * .18), int(h * .36), int(w * .64), int(h * .38))
    pygame.draw.rect(s, suit, torso, border_radius=6)
    pygame.draw.rect(s, (30, 30, 30), torso, 2, border_radius=6)
    f = pygame.font.Font(None, int(h * .36))
    t = f.render("R", True, (220, 30, 30))
    s.blit(t, t.get_rect(center=torso.center))
    pygame.draw.circle(s, (240, 200, 160), (int(w * .5), int(h * .22)), int(w * .22))
    pygame.draw.circle(s, (30, 30, 30), (int(w * .42), int(h * .22)), 2)
    pygame.draw.circle(s, (30, 30, 30), (int(w * .58), int(h * .22)), 2)
    hair = {"grunt": (30, 30, 40), "casco": (150, 155, 165), "giovanni": (200, 110, 40)}.get(variant, (30, 30, 40))
    pygame.draw.arc(s, hair, (w * .26, h * .0, w * .48, h * .3), 0, math.pi, int(h * .09))
    if variant == "casco":
        pygame.draw.rect(s, hair, (w * .26, h * .06, w * .48, h * .1), border_radius=4)
    return s


def sun(size):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    c, r = (w // 2, h // 2), min(w, h) // 2
    for i in range(12):
        a = i * math.pi / 6
        p1 = (c[0] + math.cos(a) * r * .62, c[1] + math.sin(a) * r * .62)
        p2 = (c[0] + math.cos(a) * r * .98, c[1] + math.sin(a) * r * .98)
        pygame.draw.line(s, (255, 190, 0), p1, p2, 3)
    pygame.draw.circle(s, (255, 150, 0), c, int(r * .66))
    pygame.draw.circle(s, (255, 215, 20), c, int(r * .6))
    pygame.draw.circle(s, (255, 245, 150), (c[0] - 3, c[1] - 3), int(r * .32))
    return s


def orb(size, inner, outer):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    c, r = (w // 2, h // 2), min(w, h) // 2
    pygame.draw.circle(s, (*outer, 90), c, r)
    pygame.draw.circle(s, outer, c, int(r * .78))
    pygame.draw.circle(s, inner, c, int(r * .5))
    pygame.draw.circle(s, (255, 255, 255), (c[0] - r // 4, c[1] - r // 4), max(1, r // 5))
    return s


def bolt(size):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    pts = [(w * .55, 0), (w * .1, h * .55), (w * .45, h * .55), (w * .3, h), (w * .92, h * .35), (w * .55, h * .35)]
    pygame.draw.polygon(s, (255, 235, 40), pts)
    pygame.draw.polygon(s, (230, 150, 0), pts, 2)
    return s


def mower(size):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(s, (200, 40, 40), (w * .08, h * .2, w * .84, h * .5), border_radius=6)
    pygame.draw.rect(s, (255, 255, 255), (w * .08, h * .38, w * .84, h * .1))
    pygame.draw.rect(s, (60, 60, 60), (w * .08, h * .2, w * .84, h * .5), 2, border_radius=6)
    for x in (.28, .72):
        pygame.draw.circle(s, (30, 30, 30), (int(w * x), int(h * .78)), int(h * .2))
        pygame.draw.circle(s, (170, 170, 170), (int(w * x), int(h * .78)), int(h * .08))
    return s


def pokeball(size):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    c, r = (w // 2, h // 2), min(w, h) // 2 - 1
    pygame.draw.circle(s, (240, 240, 240), c, r)
    pygame.draw.rect(s, (220, 40, 40), (0, 0, w, h // 2))
    pygame.draw.circle(s, (240, 240, 240), c, r, 0, draw_bottom_left=True, draw_bottom_right=True)
    s2 = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(s2, (220, 40, 40), c, r, 0, draw_top_left=True, draw_top_right=True)
    pygame.draw.circle(s, (20, 20, 20), c, r, 2)
    s.blit(s2, (0, 0))
    pygame.draw.line(s, (20, 20, 20), (0, h // 2), (w, h // 2), 3)
    pygame.draw.circle(s, (250, 250, 250), c, max(3, r // 3))
    pygame.draw.circle(s, (20, 20, 20), c, max(3, r // 3), 2)
    return s


def logo(size):
    w, h = size
    s = pygame.Surface(size, pygame.SRCALPHA)
    c, r = (w // 2, h // 2), min(w, h) // 2 - 1
    pygame.draw.circle(s, (25, 25, 30), c, r)
    pygame.draw.circle(s, (210, 35, 35), c, r, max(2, r // 6))
    f = pygame.font.Font(None, int(h * .85))
    t = f.render("R", True, (230, 40, 40))
    s.blit(t, t.get_rect(center=(c[0], c[1] + 1)))
    return s


def tile(size, color):
    w, h = size
    s = pygame.Surface(size)
    s.fill(color)
    rnd = random.Random(sum(color))
    for _ in range(14):
        x, y = rnd.randint(2, w - 3), rnd.randint(2, h - 3)
        pygame.draw.line(s, _light(color, 18), (x, y), (x + 2, y - 4), 1)
    return s


_KINDS = {"creature": creature, "rocket": rocket, "sun": sun, "orb": orb, "bolt": bolt,
          "mower": mower, "pokeball": pokeball, "tile": tile, "logo": logo}


def make(spec, size):
    kind, *args = spec
    return _KINDS[kind](size, *args)