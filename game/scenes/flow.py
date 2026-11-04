"""Flujo para empezar un nivel: si hay más Pokémon disponibles que casilleros de mazo, se elige el equipo."""
from ..data import LEVELS, PLANTS
from ..settings import MAZO_SLOTS, DEBUG_DESBLOQUEAR_TODO


def plantas_disponibles(idx):
    return list(PLANTS) if DEBUG_DESBLOQUEAR_TODO else list(LEVELS[idx]["plantas"])


def start_level(app, idx):
    avail = plantas_disponibles(idx)
    if len(avail) > MAZO_SLOTS:
        from .deck_select import DeckSelectScene
        app.go(DeckSelectScene(app, idx))
    else:
        from .play import PlayScene
        app.go(PlayScene(app, idx, deck=avail))