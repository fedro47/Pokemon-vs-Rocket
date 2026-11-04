# Pokémon vs Team Rocket

Tower defense estilo *Plants vs Zombies* hecho con Pygame. Defendé tu equipo Pokémon de las oleadas del Team Rocket.

## Cómo correrlo
```bash
pip install -r requirements.txt
python main.py
```
Funciona **sin ninguna imagen ni sonido**: todo tiene un sprite/sonido generado por código. Cualquier archivo que agregues lo reemplaza automáticamente.

## Controles
| Acción | Control |
|---|---|
| Recoger sol | Clic en el sol |
| Elegir Pokémon | Clic en la carta o teclas `1`-`7` |
| Plantar | Clic en una casilla |
| Pokébola (quitar Pokémon) | `Q` o clic en el botón |
| Cancelar selección | Clic derecho |
| Pausa | `Esc` / `P` |
| Velocidad x2 | `F` o botón |
| Pantalla completa | `F11` |

## Estructura
```
main.py                  punto de entrada
game/
  settings.py            constantes y rutas (relativas al proyecto, no al cwd)
  data.py                Pokémon, enemigos, proyectiles y NIVELES (acá se agrega contenido)
  entities.py            Pokemon, Enemy, Projectile, Mower, Sun, partículas
  assets.py              carga de imágenes/GIF con caché + placeholders
  placeholders.py        sprites dibujados por código
  audio.py               efectos sintetizados + música opcional
  config.py              opciones y progreso (savegame.json)
  ui.py                  botones y sliders
  scenes/                menu, level_select, settings_menu, play
assets/
  images/{pokemon,rocket,projectiles,items,backgrounds,tiles}
  sounds/  music/
tools/
  spritesheet_to_gif.py  convierte una fila de sprite sheet en GIF animado
  smoke_test.py          simula partidas sin ventana
```

## Dónde poner tus sprites
Nombre = clave del juego. Extensiones: `.gif .png .webp .jpg .jpeg`. Se recortan los bordes transparentes y se escalan manteniendo proporción.

| Qué | Ruta |
|---|---|
| Pokémon (mirando a la **derecha** se ve bien; se voltean solos) | `assets/images/pokemon/<id>.gif` (`bulbasaur`, `sunflora`, `geodude`, `squirtle`, `charmander`, `voltorb`, `pikachu`) |
| Enemigos | `assets/images/rocket/<id>.gif` (`grunt`, `casco`, `rattata`, `meowth`, `giovanni`) |
| Sol | `assets/images/items/sol.gif` |
| Cortacésped | `assets/images/items/carrito.gif` |
| Pokébola | `assets/images/items/pokebola.png` |
| Proyectiles | `assets/images/projectiles/{spore,burbuja,ascua,rayo}.png` |
| Fondo (general o por nivel) | `backgrounds/fondo.png`, `backgrounds/level_3.png`, `backgrounds/menu.png` |
| Casillas | `tiles/pasto1.jpg`, `tiles/pasto2.jpg` (o por nivel: `level_2_1`, `level_2_2`) |

Tip: Pokémon Showdown tiene GIFs animados de frente (`ani`) y de espaldas (`ani-back`); para el equipo conviene el de espaldas o el de frente (se voltea).

## Sonidos
Los efectos se generan solos. Para reemplazar uno, poné `assets/sounds/<nombre>.wav|ogg|mp3` con alguno de estos nombres:
`click error plant shoot bubble fire zap hit sun defeat explosion shovel mower steal wave win lose`.
Música: `assets/music/menu.ogg` y `assets/music/game.ogg`.

## Agregar contenido (todo en `game/data.py`)
- **Pokémon nuevo**: sumá una entrada a `PLANTS` (rol `productor|tirador|muro|bomba`) y agregalo a la lista `plantas` de un nivel.
- **Enemigo nuevo**: entrada en `ENEMIES`; usalo en las `olas` de un nivel.
- **Nivel nuevo**: dict en `LEVELS` (filas activas, soles iniciales, plantas, colores y los parámetros de `generar_olas`: cantidad, grandes, base, crece, pool, jefe).
- **Ritmo**: `GAME_SPEED` en `settings.py`, `SUN_VALUE`, velocidad/dps de cada enemigo en `ENEMIES`, `espera`/`primera` de cada nivel. Se desbloquea solo al pasar el anterior.

## Mecánicas
Recarga por carta, Pokébola, oleadas con barra de progreso y ola enorme, estados (veneno, lento, quemadura), cortacéspedes, Voltorb explosivo, Pikachu perforante, Meowth que roba soles, jefe Giovanni que invoca refuerzos, 5 niveles con progreso guardado, pausa y velocidad x2.

## Ideas para seguir
Modo supervivencia infinito, selección de equipo antes del nivel, evoluciones (Bulbasaur→Ivysaur al gastar soles), monedas/tienda, niveles nocturnos o de agua, más jefes.