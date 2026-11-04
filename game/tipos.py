"""Tabla de tipos (gen 2-5, 17 tipos). Multiplica el daño según el tipo del ataque y el del enemigo."""

TIPOS = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground",
         "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel"]

NOMBRES = {"normal": "Normal", "fire": "Fuego", "water": "Agua", "electric": "Eléctrico", "grass": "Planta",
           "ice": "Hielo", "fighting": "Lucha", "poison": "Veneno", "ground": "Tierra", "flying": "Volador",
           "psychic": "Psíquico", "bug": "Bicho", "rock": "Roca", "ghost": "Fantasma", "dragon": "Dragón",
           "dark": "Siniestro", "steel": "Acero"}

COLORES = {"normal": (168, 168, 120), "fire": (240, 128, 48), "water": (104, 144, 240), "electric": (248, 208, 48),
           "grass": (120, 200, 80), "ice": (152, 216, 216), "fighting": (192, 48, 40), "poison": (160, 64, 160),
           "ground": (224, 192, 104), "flying": (168, 144, 240), "psychic": (248, 88, 136), "bug": (168, 184, 32),
           "rock": (184, 160, 56), "ghost": (112, 88, 152), "dragon": (112, 56, 248), "dark": (112, 88, 72),
           "steel": (184, 184, 208)}

# Si un ataque es inmune (x0) usamos este valor en vez de 0, para que nunca sea frustrante.
INMUNE_MULT = 0.25

# CHART[ataque][defensor] = multiplicador (lo que no está, es x1)
CHART = {
    "normal":   {"rock": .5, "steel": .5, "ghost": 0},
    "fire":     {"fire": .5, "water": .5, "grass": 2, "ice": 2, "bug": 2, "rock": .5, "dragon": .5, "steel": 2},
    "water":    {"fire": 2, "water": .5, "grass": .5, "ground": 2, "rock": 2, "dragon": .5},
    "electric": {"water": 2, "electric": .5, "grass": .5, "ground": 0, "flying": 2, "dragon": .5},
    "grass":    {"fire": .5, "water": 2, "grass": .5, "poison": .5, "ground": 2, "flying": .5, "bug": .5,
                 "rock": 2, "dragon": .5, "steel": .5},
    "ice":      {"fire": .5, "water": .5, "grass": 2, "ice": .5, "ground": 2, "flying": 2, "dragon": 2, "steel": .5},
    "fighting": {"normal": 2, "ice": 2, "poison": .5, "flying": .5, "psychic": .5, "bug": .5, "rock": 2,
                 "ghost": 0, "dark": 2, "steel": 2},
    "poison":   {"grass": 2, "poison": .5, "ground": .5, "rock": .5, "ghost": .5, "steel": 0},
    "ground":   {"fire": 2, "electric": 2, "grass": .5, "poison": 2, "flying": 0, "bug": .5, "rock": 2, "steel": 2},
    "flying":   {"electric": .5, "grass": 2, "fighting": 2, "bug": 2, "rock": .5, "steel": .5},
    "psychic":  {"fighting": 2, "poison": 2, "psychic": .5, "dark": 0, "steel": .5},
    "bug":      {"fire": .5, "grass": 2, "fighting": .5, "poison": .5, "flying": .5, "psychic": 2, "ghost": .5,
                 "dark": 2, "steel": .5},
    "rock":     {"fire": 2, "ice": 2, "fighting": .5, "ground": .5, "flying": 2, "bug": 2, "steel": .5},
    "ghost":    {"normal": 0, "psychic": 2, "ghost": 2, "dark": .5, "steel": .5},
    "dragon":   {"dragon": 2, "steel": .5},
    "dark":     {"fighting": .5, "psychic": 2, "ghost": 2, "dark": .5, "steel": .5},
    "steel":    {"fire": .5, "water": .5, "electric": .5, "ice": 2, "rock": 2, "steel": .5},
}

# Estados a los que ciertos tipos son inmunes
INMUNE_A_ESTADO = {"veneno": {"poison", "steel"}, "quemar": {"fire"}}


def multiplicador(ataque, tipos_defensor):
    """Multiplicador total (x4, x2, x1, x0.5, x0.25...). Sin tipo de ataque o de defensor => x1."""
    if not ataque or not tipos_defensor:
        return 1.0
    m = 1.0
    for t in tipos_defensor:
        m *= CHART.get(ataque, {}).get(t, 1.0)
    return INMUNE_MULT if m == 0 else m


def debilidades(tipos_defensor):
    return [a for a in TIPOS if multiplicador(a, tipos_defensor) > 1]