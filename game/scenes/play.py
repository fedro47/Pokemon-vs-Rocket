import math
import random
import pygame
from ..settings import *
from ..data import PLANTS, LEVELS, generar_olas
from ..tipos import NOMBRES, COLORES, debilidades
from ..entities import Pokemon, Enemy, Mower, Sun, Particle, FloatText
from ..ui import Button, draw_text, gradient, handle_buttons
from .base import Scene
from .flow import plantas_disponibles, start_level

CARD_X0, CARD_Y, CARD_W, CARD_H, CARD_GAP = 118, 8, 70, 68, 6
SUN_RECT = pygame.Rect(10, 8, 100, 68)
SHOVEL_RECT = pygame.Rect(652, 8, 62, 68)
PAUSE_RECT = pygame.Rect(728, 8, 78, 32)
SPEED_RECT = pygame.Rect(812, 8, 78, 32)
INFO_RECT = pygame.Rect(728, 44, 162, 32)


class PlayScene(Scene):
    def __init__(self, app, level_index, deck=None):
        super().__init__(app)
        self.assets, self.audio, self.cfg = app.assets, app.audio, app.config
        self.level_index = level_index
        self.level = LEVELS[level_index]
        self.rows = self.level["filas"]
        self.waves = generar_olas(**self.level["olas"])
        for w in self.waves:                      # perilla de Configuración: tiempo entre oleadas
            w["espera"] *= app.config["wave_pace"]
        self.keys = list(deck) if deck else plantas_disponibles(level_index)
        self.soles = self.level["soles_iniciales"]
        self.state, self.speed, self.selected = "playing", 1, None

        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.plants = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.suns = pygame.sprite.Group()
        self.mowers = pygame.sprite.Group()
        self.particles, self.texts = [], []
        for f in self.rows:
            self.mowers.add(Mower(self, f))

        self.cards, self.cd = [], {}
        for i, key in enumerate(self.keys):
            self.cards.append(dict(key=key, rect=pygame.Rect(CARD_X0 + i * (CARD_W + CARD_GAP), CARD_Y, CARD_W, CARD_H)))
            self.cd[key] = 0.0

        self.wave_i, self.wave_timer = 0, self.waves[0]["espera"]
        self.wave_span = max(1.0, self.wave_timer)
        self.prog = 0.0
        self.pending = []
        self.sky_timer = 5.0
        self.banner = None          # [texto, tiempo, color]
        self.hint = ["", 0.0]
        self.shake = 0.0
        self.kills = 0
        self.new_unlock = []
        self.overlay_buttons = []

        self.board = self._build_board()
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.sun_icon = self.assets.frames("items/sol", (40, 40), placeholder=("sun",))[0]
        self.shovel_icon = self.assets.frames("items/pokebola", (34, 34), placeholder=("pokeball",))[0]
        self.icons, self.ghosts = {}, {}
        for key in self.keys:
            d = PLANTS[key]
            ph = ("creature", d["color"], d["label"])
            self.icons[key] = self.assets.frames(f"pokemon/{key}", (40, 40), flip=True, placeholder=ph)[0]
            g = self.assets.frames(f"pokemon/{key}", d.get("size", (60, 70)), flip=True, placeholder=ph)[0].copy()
            g.set_alpha(130)
            self.ghosts[key] = g
        self.set_banner(f"Nivel {self.level['id']}: {self.level['nombre']}", 3.0, (255, 255, 255))
        self.audio.play_music("game")

    # ------------------------------------------------------------ construcción
    def _build_board(self):
        lv = self.level
        s = pygame.Surface((WIDTH, HEIGHT))
        bg = self.assets.frames([f"backgrounds/level_{lv['id']}", "backgrounds/fondo"], (WIDTH, HEIGHT), mode="stretch")
        s.blit(bg[0] if bg else gradient((WIDTH, HEIGHT), lv["cielo"], _darker(lv["cielo"])), (0, 0))
        t = []
        for n in (1, 2):
            fr = self.assets.frames([f"tiles/level_{lv['id']}_{n}", f"tiles/pasto{n}"], (CELL_W, CELL_H),
                                    placeholder=("tile", lv["pasto"][n - 1]), mode="stretch")
            t.append(fr[0])
        dim = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
        dim.fill((30, 20, 10, 170))
        for f in range(ROWS):
            for c in range(COLS):
                x, y = GRID_X + c * CELL_W, GRID_Y + f * CELL_H
                s.blit(t[(f + c) % 2], (x, y))
                if f not in self.rows:
                    s.blit(dim, (x, y))
        pygame.draw.rect(s, (0, 0, 0), (GRID_X, GRID_Y, COLS * CELL_W, ROWS * CELL_H), 2)
        return s

    # ------------------------------------------------------------ API para entidades
    def add_sun(self, n):
        self.soles += n

    def add_text(self, x, y, text, color=(255, 255, 255)):
        self.texts.append(FloatText(self.assets.font(18), x, y, text, color))

    def set_banner(self, text, t, color):
        self.banner = [text, t, color]

    def enemy_ahead(self, fila, x):
        return any(e.fila == fila and e.x > x and e.rect.left < WIDTH for e in self.enemies)

    def plant_in_front(self, e):
        front = e.x - e.rect.w * 0.25
        col = int((front - GRID_X) // CELL_W)
        if 0 <= col < COLS:
            p = self.grid[e.fila][col]
            if p and front <= GRID_X + col * CELL_W + 70:
                return p
        return None

    def nearest_sun(self, x):
        best = None
        for s in self.suns:
            if s.state == "wait" and abs(s.x - x) < 260 and (best is None or abs(s.x - x) < abs(best.x - x)):
                best = s
        return best

    def spawn_enemy(self, key, fila, x=None):
        self.enemies.add(Enemy(self, key, fila, x))

    def spawn_plant_sun(self, p):
        self.suns.add(Sun(self, p.x, p.y - 10, p.y + 25, SUN_VALUE, hop=True))

    def remove_plant(self, p):
        if p.muerto:
            return
        p.muerto = True
        if self.grid[p.fila][p.col] is p:
            self.grid[p.fila][p.col] = None
        for _ in range(8):
            self.particles.append(Particle(p.x, p.y, random.uniform(-70, 70), random.uniform(-90, 10),
                                           .5, p.d["color"], 5, 200))
        p.kill()

    def kill_enemy(self, e):
        if e.muerto:
            return
        e.muerto = True
        self.kills += 1
        for _ in range(10):
            self.particles.append(Particle(e.x, e.y, random.uniform(-80, 80), random.uniform(-100, 20),
                                           .55, random.choice([(255, 255, 255), (200, 200, 200), (255, 90, 90)]), 5, 220))
        self.audio.play("defeat", .6)
        if e.d.get("ladron"):
            self.suns.add(Sun(self, e.x, e.y, e.y + 20, 50, hop=True))
        elif random.random() < 0.06:
            self.suns.add(Sun(self, e.x, e.y, e.y + 20, SUN_VALUE, hop=True))
        ex = e.d.get("explota")
        if ex:
            self.audio.play("explosion", .6)
            self.add_text(e.x, e.y - 40, "¡Gas tóxico!", (200, 130, 230))
            for _ in range(25):
                a, v = random.uniform(0, 6.28), random.uniform(20, 120)
                self.particles.append(Particle(e.x, e.y, math.cos(a) * v, math.sin(a) * v, random.uniform(.4, .9),
                                               random.choice([(160, 90, 200), (120, 70, 160), (190, 150, 220)]), 7))
            for pl in list(self.plants):
                if math.hypot(pl.x - e.x, pl.y - e.y) <= ex["radio"]:
                    pl.hurt(ex["dano"])
        e.kill()

    def explode(self, x, y, radio, dano, tipo=None):
        self.audio.play("explosion")
        if self.cfg["shake"]:
            self.shake = 0.35
        for _ in range(40):
            a, v = random.uniform(0, 6.28), random.uniform(40, 260)
            self.particles.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v, random.uniform(.3, .7),
                                           random.choice([(255, 200, 40), (255, 120, 30), (255, 60, 30), (90, 90, 90)]), 8))
        for e in list(self.enemies):
            if math.hypot(e.x - x, e.y - y) <= radio:
                e.hurt(dano, None, tipo)

    def lose(self):
        if self.state != "playing":
            return
        self.state = "lost"
        self.selected = None
        self.audio.stop_music()
        self.audio.play("lose")
        self.overlay_buttons = [
            Button((WIDTH // 2 - 110, 380, 220, 48), "Reintentar", self.restart, color=(60, 160, 90)),
            Button((WIDTH // 2 - 110, 440, 220, 48), "Menú de niveles", self.to_levels),
        ]

    def win(self):
        self.state = "won"
        self.selected = None
        self.audio.stop_music()
        self.audio.play("win")
        nxt = self.level_index + 1
        if nxt < len(LEVELS):
            old = set(self.level["plantas"])
            self.new_unlock = [PLANTS[k]["nombre"] for k in LEVELS[nxt]["plantas"] if k not in old]
            self.cfg["unlocked"] = max(self.cfg["unlocked"], nxt + 1)
        self.cfg.save()
        self.overlay_buttons = []
        y = 390
        if nxt < len(LEVELS):
            self.overlay_buttons.append(Button((WIDTH // 2 - 110, y, 220, 48), "Siguiente nivel", self.next_level, color=(60, 160, 90)))
            y += 58
        self.overlay_buttons.append(Button((WIDTH // 2 - 110, y, 220, 48), "Menú de niveles", self.to_levels))

    # ------------------------------------------------------------ navegación
    def restart(self):
        self.app.go(PlayScene(self.app, self.level_index, deck=self.keys))

    def next_level(self):
        start_level(self.app, self.level_index + 1)

    def to_levels(self):
        from .level_select import LevelSelectScene
        self.app.go(LevelSelectScene(self.app))

    def pause(self):
        self.state = "paused"
        self.selected = None
        self.overlay_buttons = [
            Button((WIDTH // 2 - 110, 260, 220, 48), "Reanudar", self.resume, color=(60, 160, 90)),
            Button((WIDTH // 2 - 110, 320, 220, 48), "Reiniciar", self.restart),
            Button((WIDTH // 2 - 110, 380, 220, 48), "Menú de niveles", self.to_levels, color=(170, 70, 70)),
        ]

    def resume(self):
        self.state = "playing"

    # ------------------------------------------------------------ input
    def say(self, text):
        self.hint = [text, 2.0]
        self.audio.play("error")

    def select_card(self, i):
        if i >= len(self.cards):
            return
        key = self.cards[i]["key"]
        d = PLANTS[key]
        if self.selected == key:
            self.selected = None
        elif self.cd[key] > 0:
            self.say("¡Todavía se está recargando!")
        elif self.soles < d["costo"]:
            self.say("No tenés suficientes soles.")
        else:
            self.selected = key
            self.audio.play("click")

    def cell_at(self, pos):
        x, y = pos
        if GRID_X <= x < GRID_X + COLS * CELL_W and GRID_Y <= y < GRID_Y + ROWS * CELL_H:
            return (y - GRID_Y) // CELL_H, (x - GRID_X) // CELL_W
        return None

    def handle_event(self, e):
        if self.state in ("paused", "won", "lost"):
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_p) and self.state == "paused":
                self.resume()
            else:
                handle_buttons(self.overlay_buttons, e, self.app)
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_p):
                self.pause()
            elif pygame.K_1 <= e.key <= pygame.K_9:
                self.select_card(e.key - pygame.K_1)
            elif e.key == pygame.K_q:
                self.selected = None if self.selected == "pala" else "pala"
            elif e.key == pygame.K_f:
                self.speed = 2 if self.speed == 1 else 1
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 3:
                self.selected = None
            elif e.button == 1:
                self.click(e.pos)

    def click(self, pos):
        for s in sorted(self.suns, key=lambda s: -s.y):
            if s.state != "fly" and s.hitrect.collidepoint(pos):
                s.collect()
                return
        if PAUSE_RECT.collidepoint(pos):
            self.audio.play("click")
            self.pause()
            return
        if SPEED_RECT.collidepoint(pos):
            self.audio.play("click")
            self.speed = 2 if self.speed == 1 else 1
            return
        for i, c in enumerate(self.cards):
            if c["rect"].collidepoint(pos):
                self.select_card(i)
                return
        if SHOVEL_RECT.collidepoint(pos):
            self.audio.play("click")
            self.selected = None if self.selected == "pala" else "pala"
            return
        cell = self.cell_at(pos)
        if not cell or not self.selected:
            return
        f, c = cell
        if self.selected == "pala":
            p = self.grid[f][c]
            if p:
                self.remove_plant(p)
                self.audio.play("shovel")
            self.selected = None
            return
        key = self.selected
        d = PLANTS[key]
        if f not in self.rows:
            self.say("Ahí no se puede plantar.")
        elif self.grid[f][c]:
            self.say("La casilla está ocupada.")
        elif self.soles < d["costo"]:
            self.say("No tenés suficientes soles.")
            self.selected = None
        else:
            p = Pokemon(self, key, f, c)
            self.grid[f][c] = p
            self.plants.add(p)
            self.soles -= d["costo"]
            self.cd[key] = d["recarga"]
            self.selected = None
            self.audio.play("plant")
            for _ in range(6):
                self.particles.append(Particle(p.x, p.y + 25, random.uniform(-50, 50), random.uniform(-40, 0),
                                               .4, (230, 230, 200), 4))

    # ------------------------------------------------------------ lógica
    def start_wave(self):
        w = self.waves[self.wave_i]
        for tipo, n in w["enemigos"].items():
            for _ in range(n):
                self.pending.append([random.uniform(0, 12 if w["bandera"] else 6), tipo])
        if w["bandera"]:
            final = self.wave_i == len(self.waves) - 1
            self.set_banner("¡OLEADA FINAL!" if final else "¡UNA OLEADA ENORME SE ACERCA!", 3.5, (255, 90, 90))
            self.audio.play("wave")
        self.wave_i += 1
        if self.wave_i < len(self.waves):
            self.wave_timer = self.waves[self.wave_i]["espera"]
            self.wave_span = max(1.0, self.wave_timer)

    def update(self, dt):
        if self.state == "paused":
            return
        if self.state == "playing":
            dt *= self.speed * GAME_SPEED
            self.update_world(dt)
        else:   # ganó/perdió: solo animar partículas
            self.update_fx(dt)

    def update_fx(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.life > 0]
        self.shake = max(0.0, self.shake - dt)
        if self.banner:
            self.banner[1] -= dt
            if self.banner[1] <= 0:
                self.banner = None
        self.hint[1] -= dt

    def update_world(self, dt):
        # soles del cielo
        self.sky_timer -= dt
        if self.sky_timer <= 0:
            self.sky_timer = random.uniform(8, 11)
            self.suns.add(Sun(self, random.randint(GRID_X, WIDTH - 100), -30,
                              random.randint(GRID_Y + 20, GRID_Y + ROWS * CELL_H - 40)))
        # oleadas
        for it in self.pending[:]:
            it[0] -= dt
            if it[0] <= 0:
                self.pending.remove(it)
                self.spawn_enemy(it[1], random.choice(self.rows))
        if self.wave_i < len(self.waves):
            if self.wave_i > 0 and not self.enemies and not self.pending and self.wave_timer > 10:
                self.wave_timer = 10     # si limpiaste todo, se adelanta un poco la siguiente
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.start_wave()
        for k in self.cd:
            self.cd[k] = max(0.0, self.cd[k] - dt)
        self.prog += (self._progress_target() - self.prog) * min(1.0, dt * 3)
        self.mowers.update(dt)
        self.plants.update(dt)
        self.enemies.update(dt)
        self.projectiles.update(dt)
        self.suns.update(dt)
        self.update_fx(dt)
        if self.state == "playing" and self.wave_i >= len(self.waves) and not self.pending and not self.enemies:
            self.win()

    # ------------------------------------------------------------ dibujo
    def draw(self, surf):
        c = self.canvas
        c.blit(self.board, (0, 0))
        self._draw_hover(c)
        self.mowers.draw(c)
        self.plants.draw(c)
        for e in sorted(self.enemies, key=lambda e: e.rect.bottom):
            c.blit(e.image, e.rect)
        self.projectiles.draw(c)
        self._draw_bars(c)
        for p in self.particles:
            p.draw(c)
        for s in self.suns:
            if s.visible:
                c.blit(s.image, s.rect)
        for t in self.texts:
            t.draw(c)
        ox = oy = 0
        if self.shake > 0 and self.cfg["shake"]:
            ox, oy = random.randint(-5, 5), random.randint(-5, 5)
        surf.fill((0, 0, 0))
        surf.blit(c, (ox, oy))
        self._draw_topbar(surf)
        self._draw_progress(surf)
        self._draw_banner(surf)
        self._draw_ghost(surf)
        if self.state != "playing":
            self._draw_overlay(surf)

    def _draw_hover(self, c):
        if not self.selected:
            return
        cell = self.cell_at(pygame.mouse.get_pos())
        if not cell:
            return
        f, col = cell
        ok = f in self.rows and (self.grid[f][col] is not None if self.selected == "pala" else self.grid[f][col] is None)
        color = (255, 255, 255, 70) if ok else (255, 40, 40, 80)
        if self.selected == "pala" and ok:
            color = (255, 200, 40, 90)
        r = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
        r.fill(color)
        c.blit(r, (GRID_X + col * CELL_W, GRID_Y + f * CELL_H))

    def _draw_ghost(self, surf):
        if self.selected and self.selected != "pala":
            cell = self.cell_at(pygame.mouse.get_pos())
            if cell and cell[0] in self.rows and not self.grid[cell[0]][cell[1]]:
                g = self.ghosts[self.selected]
                surf.blit(g, g.get_rect(center=(col_center_x(cell[1]), row_center_y(cell[0]))))
            else:
                g = self.ghosts[self.selected]
                surf.blit(g, g.get_rect(center=pygame.mouse.get_pos()))

    def _draw_bars(self, c):
        for p in self.plants:
            if p.vida < p.vida_max:
                pygame.draw.rect(c, (255, 0, 0), (p.rect.x, p.rect.y - 10, 50, 6))
                pygame.draw.rect(c, (0, 255, 0), (p.rect.x, p.rect.y - 10, 50 * max(0, p.vida) / p.vida_max, 6))
        for e in self.enemies:
            if e.vida < e.vida_max or e.jefe:
                w = 90 if e.jefe else 40
                x, y = e.rect.centerx - w // 2, e.rect.y - 10
                pygame.draw.rect(c, (0, 0, 0), (x, y, w, 6))
                pygame.draw.rect(c, (255, 60, 60), (x, y, w * max(0, e.vida) / e.vida_max, 6))
            for j, t in enumerate(e.tipos):   # puntitos de tipo sobre el enemigo
                pygame.draw.circle(c, COLORES[t], (e.rect.centerx - 6 * (len(e.tipos) - 1) + j * 12, e.rect.y - 18), 4)
                pygame.draw.circle(c, (0, 0, 0), (e.rect.centerx - 6 * (len(e.tipos) - 1) + j * 12, e.rect.y - 18), 4, 1)

    def _draw_topbar(self, surf):
        a = self.assets
        pygame.draw.rect(surf, (60, 60, 60), (0, 0, WIDTH, TOPBAR_H))
        pygame.draw.line(surf, (255, 255, 255), (0, TOPBAR_H), (WIDTH, TOPBAR_H), 3)
        pygame.draw.rect(surf, (220, 200, 140), SUN_RECT, border_radius=6)
        surf.blit(self.sun_icon, self.sun_icon.get_rect(center=(SUN_ICON_POS[0], SUN_ICON_POS[1] - 10)))
        draw_text(surf, a.font(26), str(self.soles), (SUN_RECT.centerx, SUN_RECT.bottom - 14), (40, 30, 0), center=True, shadow=False)
        mouse = pygame.mouse.get_pos()
        tip = ""
        for i, card in enumerate(self.cards):
            key, r = card["key"], card["rect"]
            d = PLANTS[key]
            ready = self.cd[key] <= 0 and self.soles >= d["costo"]
            pygame.draw.rect(surf, (235, 225, 190) if ready else (110, 105, 95), r, border_radius=5)
            surf.blit(self.icons[key], self.icons[key].get_rect(center=(r.centerx, r.y + 28)))
            draw_text(surf, a.font(15), str(d["costo"]), (r.centerx, r.bottom - 11), (30, 20, 0) if ready else (200, 60, 60), center=True, shadow=False)
            draw_text(surf, a.font(11), str(i + 1), (r.x + 4, r.y + 2), (60, 40, 0), shadow=False)
            pygame.draw.circle(surf, COLORES[d["tipo"]], (r.right - 9, r.y + 9), 5)
            pygame.draw.circle(surf, (0, 0, 0), (r.right - 9, r.y + 9), 5, 1)
            cdv = self.cd[key]
            if cdv > 0:
                h = int(r.h * cdv / d["recarga"])
                sh = pygame.Surface((r.w, h), pygame.SRCALPHA)
                sh.fill((0, 0, 0, 150))
                surf.blit(sh, r.topleft)
            sel = self.selected == key
            pygame.draw.rect(surf, (255, 215, 0) if sel else (30, 30, 30), r, 4 if sel else 1, border_radius=5)
            if r.collidepoint(mouse):
                tip = f"{d['nombre']} ({NOMBRES[d['tipo']]}): {d['desc']}"
        sel = self.selected == "pala"
        pygame.draw.rect(surf, (200, 60, 60) if sel else (110, 55, 55), SHOVEL_RECT, border_radius=5)
        pygame.draw.rect(surf, (255, 215, 0) if sel else (30, 30, 30), SHOVEL_RECT, 4 if sel else 1, border_radius=5)
        surf.blit(self.shovel_icon, self.shovel_icon.get_rect(center=(SHOVEL_RECT.centerx, SHOVEL_RECT.y + 28)))
        draw_text(surf, a.font(12), "Quitar (Q)", (SHOVEL_RECT.centerx, SHOVEL_RECT.bottom - 11), center=True)
        if SHOVEL_RECT.collidepoint(mouse):
            tip = "Pokébola: devuelve un Pokémon a su bola (sin reembolso)."
        for r, txt, col in ((PAUSE_RECT, "Pausa", (80, 100, 160)), (SPEED_RECT, f"x{self.speed}", (160, 110, 60))):
            pygame.draw.rect(surf, tuple(min(255, v + 30) for v in col) if r.collidepoint(mouse) else col, r, border_radius=6)
            pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=6)
            draw_text(surf, a.font(18), txt, r.center, center=True)
        pygame.draw.rect(surf, (45, 45, 45), INFO_RECT, border_radius=6)
        draw_text(surf, a.font(15), f"Nivel {self.level['id']}   KO: {self.kills}", INFO_RECT.center, center=True)
        if not tip:
            for e in self.enemies:
                if e.rect.collidepoint(mouse):
                    tip = self._enemy_tip(e)
                    break
        if self.hint[1] > 0:
            tip = self.hint[0]
        if tip:
            draw_text(surf, a.font(15, False), tip, (118, 82), (255, 240, 200))

    def _enemy_tip(self, e):
        t = e.tipos
        if not t:
            return f"{e.d['nombre']} (sin tipo)"
        deb = debilidades(t)
        return (f"{e.d['nombre']} ({'/'.join(NOMBRES[x] for x in t)}) - débil a: "
                f"{', '.join(NOMBRES[x] for x in deb) or 'nada'}")

    def _progress_target(self):
        total = len(self.waves)
        frac = 0.0
        if self.wave_i < total:
            frac = 1 - max(0.0, self.wave_timer) / self.wave_span
        return min(1.0, (self.wave_i + frac) / total)

    def _draw_progress(self, surf):
        """Barra estilo PvZ: se llena de derecha a izquierda; las banderas son logos del Team Rocket."""
        x, y, w, h = GRID_X, 578, COLS * CELL_W, 14
        total = len(self.waves)
        pygame.draw.rect(surf, (30, 30, 30), (x, y, w, h), border_radius=6)
        fill = int(w * self.prog)
        if fill > 0:
            pygame.draw.rect(surf, (90, 200, 110), (x + w - fill, y, fill, h), border_radius=6)
        pygame.draw.rect(surf, (255, 255, 255), (x, y, w, h), 1, border_radius=6)
        logo = self.assets.frames("items/logo_rocket", (24, 24), placeholder=("logo",))[0]
        for i, wv in enumerate(self.waves):
            if not wv["bandera"]:
                continue
            fx = x + w - int(w * (i + 1) / total)
            reached = self.wave_i > i
            img = logo if reached else _dim(logo)
            surf.blit(img, img.get_rect(center=(max(x + 8, fx), y + h // 2 - (6 if reached else 0))))
        head = self.assets.frames("rocket/grunt", (26, 26), placeholder=("rocket", "grunt"))[0]
        surf.blit(head, head.get_rect(center=(x + w - fill, y + h // 2)))
        draw_text(surf, self.assets.font(14), self.level["nombre"], (x - 8, y - 1), (255, 255, 255), topright=True)

    def _draw_banner(self, surf):
        if self.banner and self.state == "playing":
            text, t, col = self.banner
            img = self.assets.font(38).render(text, True, col)
            img.set_alpha(int(255 * min(1.0, t / 0.6)))
            sh = self.assets.font(38).render(text, True, (0, 0, 0))
            sh.set_alpha(img.get_alpha())
            r = img.get_rect(center=(WIDTH // 2, 330))
            surf.blit(sh, r.move(3, 3))
            surf.blit(img, r)

    def _draw_overlay(self, surf):
        a = self.assets
        dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 170))
        surf.blit(dark, (0, 0))
        if self.state == "paused":
            draw_text(surf, a.font(54), "PAUSA", (WIDTH // 2, 190), center=True)
        elif self.state == "lost":
            draw_text(surf, a.font(30), "¡LOS DEL TEAM ROCKET TE ROBARON EL POKEMON!", (WIDTH // 2, 250), (255, 60, 60), center=True)
            draw_text(surf, a.font(20), f"Enemigos derrotados: {self.kills}", (WIDTH // 2, 310), center=True)
        elif self.state == "won":
            draw_text(surf, a.font(54), "¡VICTORIA!", (WIDTH // 2, 200), (255, 215, 40), center=True)
            draw_text(surf, a.font(22), f"{self.level['nombre']} completado  -  KO: {self.kills}", (WIDTH // 2, 265), center=True)
            if self.new_unlock:
                draw_text(surf, a.font(20), "Nuevos Pokémon: " + ", ".join(self.new_unlock), (WIDTH // 2, 320), (140, 255, 160), center=True)
            elif self.level_index == len(LEVELS) - 1:
                draw_text(surf, a.font(22), "¡Derrotaste a Giovanni y al Team Rocket!", (WIDTH // 2, 320), (140, 255, 160), center=True)
        for b in self.overlay_buttons:
            b.draw(surf, self.app)


def _dim(img):
    d = img.copy()
    d.fill((175, 175, 175, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return d


def _darker(c, n=50):
    return tuple(max(0, v - n) for v in c)