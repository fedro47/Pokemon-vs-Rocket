"""Constantes globales."""
from pathlib import Path

# Las rutas se calculan desde ESTE archivo, no desde la carpeta donde ejecutes Python.
# (Ese era el motivo por el que los sprites no cargaban: os.path.exists("x.gif") es
#  relativo al directorio de trabajo actual, no al del script.)
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
SAVE_FILE = BASE_DIR / "savegame.json"

TITLE = "Pokémon vs Team Rocket"
WIDTH, HEIGHT, FPS = 900, 600, 60

ROWS, COLS = 5, 9
CELL_W, CELL_H = 80, 90
GRID_X, GRID_Y = 140, 120
TOPBAR_H = 100

SUN_VALUE = 25
SUN_ICON_POS = (60, 42)   # hacia dónde vuelan los soles al recogerlos


def row_center_y(row):
    return GRID_Y + row * CELL_H + CELL_H // 2


def col_center_x(col):
    return GRID_X + col * CELL_W + CELL_W // 2


# --- Ritmo del juego (perillas para balancear) ---
GAME_SPEED = 1.0
# Para probar todo sin jugar los niveles: desbloquea todos los niveles y todos los Pokémon.
DEBUG_DESBLOQUEAR_TODO = False
# Casilleros de equipo. Si un nivel tiene más Pokémon disponibles que esto, se abre la selección de mazo.
MAZO_SLOTS = 5
# La velocidad de los rivales y el tiempo entre oleadas se cambian en Configuración (se guardan)
# o su valor por defecto en config.py (enemy_speed / wave_pace).      # multiplicador global del tiempo: 0.8 = todo un 20% más lento