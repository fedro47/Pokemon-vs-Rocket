"""Sonidos y música.
- Los efectos se sintetizan por código (no hace falta ningún archivo).
- Si ponés assets/sounds/<nombre>.wav|ogg|mp3 con el mismo nombre, reemplaza al sintético.
- Música: assets/music/menu.ogg y assets/music/game.ogg (opcional)."""
import array
import math
import random
from pathlib import Path
import pygame

RATE = 22050


def tone(f0, f1, dur, vol=0.5, kind="sine", decay=2.0):
    n = max(1, int(RATE * dur))
    buf = array.array("h")
    phase = 0.0
    att = int(RATE * 0.004)
    for i in range(n):
        t = i / n
        phase += (f0 + (f1 - f0) * t) / RATE
        if kind == "sine":
            v = math.sin(2 * math.pi * phase)
        elif kind == "square":
            v = 1.0 if (phase % 1) < 0.5 else -1.0
        else:
            v = random.uniform(-1, 1)
        env = (1 - t) ** decay
        if i < att:
            env *= i / att
        buf.append(int(v * env * vol * 32767))
    return buf


def seq(*bufs):
    out = array.array("h")
    for b in bufs:
        out.extend(b)
    return out


def _synth():
    T = tone
    return {
        "click": T(900, 700, .05, .3, "square"),
        "error": T(160, 120, .12, .3, "square"),
        "plant": seq(T(260, 420, .08, .4), T(420, 520, .06, .3)),
        "shoot": T(520, 260, .1, .25),
        "bubble": seq(T(300, 700, .05, .3), T(700, 900, .04, .2)),
        "fire": T(200, 80, .18, .25, "noise"),
        "zap": T(1200, 200, .15, .25, "square"),
        "hit": T(300, 100, .06, .3, "noise"),
        "sun": seq(T(700, 900, .07, .35), T(1000, 1400, .1, .35)),
        "defeat": T(500, 100, .2, .3, "square"),
        "explosion": T(120, 30, .6, .7, "noise"),
        "shovel": T(400, 150, .12, .4),
        "mower": T(90, 60, .4, .4, "square"),
        "steal": T(800, 300, .2, .3, "square"),
        "wave": seq(T(110, 110, .3, .5, "square"), T(90, 90, .5, .5, "square")),
        "win": seq(T(523, 523, .12), T(659, 659, .12), T(784, 784, .12), T(1047, 1047, .4)),
        "lose": seq(T(392, 392, .2), T(330, 330, .2), T(262, 262, .2), T(196, 196, .6)),
    }


class Audio:
    def __init__(self, config, root):
        self.cfg = config
        self.root = Path(root)
        self.enabled = False
        self.sounds = {}
        self._last = {}
        self._music = None
        try:
            pygame.mixer.init(RATE, -16, 1, 512)
            self.enabled = True
        except pygame.error as e:
            print("Audio desactivado:", e)
            return
        for name, buf in _synth().items():
            snd = None
            for ext in (".wav", ".ogg", ".mp3"):
                p = self.root / "sounds" / f"{name}{ext}"
                if p.is_file():
                    try:
                        snd = pygame.mixer.Sound(str(p))
                    except pygame.error:
                        pass
                    break
            self.sounds[name] = snd or pygame.mixer.Sound(buffer=buf)

    def play(self, name, vol=1.0):
        if not self.enabled or name not in self.sounds:
            return
        now = pygame.time.get_ticks()
        if now - self._last.get(name, 0) < 40:   # evita saturar el mismo sonido
            return
        self._last[name] = now
        s = self.sounds[name]
        s.set_volume(max(0.0, min(1.0, self.cfg["sfx"] * vol)))
        s.play()

    def play_music(self, name):
        if not self.enabled or self._music == name:
            return
        self._music = name
        for ext in (".ogg", ".mp3", ".wav"):
            p = self.root / "music" / f"{name}{ext}"
            if p.is_file():
                try:
                    pygame.mixer.music.load(str(p))
                    pygame.mixer.music.set_volume(self.cfg["music"])
                    pygame.mixer.music.play(-1)
                    return
                except pygame.error:
                    pass
        pygame.mixer.music.stop()

    def stop_music(self):
        if self.enabled:
            pygame.mixer.music.stop()
        self._music = None

    def apply_volumes(self):
        if self.enabled:
            pygame.mixer.music.set_volume(self.cfg["music"])
