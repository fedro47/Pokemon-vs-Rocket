import pygame
import sys
import random
import os

# --- CONFIGURACIÓN GLOBAL ---
ANCHO_VENTANA = 900
ALTO_VENTANA = 600
FPS = 60

# Grilla de 5x9
FILAS = 5
COLUMNAS = 9
ANCHO_CASILLA = 80
ALTO_CASILLA = 90
INICIO_X = 140
INICIO_Y = 120

# Colores de respaldo (por si faltan texturas)
COLOR_PASTO_1 = (34, 139, 34)
COLOR_PASTO_2 = (50, 205, 50)

def cargar_o_crear_sprite(nombre_archivo, ancho_max, alto_max, color_respaldo, voltear_x=False):
    if os.path.exists(nombre_archivo):
        if nombre_archivo.lower().endswith('.gif'):
            try:
                from PIL import Image as PILImage
                pil_img = PILImage.open(nombre_archivo)
                frames_pygame = []
                try:
                    while True:
                        cuadro_rgba = pil_img.convert("RGBA")
                        data = cuadro_rgba.tobytes()
                        size = cuadro_rgba.size
                        surface_cuadro = pygame.image.fromstring(data, size, "RGBA")
                        surface_escalada = pygame.transform.smoothscale(surface_cuadro, (ancho_max, alto_max))
                        if voltear_x:
                            surface_escalada = pygame.transform.flip(surface_escalada, True, False)
                        frames_pygame.append(surface_escalada)
                        pil_img.seek(pil_img.tell() + 1)
                except EOFError:
                    pass
                if frames_pygame:
                    return frames_pygame
            except Exception as e:
                print(f"Error cargando GIF {nombre_archivo}: {e}")
        try:
            imagen = pygame.image.load(nombre_archivo).convert_alpha()
            surface_escalada = pygame.transform.smoothscale(imagen, (ancho_max, alto_max))
            if voltear_x:
                surface_escalada = pygame.transform.flip(surface_escalada, True, False)
            return [surface_escalada]
        except:
            pass

    superficie = pygame.Surface((ancho_max, alto_max), pygame.SRCALPHA)
    pygame.draw.rect(superficie, color_respaldo, (2, 2, ancho_max - 4, alto_max - 4))
    pygame.draw.rect(superficie, (255,255,255), (2, 2, ancho_max - 4, alto_max - 4), 1)
    return [superficie]

# --- ENTIDADES ---

class Pokemon(pygame.sprite.Sprite):
    def __init__(self, x, y, fila, tipo_pokemon="bulbasaur"):
        super().__init__()
        self.fila = fila
        self.tipo_pokemon = tipo_pokemon
        
        if tipo_pokemon == "bulbasaur":
            self.vida_max = 100
            self.vida = 100
            self.cooldown_ataque = 1500
            self.archivo = "bulbasaur.gif"
            self.archivo_alt = "bulbasaur.png"
            color_res = (0, 200, 100)
        elif tipo_pokemon == "geodude":
            self.vida_max = 300
            self.vida = 300
            self.cooldown_ataque = 999999
            self.archivo = "geodude.gif"
            self.archivo_alt = "geodude.png"
            color_res = (128, 128, 128)
            
        self.frames = cargar_o_crear_sprite(self.archivo, 60, 70, color_res, voltear_x=True)
        if len(self.frames) == 1 and not os.path.exists(self.archivo):
            self.frames = cargar_o_crear_sprite(self.archivo_alt, 60, 70, color_res, voltear_x=True)

        self.frame_actual = 0
        self.image = self.frames[self.frame_actual]
        self.rect = self.image.get_rect(center=(x, y))
        self.ultimo_frame_time = pygame.time.get_ticks()
        self.ultimo_ataque = pygame.time.get_ticks()

    def update(self, grupo_zombies, grupo_proyectiles):
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_frame_time > 100:
            self.frame_actual = (self.frame_actual + 1) % len(self.frames)
            self.image = self.frames[self.frame_actual]
            self.ultimo_frame_time = ahora

        if self.tipo_pokemon == "bulbasaur":
            zombies_en_carril = [z for z in grupo_zombies if z.fila == self.fila and z.rect.x > self.rect.x]
            if zombies_en_carril:
                if ahora - self.ultimo_ataque >= self.cooldown_ataque:
                    proyectil = Proyectil(self.rect.right, self.rect.centery, self.fila)
                    grupo_proyectiles.add(proyectil)
                    self.ultimo_ataque = ahora

class Zombie(pygame.sprite.Sprite):
    def __init__(self, fila):
        super().__init__()
        self.fila = fila
        self.vida_max = 100
        self.vida = 100
        self.velocidad = 0.8
        self.esta_comiendo = False
        
        self.frames = cargar_o_crear_sprite("zombie_walk.gif", 55, 75, (255, 0, 0), voltear_x=False)
        if len(self.frames) == 1 and not os.path.exists("zombie_walk.gif"):
            self.frames = cargar_o_crear_sprite("zombie_walk.png", 55, 75, (255, 0, 0), voltear_x=False)
            
        self.frame_actual = 0
        self.image = self.frames[self.frame_actual]
        y_pos = INICIO_Y + (fila * ALTO_CASILLA) + (ALTO_CASILLA // 2)
        self.rect = self.image.get_rect(center=(ANCHO_VENTANA + 30, y_pos))
        self.ultimo_frame_time = pygame.time.get_ticks()

    def update(self, grupo_pokemon):
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_frame_time > 100:
            self.frame_actual = (self.frame_actual + 1) % len(self.frames)
            self.image = self.frames[self.frame_actual]
            self.ultimo_frame_time = ahora

        self.esta_comiendo = False
        pokemon_chocado = pygame.sprite.spritecollideany(self, grupo_pokemon)
        
        if pokemon_chocado and pokemon_chocado.fila == self.fila:
            self.esta_comiendo = True
            pokemon_chocado.vida -= 0.5
            if pokemon_chocado.vida <= 0:
                pokemon_chocado.kill()
        
        if not self.esta_comiendo:
            self.rect.x -= self.velocidad
            
        if self.vida <= 0:
            self.kill()

class Proyectil(pygame.sprite.Sprite):
    def __init__(self, x, y, fila):
        super().__init__()
        if os.path.exists("proyectil.png"):
            self.image = pygame.image.load("proyectil.png").convert_alpha()
            self.image = pygame.transform.smoothscale(self.image, (20, 20))
        else:
            self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (144, 238, 144), (8, 8), 8)
            pygame.draw.circle(self.image, (60, 179, 113), (8, 8), 8, 2)
            
        self.rect = self.image.get_rect(center=(x, y))
        self.fila = fila
        self.velocidad = 5

    def update(self):
        self.rect.x += self.velocidad
        if self.rect.x > ANCHO_VENTANA:
            self.kill()

class Carrito(pygame.sprite.Sprite):
    def __init__(self, fila):
        super().__init__()
        self.fila = fila
        # Intentará cargar koraidon o varoom. Si no, usa el placeholder gris
        self.frames = cargar_o_crear_sprite("carrito.gif", 65, 55, (192, 192, 192), voltear_x=True)
        self.image = self.frames[0]
        y_pos = INICIO_Y + (fila * ALTO_CASILLA) + (ALTO_CASILLA // 2)
        self.rect = self.image.get_rect(center=(INICIO_X - 45, y_pos))
        self.activo = False
        self.velocidad = 8

    def update(self, grupo_zombies):
        if not self.activo:
            zombies_en_carril = [z for z in grupo_zombies if z.fila == self.fila]
            for zombie in zombies_en_carril:
                if zombie.rect.left <= self.rect.right:
                    self.activo = True
        else:
            self.rect.x += self.velocidad
            zombies_en_carril = [z for z in grupo_zombies if z.fila == self.fila]
            for zombie in zombies_en_carril:
                if self.rect.colliderect(zombie.rect):
                    zombie.kill()
            if self.rect.x > ANCHO_VENTANA:
                self.kill()

class Sol(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Intentará buscar sol.gif o sol.png. Si no, bolita nativa naranja/amarilla brillante
        self.frames = cargar_o_crear_sprite("sol.gif", 45, 45, (255, 215, 0))
        if len(self.frames) == 1 and not os.path.exists("sol.gif"):
            self.frames = cargar_o_crear_sprite("sol.png", 45, 45, (255, 215, 0))
            
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(INICIO_X, ANCHO_VENTANA - 100)
        self.rect.y = -40
        self.destino_y = random.randint(INICIO_Y, ALTO_VENTANA - 100)
        self.velocidad = 2
        self.frame_actual = 0
        self.ultimo_frame_time = pygame.time.get_ticks()

    def update(self):
        # Animación del Sol por si es un GIF
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_frame_time > 100 and len(self.frames) > 1:
            self.frame_actual = (self.frame_actual + 1) % len(self.frames)
            self.image = self.frames[self.frame_actual]
            self.ultimo_frame_time = ahora

        if self.rect.y < self.destino_y:
            self.rect.y += self.velocidad

# --- SISTEMA CENTRAL DEL JUEGO ---

class Juego:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
        pygame.display.set_caption("Pokémon vs Zombies - Visual Update")
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.SysFont("Arial", 22, bold=True)
        self.fuente_chica = pygame.font.SysFont("Arial", 14, bold=True)
        
        self.soles = 150
        self.game_over = False
        self.item_seleccionado = "bulbasaur"
        
        # --- CARGA DE TEXTURAS DE FONDO Y CASILLAS ---
        self.textura_fondo = None
        if os.path.exists("fondo.png"):
            self.textura_fondo = pygame.image.load("fondo.png").convert()
            self.textura_fondo = pygame.transform.smoothscale(self.textura_fondo, (ANCHO_VENTANA, ALTO_VENTANA))
            
        self.textura_pasto1 = None
        if os.path.exists("pasto1.jpg"):
            self.textura_pasto1 = pygame.image.load("pasto1.jpg").convert_alpha()
            self.textura_pasto1 = pygame.transform.smoothscale(self.textura_pasto1, (ANCHO_CASILLA, ALTO_CASILLA))
            
        self.textura_pasto2 = None
        if os.path.exists("pasto2.jpeg"):
            self.textura_pasto2 = pygame.image.load("pasto2.jpeg").convert_alpha()
            self.textura_pasto2 = pygame.transform.smoothscale(self.textura_pasto2, (ANCHO_CASILLA, ALTO_CASILLA))

        self.cartas = [
            {"id": "bulbasaur", "nombre": "Bulba", "costo": 100, "rect": pygame.Rect(180, 15, 90, 65), "color": (0, 180, 90)},
            {"id": "geodude", "nombre": "Geo", "costo": 50, "rect": pygame.Rect(285, 15, 90, 65), "color": (130, 130, 130)}
        ]
        
        self.rect_pokebola = pygame.Rect(400, 15, 90, 65)
        self.img_pokebola = None
        if os.path.exists("pokebola.png"):
            self.img_pokebola = pygame.image.load("pokebola.png").convert_alpha()
            self.img_pokebola = pygame.transform.smoothscale(self.img_pokebola, (40, 40))
        
        self.pokemon_group = pygame.sprite.Group()
        self.zombie_group = pygame.sprite.Group()
        self.proyectil_group = pygame.sprite.Group()
        self.carrito_group = pygame.sprite.Group()
        self.sol_group = pygame.sprite.Group()
        
        for f in range(FILAS):
            self.carrito_group.add(Carrito(f))
        
        self.grilla_logica = [[0 for _ in range(COLUMNAS)] for _ in range(FILAS)]
        
        self.ZOMBIE_SPAWN_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.ZOMBIE_SPAWN_EVENT, 5000)
        
        self.SOL_SPAWN_EVENT = pygame.USEREVENT + 2
        pygame.time.set_timer(self.SOL_SPAWN_EVENT, 7000)

    def dibujar_interfaz(self):
        # 1. Dibujar el Fondo General (Si existe fondo.png, se superpone)
        if self.textura_fondo:
            self.pantalla.blit(self.textura_fondo, (0, 0))
        else:
            self.pantalla.fill((85, 107, 47))
        
        # 2. Dibujar Tablero (Usa texturas pasto1.png y pasto2.png si existen)
        for f in range(FILAS):
            for c in range(COLUMNAS):
                x = INICIO_X + (c * ANCHO_CASILLA)
                y = INICIO_Y + (f * ALTO_CASILLA)
                
                es_par = (f + c) % 2 == 0
                if es_par:
                    if self.textura_pasto1:
                        self.pantalla.blit(self.textura_pasto1, (x, y))
                    else:
                        pygame.draw.rect(self.pantalla, COLOR_PASTO_1, (x, y, ANCHO_CASILLA, ALTO_CASILLA))
                else:
                    if self.textura_pasto2:
                        self.pantalla.blit(self.textura_pasto2, (x, y))
                    else:
                        pygame.draw.rect(self.pantalla, COLOR_PASTO_2, (x, y, ANCHO_CASILLA, ALTO_CASILLA))

        # 3. BANNER SUPERIOR DE LA UI
        pygame.draw.rect(self.pantalla, (60, 60, 60), (0, 0, ANCHO_VENTANA, 100))
        pygame.draw.line(self.pantalla, (255, 255, 255), (0, 100), (ANCHO_VENTANA, 100), 3)

        # Contador de soles
        pygame.draw.rect(self.pantalla, (220, 200, 140), (15, 15, 140, 65), border_radius=5)
        texto_soles = self.fuente.render(f"☀️ {self.soles}", True, (0, 0, 0))
        self.pantalla.blit(texto_soles, (35, 33))

        # Cartas de Pokémon
        for carta in self.cartas:
            fondable = self.soles >= carta["costo"]
            color_fondo = carta["color"] if fondable else (40, 40, 40)
            borde = 4 if self.item_seleccionado == carta["id"] else 1
            color_borde = (255, 215, 0) if self.item_seleccionado == carta["id"] else (100, 100, 100)
            
            pygame.draw.rect(self.pantalla, color_fondo, carta["rect"], border_radius=4)
            pygame.draw.rect(self.pantalla, color_borde, carta["rect"], borde, border_radius=4)
            
            t_nombre = self.fuente_chica.render(carta["nombre"], True, (255, 255, 255))
            t_costo = self.fuente_chica.render(f"${carta['costo']}", True, (255, 255, 0) if fondable else (150, 50, 50))
            self.pantalla.blit(t_nombre, (carta["rect"].x + 8, carta["rect"].y + 8))
            self.pantalla.blit(t_costo, (carta["rect"].x + 8, carta["rect"].y + 40))

        # Herramienta Pokébola
        color_pb = (200, 50, 50) if self.item_seleccionado == "pokebola" else (100, 50, 50)
        borde_pb = 4 if self.item_seleccionado == "pokebola" else 1
        color_b_pb = (255, 215, 0) if self.item_seleccionado == "pokebola" else (100, 100, 100)
        
        pygame.draw.rect(self.pantalla, color_pb, self.rect_pokebola, border_radius=4)
        pygame.draw.rect(self.pantalla, color_b_pb, self.rect_pokebola, borde_pb, border_radius=4)
        
        if self.img_pokebola:
            self.pantalla.blit(self.img_pokebola, (self.rect_pokebola.x + 25, self.rect_pokebola.y + 5))
        else:
            t_pala = self.fuente_chica.render("POKEBOLA", True, (255, 255, 255))
            self.pantalla.blit(t_pala, (self.rect_pokebola.x + 10, self.rect_pokebola.y + 12))
            
        t_accion = self.fuente_chica.render("(Quitar)", True, (230, 230, 230))
        self.pantalla.blit(t_accion, (self.rect_pokebola.x + 24, self.rect_pokebola.y + 42))

    def dibujar_barras_vida(self):
        for p in self.pokemon_group:
            if p.vida < p.vida_max:
                ancho_barra = 50 * (p.vida / p.vida_max)
                pygame.draw.rect(self.pantalla, (255, 0, 0), (p.rect.x, p.rect.y - 10, 50, 6))
                pygame.draw.rect(self.pantalla, (0, 255, 0), (p.rect.x, p.rect.y - 10, ancho_barra, 6))
        for z in self.zombie_group:
            if z.vida < z.vida_max:
                ancho_barra = 40 * (z.vida / z.vida_max)
                pygame.draw.rect(self.pantalla, (0, 0, 0), (z.rect.x, z.rect.y - 10, 40, 6))
                pygame.draw.rect(self.pantalla, (255, 0, 0), (z.rect.x, z.rect.y - 10, ancho_barra, 6))

    def obtener_casilla_por_click(self, pos_mouse):
        x, y = pos_mouse
        if INICIO_X <= x < INICIO_X + (COLUMNAS * ANCHO_CASILLA) and INICIO_Y <= y < INICIO_Y + (FILAS * ALTO_CASILLA):
            columna = (x - INICIO_X) // ANCHO_CASILLA
            fila = (y - INICIO_Y) // ALTO_CASILLA
            return fila, columna
        return None

    def bucle_principal(self):
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if not self.game_over:
                    if evento.type == self.ZOMBIE_SPAWN_EVENT:
                        self.zombie_group.add(Zombie(random.randint(0, FILAS - 1)))

                    if evento.type == self.SOL_SPAWN_EVENT:
                        self.sol_group.add(Sol())

                    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                        sol_clickeado = False
                        for sol in list(self.sol_group):
                            if sol.rect.collidepoint(evento.pos):
                                self.soles += 25
                                sol.kill()
                                sol_clickeado = True
                                break
                        
                        if sol_clickeado:
                            continue

                        menu_clickeado = False
                        for carta in self.cartas:
                            if carta["rect"].collidepoint(evento.pos):
                                self.item_seleccionado = carta["id"]
                                menu_clickeado = True
                                break
                        
                        if self.rect_pokebola.collidepoint(evento.pos):
                            self.item_seleccionado = "pokebola"
                            menu_clickeado = True
                            
                        if menu_clickeado:
                            continue

                        casilla = self.obtener_casilla_por_click(evento.pos)
                        if casilla:
                            f, c = casilla
                            
                            if self.item_seleccionado == "pokebola":
                                for p in list(self.pokemon_group):
                                    pkmn_c = (p.rect.centerx - INICIO_X) // ANCHO_CASILLA
                                    pkmn_f = (p.rect.centery - INICIO_Y) // ALTO_CASILLA
                                    if pkmn_f == f and pkmn_c == c:
                                        p.kill()
                                        self.grilla_logica[f][c] = 0
                                self.item_seleccionado = None
                                
                            elif self.item_seleccionado in ["bulbasaur", "geodude"]:
                                costo_actual = 100 if self.item_seleccionado == "bulbasaur" else 50
                                
                                if self.grilla_logica[f][c] == 0 and self.soles >= costo_actual:
                                    self.soles -= costo_actual
                                    centro_x = INICIO_X + (c * ANCHO_CASILLA) + (ANCHO_CASILLA // 2)
                                    centro_y = INICIO_Y + (f * ALTO_CASILLA) + (ALTO_CASILLA // 2)
                                    
                                    nuevo_pkmn = Pokemon(centro_x, centro_y, f, self.item_seleccionado)
                                    self.pokemon_group.add(nuevo_pkmn)
                                    self.grilla_logica[f][c] = 1
                else:
                    if evento.type == pygame.KEYDOWN or evento.type == pygame.MOUSEBUTTONDOWN:
                        self.__init__()

            if not self.game_over:
                self.grilla_logica = [[0 for _ in range(COLUMNAS)] for _ in range(FILAS)]
                for p in self.pokemon_group:
                    c = (p.rect.centerx - INICIO_X) // ANCHO_CASILLA
                    f = (p.rect.centery - INICIO_Y) // ALTO_CASILLA
                    if 0 <= f < FILAS and 0 <= c < COLUMNAS:
                        self.grilla_logica[f][c] = 1

                self.pokemon_group.update(self.zombie_group, self.proyectil_group)
                self.zombie_group.update(self.pokemon_group)
                self.proyectil_group.update()
                self.carrito_group.update(self.zombie_group)
                self.sol_group.update()

                for proyectil in self.proyectil_group:
                    zombies_afectados = [z for z in self.zombie_group if z.fila == proyectil.fila]
                    colisiones = pygame.sprite.spritecollide(proyectil, zombies_afectados, False)
                    if colisiones:
                        for zombie in colisiones:
                            zombie.vida -= 25
                        proyectil.kill()

                for zombie in self.zombie_group:
                    if zombie.rect.right < 0:
                        self.game_over = True

            self.dibujar_interfaz()

            self.carrito_group.draw(self.pantalla)
            self.pokemon_group.draw(self.pantalla)
            self.zombie_group.draw(self.pantalla)
            self.proyectil_group.draw(self.pantalla)
            self.sol_group.draw(self.pantalla)

            self.dibujar_barras_vida()

            if self.game_over:
                superficie_oscura = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
                superficie_oscura.fill((0, 0, 0, 180))
                self.pantalla.blit(superficie_oscura, (0, 0))
                fuente_go = pygame.font.SysFont("Arial", 40, bold=True)
                texto_go = fuente_go.render("¡LOS DEL TEAM ROCKET TE ROBARON EL POKEMON!", True, (255, 0, 0))
                rect_go = texto_go.get_rect(center=(ANCHO_VENTANA // 2, ALTO_VENTANA // 2 - 30))
                self.pantalla.blit(texto_go, rect_go)
                texto_restart = self.fuente.render("Haz clic o presiona una tecla para reiniciar", True, (255, 255, 255))
                rect_restart = texto_restart.get_rect(center=(ANCHO_VENTANA // 2, ALTO_VENTANA // 2 + 40))
                self.pantalla.blit(texto_restart, rect_restart)

            pygame.display.flip()
            self.reloj.tick(FPS)

if __name__ == "__main__":
    juego = Juego()
    juego.bucle_principal()
