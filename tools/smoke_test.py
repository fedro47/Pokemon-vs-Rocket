"""Prueba automática sin ventana: simula partidas completas de cada nivel.  python tools/smoke_test.py"""
import os, sys, random
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
from game.app import App
from game.data import LEVELS, PLANTS
from game.scenes.play import PlayScene
from game.scenes.menu import MenuScene
from game.scenes.level_select import LevelSelectScene
from game.scenes.settings_menu import SettingsScene
from game.settings import *

def ev(t, **kw): return pygame.event.Event(t, **kw)
def click(s, pos): s.handle_event(ev(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))

app = App()
app.config["unlocked"] = 5
for cls in (MenuScene, LevelSelectScene, SettingsScene):
    s = cls(app); app.go(s)
    for _ in range(5): app.step(1/60)
    click(s, (450, 300)); s.handle_event(ev(pygame.MOUSEBUTTONUP, pos=(450, 300), button=1))
    s.handle_event(ev(pygame.MOUSEMOTION, pos=(420, 150), rel=(0, 0), buttons=(1, 0, 0)))
print("menus OK")

# --- tabla de tipos
from game.tipos import multiplicador, debilidades
assert multiplicador("electric", ["poison", "flying"]) == 2
assert multiplicador("grass", ["poison", "flying"]) == 0.25
assert multiplicador("electric", ["ground"]) == 0.25        # inmune -> 0.25
assert multiplicador("water", ["ground"]) == 2 and multiplicador("fire", []) == 1
assert "electric" in debilidades(["flying"])
print("tipos OK")

# --- selección de mazo
from game.scenes.deck_select import DeckSelectScene
from game.scenes.flow import start_level
from game.settings import MAZO_SLOTS
start_level(app, 1); assert isinstance(app.scene, PlayScene)          # nivel 2: <= slots, entra directo
start_level(app, 4); assert isinstance(app.scene, DeckSelectScene)    # nivel 5: abre selección
d = app.scene; assert len(d.deck) == MAZO_SLOTS
d.draw(app.screen)
click(d, d.slots[0].center); assert len(d.deck) == MAZO_SLOTS - 1     # quitar
extra = [k for k in d.avail if k not in d.deck][0]
click(d, d.rects[extra].center); assert extra in d.deck               # agregar
d.start(); assert isinstance(app.scene, PlayScene) and app.scene.keys == d.deck
assert len(app.scene.cards) == MAZO_SLOTS
app.scene.restart(); assert app.scene.keys == d.deck                  # reintentar conserva el mazo
print("mazo OK")

# --- efectos de tipo en combate
ps = PlayScene(app, 4, deck=["pikachu"]); app.go(ps)
ps.spawn_enemy("zubat", 2, 500); z = list(ps.enemies)[0]; z.hurt(10, None, "electric"); assert abs(z.vida - 40) < 1e-6
ps.spawn_enemy("koffing", 2, 500); k = [e for e in ps.enemies if e.key == "koffing"][0]
k.hurt(1, "veneno", "grass"); assert "veneno" not in k.estados      # veneno es inmune al veneno
from game.entities import Pokemon
pl = Pokemon(ps, "geodude", 2, 3); ps.grid[2][3] = pl; ps.plants.add(pl)
k.x = pl.x; k.rect.centerx = int(k.x); k.y = pl.y; hp = pl.vida
ps.kill_enemy(k); assert pl.vida < hp                               # el gas daña a los Pokémon
print("combate/tipos OK")

def play(level, smart, seconds=700):
    s = PlayScene(app, level); app.go(s)
    random.seed(level)
    for frame in range(60 * seconds):
        if s.state != "playing": break
        if smart and frame % 20 == 0:
            for sun in list(s.suns): click(s, sun.rect.center)
            i = random.randrange(len(s.cards))
            s.select_card(i)
            if s.selected:
                r, c = random.choice(s.rows), random.randrange(0, 6)
                click(s, (col_center_x(c), row_center_y(r)))
        if frame % 500 == 0: s.handle_event(ev(pygame.KEYDOWN, key=pygame.K_f))
        s.update(1/60)
        if frame % 6 == 0: s.draw(app.screen)
    s.draw(app.screen)
    return s

for lv in range(len(LEVELS)):
    s = play(lv, True)
    print(f"nivel {lv+1} con IA ->", s.state, "KO", s.kills, "soles", s.soles)
s = play(0, False)
print("nivel 1 sin plantar ->", s.state)
assert s.state == "lost"
# pausa / overlays
s = PlayScene(app, 0); s.pause(); s.draw(app.screen); s.handle_event(ev(pygame.KEYDOWN, key=pygame.K_ESCAPE)); assert s.state == "playing"
s.win(); s.draw(app.screen); s.lose; print("TODO OK")