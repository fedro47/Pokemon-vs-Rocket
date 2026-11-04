"""Entidades del juego. Todas reciben `ctx` (la PlayScene) para interactuar con el mundo."""
import math
import random
import pygame
from .settings import *
from .data import PLANTS, ENEMIES, PROJECTILES
from .tipos import multiplicador, INMUNE_A_ESTADO

VENENO_DPS, QUEMAR_DPS = 8, 12
EFECTO_DURACION = {"veneno": 5.0, "lento": 4.0, "quemar": 3.0}


def _apply(surf, color, flags):
    s = surf.copy()
    s.fill(color, special_flags=flags)
    return s


class Anim(pygame.sprite.Sprite):
    fps = 10

    def __init__(self, frames):
        super().__init__()
        self.frames, self.fi, self._t = frames, 0, 0.0
        self.image = frames[0]
        self.rect = self.image.get_rect()

    def animate(self, dt):
        if len(self.frames) > 1:
            self._t += dt
            step = 1.0 / self.fps
            while self._t >= step:
                self._t -= step
                self.fi = (self.fi + 1) % len(self.frames)
        return self.frames[self.fi]


# ------------------------------------------------------------------ Pokémon
class Pokemon(Anim):
    def __init__(self, ctx, key, fila, col):
        d = PLANTS[key]
        frames = ctx.assets.frames(f"pokemon/{key}", d.get("size", (60, 70)), flip=True,
                                   placeholder=("creature", d["color"], d["label"]))
        super().__init__(frames)
        self.ctx, self.key, self.d, self.fila, self.col = ctx, key, d, fila, col
        self.vida = self.vida_max = d["vida"]
        self.x, self.y = col_center_x(col), row_center_y(fila)
        self.rect.center = (self.x, self.y)
        self.timer = 0.0
        self.next_sun = d.get("primer", 0)
        self.cd = d.get("cadencia", 0) * 0.5
        self.mecha = d.get("mecha", 0)
        self.muerto = False

    def hurt(self, dmg):
        self.vida -= dmg
        if self.vida <= 0 and not self.muerto:
            self.ctx.remove_plant(self)

    def update(self, dt):
        base = self.animate(dt)
        ctx, d = self.ctx, self.d
        rol = d["rol"]
        self.image = base
        if rol == "productor":
            self.timer += dt
            if self.timer >= self.next_sun:
                self.timer, self.next_sun = 0.0, d["intervalo"]
                ctx.spawn_plant_sun(self)
        elif rol == "tirador":
            self.cd -= dt
            if self.cd <= 0 and ctx.enemy_ahead(self.fila, self.x):
                self.cd = d["cadencia"]
                ctx.projectiles.add(Projectile(ctx, self.x + 22, self.y - 8, self.fila, d))
                ctx.audio.play(d["sonido"], 0.6)
        elif rol == "bomba":
            self.mecha -= dt
            k = 1 - max(0, self.mecha) / d["mecha"]
            img = pygame.transform.smoothscale(base, (int(base.get_width() * (1 + .4 * k)),
                                                      int(base.get_height() * (1 + .4 * k))))
            if int(self.mecha * 10) % 2 == 0:
                img = _apply(img, (110, 110, 110, 0), pygame.BLEND_RGB_ADD)
            self.image = img
            self.rect = img.get_rect(center=(self.x, self.y))
            if self.mecha <= 0:
                ctx.explode(self.x, self.y, d["radio"], d["dano"], d.get("tipo"))
                ctx.remove_plant(self)


# ------------------------------------------------------------------ Enemigos
class Enemy(Anim):
    fps = 8

    def __init__(self, ctx, key, fila, x=None):
        d = ENEMIES[key]
        frames = ctx.assets.frames(f"rocket/{key}", d["size"], placeholder=d["placeholder"])
        super().__init__(frames)
        self.ctx, self.key, self.d, self.fila = ctx, key, d, fila
        self.vida = self.vida_max = d["vida"]
        self.vel = d["vel"] * ctx.cfg["enemy_speed"]   # perilla global de velocidad (Configuración)
        self.dps = d["dps"]
        self.jefe = d.get("jefe", False)
        self.tipos = d.get("tipos", [])
        self.fx_cd = 0.0
        self.x = x if x is not None else WIDTH + d["size"][0] / 2 + 10
        self.y = row_center_y(fila) + random.randint(-4, 4) - (12 if self.jefe else 0)
        self.rect.center = (self.x, self.y)
        self.estados = {}
        self.flash = 0.0
        self.muerto = False
        self.comiendo = False
        self.skill_t = 8.0 if self.jefe else 3.0
        self.walk_t = random.random() * 6

    @property
    def hitbox(self):
        return self.rect.inflate(-int(self.rect.w * .4), 0)

    def _inmune_a(self, efecto):
        return any(t in INMUNE_A_ESTADO.get(efecto, ()) for t in self.tipos)

    def hurt(self, dmg, efecto=None, tipo=None):
        if self.muerto:
            return
        m = multiplicador(tipo, self.tipos)
        dmg *= m
        if tipo and m != 1 and self.fx_cd <= 0:
            self.fx_cd = 1.2
            if m >= 2:
                self.ctx.add_text(self.x, self.rect.y - 22, "¡Súper eficaz!", (255, 230, 80))
            elif m >= 0.5:
                self.ctx.add_text(self.x, self.rect.y - 22, "Poco eficaz...", (190, 190, 190))
            else:
                self.ctx.add_text(self.x, self.rect.y - 22, "Casi inmune", (150, 150, 170))
        self.vida -= dmg
        self.flash = 0.08
        if efecto and self._inmune_a(efecto):
            efecto = None
        if efecto:
            self.estados[efecto] = EFECTO_DURACION[efecto]
            if efecto == "quemar":
                self.estados.pop("lento", None)
            elif efecto == "lento":
                self.estados.pop("quemar", None)
        if self.vida <= 0:
            self.ctx.kill_enemy(self)

    def update(self, dt):
        base = self.animate(dt)
        ctx = self.ctx
        self.flash = max(0.0, self.flash - dt)
        self.fx_cd = max(0.0, self.fx_cd - dt)
        for k in list(self.estados):
            self.estados[k] -= dt
            if self.estados[k] <= 0:
                del self.estados[k]
        dot = (VENENO_DPS if "veneno" in self.estados else 0) + (QUEMAR_DPS if "quemar" in self.estados else 0)
        if dot:
            self.vida -= dot * dt
            if random.random() < dt * 4:
                col = (150, 80, 210) if "veneno" in self.estados else (255, 120, 30)
                ctx.particles.append(Particle(self.x + random.randint(-12, 12), self.y - 20, 0, -30, .5, col, 3))
            if self.vida <= 0:
                ctx.kill_enemy(self)
                return
        mult = 0.5 if "lento" in self.estados else 1.0

        target = ctx.plant_in_front(self)
        self.comiendo = target is not None
        if target:
            target.hurt(self.dps * mult * dt)
        else:
            self.x -= self.vel * mult * dt

        self.skill_t -= dt
        if self.skill_t <= 0:
            if self.jefe:
                self.skill_t = 9.0
                ctx.spawn_enemy(self.d["invoca"], self.fila, self.x + 40)
                ctx.add_text(self.x, self.y - 70, "¡Refuerzos!", (255, 120, 120))
                ctx.audio.play("wave", .6)
            elif self.d.get("ladron"):
                self.skill_t = 5.0
                s = ctx.nearest_sun(self.x)
                if s:
                    s.kill()
                    ctx.add_text(self.x, self.y - 40, "¡Robó un sol!", (255, 220, 80))
                    ctx.audio.play("steal", .6)

        img = base
        if "veneno" in self.estados:
            img = _apply(img, (190, 110, 230), pygame.BLEND_RGB_MULT)
        if "lento" in self.estados:
            img = _apply(img, (140, 190, 255), pygame.BLEND_RGB_MULT)
        if "quemar" in self.estados:
            img = _apply(img, (255, 150, 100), pygame.BLEND_RGB_MULT)
        if self.flash > 0:
            img = _apply(img, (90, 90, 90, 0), pygame.BLEND_RGB_ADD)
        bob = 0.0
        if len(self.frames) == 1:   # sprite estático: lo hacemos "caminar" con rebote y balanceo
            self.walk_t += dt * (3 if self.comiendo else 6) * mult
            img = pygame.transform.rotozoom(img, math.sin(self.walk_t) * 4, 1.0)
            bob = 0.0 if self.comiendo else abs(math.sin(self.walk_t)) * 4
        self.image = img
        self.rect = img.get_rect(center=(round(self.x), round(self.y - bob)))
        if self.rect.right < 0:
            ctx.lose()


# ------------------------------------------------------------------ Proyectil
class Projectile(pygame.sprite.Sprite):
    def __init__(self, ctx, x, y, fila, plant_data):
        super().__init__()
        name = plant_data["proyectil"]
        p = PROJECTILES[name]
        self.frames = ctx.assets.frames(f"projectiles/{name}", p["size"], placeholder=p["placeholder"])
        self.image = self.frames[0]
        self.ctx, self.fila = ctx, fila
        self.x, self.y0 = float(x), float(y)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel, self.estela = p["vel"], p["estela"]
        self.amp = p.get("amp", 2)
        self.dano = plant_data["dano"]
        self.efecto = plant_data.get("efecto")
        self.tipo = plant_data.get("tipo")
        self.perfora = plant_data.get("perfora", False)
        self.hits = set()
        self.t = 0.0
        self.trail = 0.0

    def update(self, dt):
        ctx = self.ctx
        self.t += dt
        self.x += self.vel * dt
        y = self.y0 + math.sin(self.t * 14) * self.amp
        self.image = self.frames[int(self.t * 10) % len(self.frames)]
        self.rect.center = (round(self.x), round(y))
        self.trail -= dt
        if self.trail <= 0:
            self.trail = 0.04
            ctx.particles.append(Particle(self.x - 10, y + random.uniform(-3, 3), random.uniform(-15, 5),
                                          random.uniform(-10, 10), .35, self.estela, 4))
        for e in list(ctx.enemies):
            if e.fila == self.fila and e not in self.hits and self.rect.colliderect(e.hitbox):
                self.hits.add(e)
                e.hurt(self.dano, self.efecto, self.tipo)
                ctx.audio.play("hit", .5)
                for _ in range(5):
                    ctx.particles.append(Particle(self.x, y, random.uniform(-60, 60), random.uniform(-60, 40),
                                                  .3, self.estela, 4))
                if not self.perfora:
                    self.kill()
                    return
        if self.x > WIDTH + 20:
            self.kill()


# ------------------------------------------------------------------ Cortacésped
class Mower(Anim):
    def __init__(self, ctx, fila):
        frames = ctx.assets.frames("items/carrito", (65, 55), flip=True, placeholder=("mower",))
        super().__init__(frames)
        self.ctx, self.fila = ctx, fila
        self.x = GRID_X - 45
        self.rect.center = (self.x, row_center_y(fila))
        self.active = False
        self.hit = set()

    def update(self, dt):
        self.image = self.animate(dt)
        ctx = self.ctx
        if not self.active:
            for e in ctx.enemies:
                if e.fila == self.fila and e.rect.left <= self.rect.right + 5:
                    self.active = True
                    ctx.audio.play("mower")
                    break
            return
        self.x += 480 * dt
        self.rect.centerx = round(self.x)
        for e in list(ctx.enemies):
            if e.fila == self.fila and self.rect.colliderect(e.hitbox):
                if e.jefe:
                    if e not in self.hit:
                        self.hit.add(e)
                        e.hurt(600)
                else:
                    e.hurt(99999)
        if self.rect.left > WIDTH:
            self.kill()


# ------------------------------------------------------------------ Sol
class Sun(Anim):
    def __init__(self, ctx, x, y, dest_y, valor=SUN_VALUE, hop=False):
        frames = ctx.assets.frames("items/sol", (46, 46), placeholder=("sun",))
        super().__init__(frames)
        self.ctx, self.x, self.y, self.dest, self.valor, self.hop = ctx, float(x), float(y), dest_y, valor, hop
        self.vx = random.uniform(-45, 45) if hop else 0
        self.vy = -170.0 if hop else 0
        self.state = "fall"      # fall -> wait -> fly
        self.life = 10.0
        self.t = random.random() * 6
        self.visible = True
        self.rect.center = (x, y)

    @property
    def hitrect(self):
        return self.rect.inflate(26, 26)

    def collect(self):
        if self.state == "fly":
            return False
        self.state = "fly"
        self.ctx.add_sun(self.valor)
        self.ctx.audio.play("sun")
        return True

    def update(self, dt):
        self.t += dt
        base = self.animate(dt)
        if self.state == "fly":
            tx, ty = SUN_ICON_POS
            k = min(1.0, dt * 9)
            self.x += (tx - self.x) * k
            self.y += (ty - self.y) * k
            if math.hypot(tx - self.x, ty - self.y) < 14:
                self.kill()
                return
        else:
            if self.state == "fall":
                if self.hop:
                    self.vy += 520 * dt
                    self.x += self.vx * dt
                    self.y += self.vy * dt
                    if self.y >= self.dest and self.vy > 0:
                        self.y, self.state = self.dest, "wait"
                elif self.y < self.dest:
                    self.y += 70 * dt
                else:
                    self.state = "wait"
            if self.state == "wait":
                self.life -= dt
                if self.life <= 0:
                    self.kill()
                    return
        self.visible = not (self.state == "wait" and self.life < 2.5 and int(self.t * 10) % 2)
        if len(self.frames) == 1:
            self.image = pygame.transform.rotozoom(base, self.t * 40, 1 + 0.06 * math.sin(self.t * 5))
        else:
            self.image = base
        self.rect = self.image.get_rect(center=(self.x, self.y))


# ------------------------------------------------------------------ Efectos
class Particle:
    def __init__(self, x, y, vx, vy, life, color, size, grav=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max = life
        self.color, self.size, self.grav = color, size, grav

    def update(self, dt):
        self.life -= dt
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf):
        r = max(1, int(self.size * self.life / self.max))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


class FloatText:
    def __init__(self, font, x, y, text, color):
        self.img = font.render(text, True, color)
        self.sh = font.render(text, True, (0, 0, 0))
        self.x, self.y, self.life = x, y, 1.2

    def update(self, dt):
        self.life -= dt
        self.y -= 30 * dt

    def draw(self, surf):
        a = int(255 * min(1.0, self.life / 0.5))
        for im, off in ((self.sh, 1), (self.img, 0)):
            im.set_alpha(a)
            r = im.get_rect(center=(self.x + off, self.y + off))
            surf.blit(im, r)