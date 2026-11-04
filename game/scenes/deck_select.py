import pygame
from ..settings import *
from ..data import LEVELS, PLANTS, ENEMIES
from ..tipos import NOMBRES, debilidades
from ..ui import Button, draw_text, gradient, handle_buttons, draw_tipo_tag
from .base import Scene
from .flow import plantas_disponibles

CW, CH, GAP = 100, 120, 12


class DeckSelectScene(Scene):
    """Elegir el equipo antes del nivel (como las semillas de PvZ)."""

    def __init__(self, app, idx):
        super().__init__(app)
        self.idx, self.level = idx, LEVELS[idx]
        self.avail = plantas_disponibles(idx)
        self.bg = gradient((WIDTH, HEIGHT), (50, 80, 120), (25, 35, 60))
        x0 = (WIDTH - (len(self.avail) * (CW + GAP) - GAP)) // 2
        self.rects = {k: pygame.Rect(x0 + i * (CW + GAP), 95, CW, CH) for i, k in enumerate(self.avail)}
        sx = (WIDTH - (MAZO_SLOTS * (CW + GAP) - GAP)) // 2
        self.slots = [pygame.Rect(sx + i * (CW + GAP), 425, CW, CH) for i in range(MAZO_SLOTS)]
        last = [k for k in app.config["last_deck"] if k in self.avail]
        self.deck = (last or self.avail)[:MAZO_SLOTS]
        o = self.level["olas"]
        self.enemigos = [t for t, _, _ in o["pool"]] + ([o["jefe"]] if o.get("jefe") else [])
        self.erects = [pygame.Rect(40 + i * 64, 312, 56, 56) for i in range(len(self.enemigos))]
        self.btn_back = Button((40, 548, 150, 42), "Volver", self.back, 22)
        self.btn_go = Button((WIDTH - 220, 548, 180, 42), "¡Comenzar!", self.start, 24, (60, 160, 90))
        self.btn_auto = Button((WIDTH // 2 - 75, 548, 150, 42), "Vaciar", self.clear, 20, (120, 90, 60))

    def back(self):
        from .level_select import LevelSelectScene
        self.app.go(LevelSelectScene(self.app))

    def clear(self):
        self.deck = []

    def start(self):
        if not self.deck:
            return
        self.app.config["last_deck"] = list(self.deck)
        self.app.config.save()
        from .play import PlayScene
        self.app.go(PlayScene(self.app, self.idx, deck=list(self.deck)))

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.back()
            return
        self.btn_go.enabled = bool(self.deck)
        if handle_buttons([self.btn_back, self.btn_go, self.btn_auto], e, self.app):
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for k, r in self.rects.items():
                if r.collidepoint(e.pos):
                    if k in self.deck:
                        self.deck.remove(k)
                        self.app.audio.play("click")
                    elif len(self.deck) < MAZO_SLOTS:
                        self.deck.append(k)
                        self.app.audio.play("plant", .5)
                    else:
                        self.app.audio.play("error")
                    return
            for i, r in enumerate(self.slots):
                if i < len(self.deck) and r.collidepoint(e.pos):
                    self.deck.pop(i)
                    self.app.audio.play("click")
                    return

    # ---------------------------------------------------------------- dibujo
    def _icon(self, key, size):
        d = PLANTS[key]
        return self.app.assets.frames(f"pokemon/{key}", (size, size), flip=True,
                                      placeholder=("creature", d["color"], d["label"]))[0]

    def _card(self, surf, key, r, dim=False):
        a = self.app.assets
        d = PLANTS[key]
        pygame.draw.rect(surf, (110, 105, 95) if dim else (235, 225, 190), r, border_radius=8)
        pygame.draw.rect(surf, (30, 30, 30), r, 2, border_radius=8)
        surf.blit(self._icon(key, 62), (r.centerx - 31, r.y + 15))
        draw_text(surf, a.font(15), d["nombre"], (r.centerx, r.y + 86), (30, 20, 0), center=True, shadow=False)
        draw_text(surf, a.font(14), str(d["costo"]), (r.x + 8, r.bottom - 20), (30, 20, 0), shadow=False)
        draw_tipo_tag(surf, a, d["tipo"], (r.right - 60, r.bottom - 21), 11)

    def draw(self, surf):
        a = self.app.assets
        mouse = pygame.mouse.get_pos()
        surf.blit(self.bg, (0, 0))
        draw_text(surf, a.font(32), f"Elegí tu equipo ({len(self.deck)}/{MAZO_SLOTS})", (WIDTH // 2, 40), center=True)
        draw_text(surf, a.font(15, False), f"{self.level['nombre']} - clic en una carta para sumarla o quitarla",
                  (WIDTH // 2, 70), (210, 210, 210), center=True)
        tip = None
        for k, r in self.rects.items():
            self._card(surf, k, r, dim=k in self.deck)
            if k in self.deck:   # cinta verde arriba de la carta
                rib = pygame.Rect(r.x + 2, r.y + 2, r.w - 4, 14)
                pygame.draw.rect(surf, (60, 160, 90), rib, border_radius=5)
                draw_text(surf, a.font(11), "EN EL EQUIPO", rib.center, center=True, shadow=False)
            if r.collidepoint(mouse):
                tip = ("p", k)
        # enemigos
        draw_text(surf, a.font(17), "Enemigos de este nivel (pasá el mouse para ver sus debilidades):", (40, 286))
        for k, r in zip(self.enemigos, self.erects):
            d = ENEMIES[k]
            pygame.draw.rect(surf, (60, 40, 50), r, border_radius=6)
            surf.blit(a.frames(f"rocket/{k}", (50, 50), placeholder=d["placeholder"])[0], (r.x + 3, r.y + 3))
            for j, t in enumerate(d.get("tipos", [])):
                from ..tipos import COLORES
                pygame.draw.circle(surf, COLORES[t], (r.x + 8 + j * 12, r.bottom - 6), 5)
                pygame.draw.circle(surf, (0, 0, 0), (r.x + 8 + j * 12, r.bottom - 6), 5, 1)
            if r.collidepoint(mouse):
                tip = ("e", k)
        # equipo
        draw_text(surf, a.font(17), "Tu equipo:", (self.slots[0].x, 398))
        for i, r in enumerate(self.slots):
            if i < len(self.deck):
                self._card(surf, self.deck[i], r)
                draw_text(surf, a.font(12), str(i + 1), (r.x + 6, r.y + 4), (60, 40, 0), shadow=False)
                if r.collidepoint(mouse):
                    tip = ("p", self.deck[i])
            else:
                pygame.draw.rect(surf, (20, 25, 40), r, border_radius=8)
                pygame.draw.rect(surf, (90, 100, 130), r, 2, border_radius=8)
        # tooltip
        box = pygame.Rect(40, 226, 820, 50)
        pygame.draw.rect(surf, (20, 25, 40), box, border_radius=6)
        if tip and tip[0] == "p":
            d = PLANTS[tip[1]]
            draw_text(surf, a.font(17), f"{d['nombre']} ({NOMBRES[d['tipo']]})  -  costo {d['costo']}, recarga {d['recarga']:g}s, vida {d['vida']}",
                      (box.x + 10, box.y + 6))
            draw_text(surf, a.font(15, False), d["desc"], (box.x + 10, box.y + 28), (220, 220, 220), shadow=False)
        elif tip:
            d = ENEMIES[tip[1]]
            t = d.get("tipos", [])
            draw_text(surf, a.font(17), f"{d['nombre']}  ({'/'.join(NOMBRES[x] for x in t) if t else 'sin tipo'})   vida {d['vida']}",
                      (box.x + 10, box.y + 6))
            deb = debilidades(t)
            draw_text(surf, a.font(15, False), "Débil a: " + (", ".join(NOMBRES[x] for x in deb) if deb else "ningún tipo en particular"),
                      (box.x + 10, box.y + 28), (255, 230, 120), shadow=False)
        else:
            draw_text(surf, a.font(15, False), "Pasá el mouse sobre un Pokémon o un enemigo para ver detalles.",
                      (box.x + 10, box.y + 16), (170, 170, 170), shadow=False)
        self.btn_go.enabled = bool(self.deck)
        for b in (self.btn_back, self.btn_auto, self.btn_go):
            b.draw(surf, self.app)