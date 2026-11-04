"""Todo el contenido del juego es datos. Para agregar un Pokémon, un enemigo o un nivel
alcanza con sumar una entrada acá (y opcionalmente su imagen en assets/images/)."""

# ---------------------------------------------------------------- POKÉMON (plantas)
# rol: productor | tirador | muro | bomba
PLANTS = {
    "sunflora": dict(
        nombre="Sunflora", tipo="grass", costo=50, recarga=7.5, vida=90, rol="productor",
        intervalo=14.0, primer=8.0, color=(235, 200, 60), label="S",
        desc="Produce soles cada pocos segundos."),
    "bulbasaur": dict(
        nombre="Bulbasaur", tipo="grass", costo=100, recarga=5.0, vida=100, rol="tirador",
        cadencia=1.5, dano=18, proyectil="spore", sonido="shoot", efecto="veneno",
        color=(80, 190, 130), label="B",
        desc="Lanza esporas venenosas: daño + veneno."),
    "geodude": dict(
        nombre="Geodude", tipo="rock", costo=50, recarga=20.0, vida=500, rol="muro",
        color=(140, 140, 140), label="G",
        desc="Muro de roca muy resistente."),
    "squirtle": dict(
        nombre="Squirtle", tipo="water", costo=150, recarga=5.0, vida=100, rol="tirador",
        cadencia=1.6, dano=15, proyectil="burbuja", sonido="bubble", efecto="lento",
        color=(90, 160, 230), label="Q",
        desc="Burbujas que ralentizan a los enemigos."),
    "charmander": dict(
        nombre="Charmander", tipo="fire", costo=175, recarga=6.0, vida=100, rol="tirador",
        cadencia=1.8, dano=22, proyectil="ascua", sonido="fire", efecto="quemar",
        color=(240, 130, 60), label="C",
        desc="Ascuas: daño alto y quemadura."),
    "voltorb": dict(
        nombre="Voltorb", tipo="electric", costo=150, recarga=30.0, vida=60, rol="bomba",
        mecha=1.2, radio=135, dano=600, color=(220, 60, 60), label="V",
        desc="Autodestrucción en área 3x3."),
    "pikachu": dict(
        nombre="Pikachu", tipo="electric", costo=200, recarga=7.0, vida=100, rol="tirador",
        cadencia=1.7, dano=28, proyectil="rayo", sonido="zap", perfora=True,
        color=(250, 220, 50), label="P",
        desc="Rayo que atraviesa a toda la fila."),
}

PROJECTILES = {
    "spore": dict(size=(24, 24), vel=260, estela=(150, 90, 210),
                  placeholder=("orb", (170, 90, 230), (90, 200, 90))),
    "burbuja": dict(size=(24, 24), vel=280, estela=(150, 210, 255),
                    placeholder=("orb", (200, 235, 255), (80, 150, 230))),
    "ascua": dict(size=(24, 24), vel=300, estela=(255, 160, 40),
                  placeholder=("orb", (255, 230, 80), (240, 90, 30))),
    "rayo": dict(size=(36, 36), vel=420, amp=6, estela=(255, 240, 80),
                 placeholder=("bolt",)),
}

# ---------------------------------------------------------------- ENEMIGOS (zombies)
# tipos: lista de tipos (vacía = humano, sin tipo, daño neutral)
ENEMIES = {
    "grunt": dict(nombre="Recluta Rocket", vida=100, vel=14, dps=20, size=(55, 75), tipos=[],
                  placeholder=("rocket", "grunt")),
    "casco": dict(nombre="Recluta con casco", vida=280, vel=14, dps=20, size=(55, 75), tipos=[],
                  placeholder=("rocket", "casco")),
    "rattata": dict(nombre="Rattata", vida=70, vel=30, dps=18, size=(55, 45), tipos=["normal"],
                    placeholder=("creature", (150, 90, 170), "R")),
    "zubat": dict(nombre="Zubat", vida=60, vel=34, dps=15, size=(55, 45), tipos=["poison", "flying"],
                  placeholder=("creature", (110, 90, 170), "Z")),
    "koffing": dict(nombre="Koffing", vida=140, vel=12, dps=20, size=(60, 60), tipos=["poison"],
                    explota=dict(radio=95, dano=120),   # al caer suelta gas y daña a los Pokémon cercanos
                    placeholder=("creature", (150, 120, 190), "K")),
    "meowth": dict(nombre="Meowth ladrón", vida=90, vel=20, dps=18, size=(55, 60), tipos=["normal"], ladron=True,
                   placeholder=("creature", (235, 215, 160), "M")),
    "giovanni": dict(nombre="Giovanni", vida=2500, vel=8, dps=70, size=(95, 115), tipos=["ground"], jefe=True,
                     invoca="grunt", placeholder=("rocket", "giovanni")),
}


# ---------------------------------------------------------------- NIVELES
import random

# "Costo" de cada enemigo para el generador de oleadas (como los puntos de PvZ).
COSTO = {"grunt": 1, "casco": 3, "rattata": 2, "zubat": 2, "koffing": 3, "meowth": 3}


def generar_olas(cantidad, grandes, pool, base=1.0, crece=0.7, espera=28, primera=45,
                 mult_grande=2.0, jefe=None, rnd=None):
    """Genera las oleadas de un nivel con un presupuesto creciente.

    cantidad : total de oleadas.
    grandes  : 1 = solo una oleada enorme al final; 2 = una a la mitad y otra al final.
    pool     : lista de (tipo, peso, desde_que_ola_aparece).
    base/crece: presupuesto de la ola i = base + crece * i  (las enormes lo multiplican).
    espera   : segundos entre oleadas;  primera: tiempo de calma antes de la primera.
    jefe     : tipo de enemigo que se suma a la última ola.
    """
    rnd = rnd or random
    idx_grandes = {cantidad - 1}
    if grandes >= 2:
        idx_grandes.add(cantidad // 2)
    olas = []
    for i in range(cantidad):
        grande = i in idx_grandes
        presupuesto = (base + crece * i) * (mult_grande if grande else 1.0)
        disp = [(t, w) for t, w, desde in pool if i >= desde]
        enem = {}
        while True:
            ok = [(t, w) for t, w in disp if COSTO[t] <= presupuesto]
            if not ok:
                break
            t = rnd.choices([a for a, _ in ok], [b for _, b in ok])[0]
            enem[t] = enem.get(t, 0) + 1
            presupuesto -= COSTO[t]
        if not enem:
            enem["grunt"] = 1
        if jefe and i == cantidad - 1:
            enem[jefe] = 1
        olas.append(dict(espera=primera if i == 0 else espera, bandera=grande, enemigos=enem))
    return olas


ALL_ROWS = [0, 1, 2, 3, 4]

LEVELS = [
    dict(id=1, nombre="Pueblo Paleta", desc="Tutorial: 3 filas.",
         filas=[1, 2, 3], soles_iniciales=100,
         plantas=["sunflora", "bulbasaur"],
         pasto=((70, 160, 65), (85, 180, 75)), cielo=(130, 200, 240),
         olas=dict(cantidad=8, grandes=1, base=1.0, crece=0.6,
                   pool=[("grunt", 1, 0)])),
    dict(id=2, nombre="Bosque Verde", desc="Llegan los cascos.",
         filas=ALL_ROWS, soles_iniciales=100,
         plantas=["sunflora", "bulbasaur", "geodude"],
         pasto=((40, 120, 50), (55, 140, 62)), cielo=(90, 150, 110),
         olas=dict(cantidad=10, grandes=2, base=1.5, crece=0.6,
                   pool=[("grunt", 3, 0), ("casco", 1, 3)])),
    dict(id=3, nombre="Ciudad Celeste", desc="Rattatas y Zubats.",
         filas=ALL_ROWS, soles_iniciales=125,
         plantas=["sunflora", "bulbasaur", "geodude", "squirtle"],
         pasto=((110, 135, 160), (125, 150, 175)), cielo=(150, 190, 230),
         olas=dict(cantidad=11, grandes=2, base=2.0, crece=0.65,
                   pool=[("grunt", 3, 0), ("rattata", 2, 1), ("casco", 2, 3), ("zubat", 1, 4)])),
    dict(id=4, nombre="Isla Canela", desc="Ladrones y gas tóxico.",
         filas=ALL_ROWS, soles_iniciales=150,
         plantas=["sunflora", "bulbasaur", "geodude", "squirtle", "charmander", "voltorb"],
         pasto=((205, 185, 115), (220, 200, 130)), cielo=(120, 200, 230),
         olas=dict(cantidad=12, grandes=2, base=2.0, crece=0.65,
                   pool=[("grunt", 3, 0), ("rattata", 2, 1), ("casco", 2, 3), ("zubat", 2, 3), ("meowth", 1, 4), ("koffing", 1, 5)])),
    dict(id=5, nombre="Guarida Rocket", desc="¡Jefe final: Giovanni!",
         filas=ALL_ROWS, soles_iniciales=150,
         plantas=["sunflora", "bulbasaur", "geodude", "squirtle", "charmander", "voltorb", "pikachu"],
         pasto=((75, 65, 90), (90, 80, 105)), cielo=(50, 40, 70),
         olas=dict(cantidad=14, grandes=2, base=2.5, crece=0.65, espera=26, jefe="giovanni",
                   pool=[("grunt", 3, 0), ("rattata", 2, 1), ("casco", 2, 3), ("zubat", 2, 3), ("meowth", 1, 4), ("koffing", 1, 5)])),
]