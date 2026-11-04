import math
import random
import pygame
from ..settings import *
from ..ui import Button, draw_text, gradient, handle_buttons
from .base import Scene


class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        app.audio.play_music("menu")
        cx = WIDTH // 2
        self.buttons = [
            Button((cx - 130, 290, 260, 54), "Jugar", self.play, color=(60, 160, 90)),
            Button((cx - 130, 360, 260, 54), "Configuración", self.settings),
            Button((cx - 130, 430, 260, 54), "Salir", app.quit, color=(170, 70, 70)),
        ]
        bg = app.assets.frames(["backgrounds/menu", "backgrounds/fondo"], (WIDTH, HEIGHT), mode="stretch")
        self.bg = bg[0] if bg else gradient((WIDTH, HEIGHT), (120, 190, 240), (70, 150, 80))
        self.ball = app.assets.frames("items/pokebola", (34, 34), placeholder=("pokeball",))[0]
        self.balls = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(-40, 40),
                       random.uniform(-40, 40)] for _ in range(10)]
        lg = app.assets.frames("items/logo_titulo", (560, 190))
        self.logo = lg[0] if lg else None   # si ponés assets/images/items/logo_titulo.png, reemplaza al texto
        self.t = 0

    def play(self):
        from .level_select import LevelSelectScene
        self.app.go(LevelSelectScene(self.app))

    def settings(self):
        from .settings_menu import SettingsScene
        self.app.go(SettingsScene(self.app))

    def handle_event(self, e):
        handle_buttons(self.buttons, e, self.app)

    def update(self, dt):
        self.t += dt
        for b in self.balls:
            b[0] = (b[0] + b[2] * dt) % WIDTH
            b[1] = (b[1] + b[3] * dt) % HEIGHT

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 90))
        surf.blit(dark, (0, 0))
        for b in self.balls:
            surf.blit(self.ball, (b[0], b[1]))
        a = self.app.assets
        y = 90 + math.sin(self.t * 2) * 6
        if self.logo:
            surf.blit(self.logo, self.logo.get_rect(center=(WIDTH // 2, y + 40)))
        else:
            draw_text(surf, a.font(72), "POKÉMON", (WIDTH // 2, y), (255, 215, 40), center=True)
            draw_text(surf, a.font(44), "vs TEAM ROCKET", (WIDTH // 2, y + 66), (255, 90, 90), center=True)
        draw_text(surf, a.font(16, False), "Defendé tu equipo de los villanos. F11: pantalla completa",
                  (WIDTH // 2, HEIGHT - 24), (230, 230, 230), center=True)
        for b in self.buttons:
            b.draw(surf, self.app)