import sys
import pygame
from .settings import *
from .config import Config
from .assets import Assets
from .audio import Audio
from .ui import draw_text


class App:
    def __init__(self):
        pygame.init()
        self.config = Config.load()
        self.screen = None
        self.set_display()
        pygame.display.set_caption(TITLE)
        self.assets = Assets(ASSETS_DIR)
        self.audio = Audio(self.config, ASSETS_DIR)
        self.clock = pygame.time.Clock()
        self.scene = None
        from .scenes.menu import MenuScene
        self.go(MenuScene(self))

    def set_display(self):
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.config["fullscreen"] else 0)
        try:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        except pygame.error:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

    def go(self, scene):
        self.scene = scene

    def quit(self):
        self.config.save()
        pygame.quit()
        sys.exit()

    def step(self, dt):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quit()
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                self.config["fullscreen"] = not self.config["fullscreen"]
                self.set_display()
            else:
                self.scene.handle_event(e)
        self.scene.update(dt)
        self.scene.draw(self.screen)
        if self.config["show_fps"]:
            draw_text(self.screen, self.assets.font(14), f"{self.clock.get_fps():.0f} FPS", (WIDTH - 70, HEIGHT - 20))
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.step(dt)
