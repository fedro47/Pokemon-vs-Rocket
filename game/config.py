"""Configuración y progreso guardados en savegame.json."""
import json
from .settings import SAVE_FILE

DEFAULTS = {
    "music": 0.5,
    "sfx": 0.7,
    "fullscreen": False,
    "shake": True,
    "show_fps": False,
    "enemy_speed": 1.25,   # multiplicador de velocidad de los rivales (0.25x - 2.0x)
    "last_deck": [],       # último equipo elegido
    "wave_pace": 1.0,      # multiplicador del tiempo entre oleadas (menor = más seguidas)
    "unlocked": 1,      # cantidad de niveles desbloqueados
}


class Config:
    def __init__(self):
        self.data = dict(DEFAULTS)

    @classmethod
    def load(cls):
        cfg = cls()
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for k in DEFAULTS:
                if k in saved:
                    cfg.data[k] = saved[k]
        except (OSError, ValueError):
            pass
        return cfg

    def save(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError as e:
            print("No se pudo guardar:", e)

    def reset_progress(self):
        self.data["unlocked"] = 1
        self.save()

    def __getitem__(self, k):
        return self.data[k]

    def __setitem__(self, k, v):
        self.data[k] = v