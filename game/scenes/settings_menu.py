import pygame
from ..settings import *
from ..ui import Button, Slider, draw_text, gradient, handle_buttons
from .base import Scene

# rango de las perillas de ritmo
LO, HI = 0.25, 2.0


class SettingsScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.cfg = app.config
        self.bg = gradient((WIDTH, HEIGHT), (40, 60, 90), (20, 30, 50))
        to01 = lambda v: (v - LO) / (HI - LO)
        self.sliders = [
            ("Música", Slider((400, 115, 300, 10), self.cfg["music"], self.set_music), "music", lambda v: f"{int(v*100)}%"),
            ("Efectos", Slider((400, 160, 300, 10), self.cfg["sfx"], self.set_sfx), "sfx", lambda v: f"{int(v*100)}%"),
            ("Velocidad de rivales", Slider((400, 205, 300, 10), to01(self.cfg["enemy_speed"]),
                                            lambda v: self.set_range("enemy_speed", v)), "enemy_speed", lambda v: f"{v:.2f}x"),
            ("Tiempo entre oleadas", Slider((400, 250, 300, 10), to01(self.cfg["wave_pace"]),
                                            lambda v: self.set_range("wave_pace", v)), "wave_pace", lambda v: f"{v:.2f}x"),
        ]
        self.buttons = []
        self.rebuild()

    def set_music(self, v):
        self.cfg["music"] = v
        self.app.audio.apply_volumes()

    def set_sfx(self, v):
        self.cfg["sfx"] = v

    def set_range(self, key, v):
        self.cfg[key] = round(LO + (HI - LO) * v, 2)

    def toggle(self, key):
        self.cfg[key] = not self.cfg[key]
        if key == "fullscreen":
            self.app.set_display()
        self.rebuild()

    def reset(self):
        self.cfg.reset_progress()
        self.rebuild()

    def back(self):
        self.cfg.save()
        from .menu import MenuScene
        self.app.go(MenuScene(self.app))

    def rebuild(self):
        yn = lambda v: "Sí" if v else "No"
        c = self.cfg
        self.buttons = [
            Button((300, 295, 300, 44), f"Pantalla completa: {yn(c['fullscreen'])}", lambda: self.toggle("fullscreen"), 22),
            Button((300, 349, 300, 44), f"Temblor de pantalla: {yn(c['shake'])}", lambda: self.toggle("shake"), 22),
            Button((300, 403, 300, 44), f"Mostrar FPS: {yn(c['show_fps'])}", lambda: self.toggle("show_fps"), 22),
            Button((300, 457, 300, 44), "Borrar progreso", self.reset, 22, (170, 70, 70)),
            Button((300, 520, 300, 46), "Volver", self.back, 24, (60, 160, 90)),
        ]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.back()
            return
        for _, s, _, _ in self.sliders:
            s.handle_event(e)
        handle_buttons(self.buttons, e, self.app)

    def draw(self, surf):
        a = self.app.assets
        surf.blit(self.bg, (0, 0))
        draw_text(surf, a.font(40), "Configuración", (WIDTH // 2, 50), center=True)
        for name, s, key, fmt in self.sliders:
            draw_text(surf, a.font(20), name, (150, s.rect.y - 10))
            s.draw(surf)
            draw_text(surf, a.font(18), fmt(self.cfg[key]), (s.rect.right + 30, s.rect.y - 8))
        for b in self.buttons:
            b.draw(surf, self.app)