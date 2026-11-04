import pygame
from ..settings import *
from ..data import LEVELS, PLANTS
from ..ui import Button, draw_text, gradient, handle_buttons
from .base import Scene

BOX_W, BOX_H, GAP = 150, 270, 17


class LevelSelectScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.bg = gradient((WIDTH, HEIGHT), (60, 120, 190), (30, 60, 110))
        self.unlocked = len(LEVELS) if DEBUG_DESBLOQUEAR_TODO else app.config["unlocked"]
        x0 = (WIDTH - (len(LEVELS) * BOX_W + (len(LEVELS) - 1) * GAP)) // 2
        self.boxes = [pygame.Rect(x0 + i * (BOX_W + GAP), 130, BOX_W, BOX_H) for i in range(len(LEVELS))]
        self.buttons = [Button((WIDTH // 2 - 100, 500, 200, 48), "Volver", self.back)]

    def back(self):
        from .menu import MenuScene
        self.app.go(MenuScene(self.app))

    def start(self, i):
        from .flow import start_level
        start_level(self.app, i)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.back()
            return
        if handle_buttons(self.buttons, e, self.app):
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.boxes):
                if r.collidepoint(e.pos):
                    if i < self.unlocked:
                        self.app.audio.play("click")
                        self.start(i)
                    else:
                        self.app.audio.play("error")

    def draw(self, surf):
        a = self.app.assets
        surf.blit(self.bg, (0, 0))
        draw_text(surf, a.font(42), "Elegí un nivel", (WIDTH // 2, 70), center=True)
        mouse = pygame.mouse.get_pos()
        for i, (r, lv) in enumerate(zip(self.boxes, LEVELS)):
            ok = i < self.unlocked
            col = lv["pasto"][0] if ok else (80, 80, 80)
            if ok and r.collidepoint(mouse):
                col = tuple(min(255, c + 30) for c in col)
            pygame.draw.rect(surf, col, r, border_radius=12)
            pygame.draw.rect(surf, (255, 215, 0) if ok else (120, 120, 120), r, 3, border_radius=12)
            draw_text(surf, a.font(34), str(lv["id"]), (r.centerx, r.y + 30), center=True)
            draw_text(surf, a.font(17), lv["nombre"], (r.centerx, r.y + 70), center=True)
            if ok:
                draw_text(surf, a.font(13, False), lv["desc"], (r.centerx, r.y + 92), center=True)
                for k in range(len(LEVELS)):   # dificultad: círculos rellenos
                    pygame.draw.circle(surf, (255, 215, 0) if k < lv["id"] else (60, 60, 60), (r.centerx - 40 + k * 20, r.y + 116), 6)
                for j, key in enumerate(lv["plantas"]):
                    d = PLANTS[key]
                    ic = a.frames(f"pokemon/{key}", (28, 28), flip=True,
                                  placeholder=("creature", d["color"], d["label"]))[0]
                    surf.blit(ic, (r.x + 14 + (j % 4) * 31, r.y + 140 + (j // 4) * 34))
            else:
                draw_text(surf, a.font(18), "BLOQUEADO", (r.centerx, r.centery + 20), (200, 200, 200), center=True)
        for b in self.buttons:
            b.draw(surf, self.app)