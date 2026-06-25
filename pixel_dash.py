import pygame
import sys
import math
import random
import asyncio
import os

ESCALA       = 4
ANCHO_JUEGO  = 240
ALTO_JUEGO   = 135
ANCHO_REAL   = ANCHO_JUEGO * ESCALA
ALTO_REAL    = ALTO_JUEGO  * ESCALA
FPS          = 60
TILE         = 16
GRAVEDAD     = 0.4

NEGRO    = (  0,   0,   0)
BLANCO   = (255, 255, 255)
AMARILLO = (245, 197,  24)
ROJO     = (220,  50,  50)
GRIS     = (150, 150, 150)
ORO      = (255, 215,   0)

PALETAS = [
    {
        "cielo":  ( 13,  27,  42),
        "suelo":  ( 26, 107,  60),
        "suelo2": ( 46, 204, 113),
        "plat":   (100,  70, 160),
        "plat2":  (155, 120, 210),
        "acento": ( 46, 204, 113),
        "nombre": "PRADERA VERDE",
    },
    {
        "cielo":  ( 42,  20,   5),
        "suelo":  (140,  70,  10),
        "suelo2": (230, 126,  34),
        "plat":   (160,  80,  20),
        "plat2":  (210, 130,  60),
        "acento": (230, 126,  34),
        "nombre": "DESIERTO",
    },
    {
        "cielo":  ( 20,   5,  42),
        "suelo":  ( 74,   0, 114),
        "suelo2": (155,  89, 182),
        "plat":   ( 50,   0,  80),
        "plat2":  (130,  60, 180),
        "acento": (155,  89, 182),
        "nombre": "PALACIO",
    },
    {
        "cielo":  (  5,  15,  30),
        "suelo":  (  0,  80,  80),
        "suelo2": (  0, 188, 212),
        "plat":   (  0,  60,  80),
        "plat2":  (  0, 150, 180),
        "acento": (  0, 229, 255),
        "nombre": "ABISMO FINAL",
    },
]

MAPAS = [
    [
        "                              G",
        "                              #",
        "        PPP      PPP          #",
        "                             ##",
        "  S SS      E         SS    ###",
        "################################",
    ],
    [
        "                                G",
        "      PPP                       #",
        "                  PP            #",
        "  PP        E          E       ##",
        "  SS  SS  SSSS  SSS  SSSS     ###",
        "#################################",
    ],
    [
        "                                    G",
        "    PP        PP       PP           #",
        "         PP       E        PP      ##",
        " E    SS     SS      SS       SS  ###",
        "   SS    SSSS##   SSS##S   SSS##S####",
        "#####################################",
    ],
    [
        "                                          G",
        "  PP       PP        PP        PP         #",
        "      PP        PP        PP        PP   ##",
        " E   SSS  E   SSSS  E   SSSS  E   SSSS ###",
        " SSSS###SSSSSS####SSSSSS####SSSSSS####S####",
        "###########################################",
    ],
]

def es_web():
    return sys.platform == "emscripten"

class GameObject:
    def __init__(self, x, y, ancho, alto, color=BLANCO):
        self.x      = float(x)
        self.y      = float(y)
        self.ancho  = ancho
        self.alto   = alto
        self.color  = color
        self.activo = True

    def obtener_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.ancho, self.alto)

    def dibujar(self, lienzo, camara_x=0):
        pygame.draw.rect(
            lienzo, self.color,
            (int(self.x - camara_x), int(self.y), self.ancho, self.alto)
        )

    def actualizar(self):
        pass

class Suelo(GameObject):
    def __init__(self, x, y, paleta):
        super().__init__(x, y, TILE, TILE, paleta["suelo"])
        self.paleta = paleta

    def dibujar(self, lienzo, camara_x=0):
        super().dibujar(lienzo, camara_x)
        sx = int(self.x - camara_x)
        pygame.draw.rect(lienzo, self.paleta["suelo2"], (sx, int(self.y), TILE, 2))

class Plataforma(GameObject):
    def __init__(self, x, y, paleta):
        super().__init__(x, y, TILE, TILE, paleta["plat"])
        self.paleta = paleta

    def dibujar(self, lienzo, camara_x=0):
        super().dibujar(lienzo, camara_x)
        sx = int(self.x - camara_x)
        pygame.draw.rect(lienzo, self.paleta["plat2"], (sx, int(self.y), TILE, 2))

class Pico(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, TILE, TILE, GRIS)

    def dibujar(self, lienzo, camara_x=0):
        sx = int(self.x - camara_x)
        sy = int(self.y)
        if sx + TILE < 0 or sx > ANCHO_JUEGO:
            return

        for fila in range(TILE):
            mitad  = fila // 2
            inicio = sx + TILE // 2 - mitad
            ancho  = max(1, mitad * 2)
            pygame.draw.rect(lienzo, (200, 200, 200), (inicio, sy + fila, ancho, 1))
        for fila in range(TILE):
            pygame.draw.rect(lienzo, (120, 120, 120),
                             (sx + TILE // 2, sy + fila, 1, 1))

    def obtener_hitbox(self):
        return pygame.Rect(int(self.x) + 3, int(self.y) + 4, TILE - 6, TILE - 4)

class _Meta(GameObject):
    def __init__(self, x, y, paleta):
        super().__init__(x, y, TILE, TILE * 2, paleta["acento"])
        self.paleta      = paleta
        self.frame_timer = 0

    def actualizar(self):
        self.frame_timer += 1

    def dibujar(self, lienzo, camara_x=0):
        sx = int(self.x - camara_x)
        sy = int(self.y)
        if sx + TILE < 0 or sx > ANCHO_JUEGO:
            return

        pygame.draw.rect(lienzo, GRIS, (sx + 7, sy - 10, 2, TILE * 2 + 10))

        for i in range(8):
            wave = int(math.sin(self.frame_timer * 0.15 + i * 0.5) * 2)
            pygame.draw.rect(lienzo, self.paleta["acento"],
                             (sx + 9 + wave, sy - 10 + i, 6, 1))

        pygame.draw.rect(lienzo, ORO, (sx + 5, sy - 14, 4, 4))

class Enemigo(GameObject):
    def __init__(self, x, y, paleta, nivel_idx=0):
        super().__init__(x, y, TILE - 2, TILE - 2, ROJO)
        self.dir         = 1
        self.inicio_x    = x
        self.rango       = TILE * 3 + nivel_idx * TILE
        self.velocidad   = 0.6 + nivel_idx * 0.15
        self.frame_timer = 0

    def actualizar(self):
        self.x += self.dir * self.velocidad
        self.frame_timer += 1
        if self.x > self.inicio_x + self.rango:
            self.dir = -1
        elif self.x < self.inicio_x - self.rango * 0.2:
            self.dir = 1

    def dibujar(self, lienzo, camara_x=0):
        sx = int(self.x - camara_x)
        sy = int(self.y)
        if sx + self.ancho < 0 or sx > ANCHO_JUEGO:
            return
        sprite = [
            [0,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1],
            [1,1,2,1,1,2,1,1],
            [1,1,3,1,1,3,1,1],
            [1,1,1,2,2,1,1,1],
            [1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,0],
            [0,0,1,0,0,1,0,0],
        ]
        colores = {1: ROJO, 2: BLANCO, 3: NEGRO}
        leg_off = (self.frame_timer // 8) % 2
        for ry, fila in enumerate(sprite):
            for rx, pixel in enumerate(fila):
                if pixel:
                    draw_rx = rx if self.dir > 0 else (7 - rx)
                    dy = (leg_off if rx in [2, 5] else -leg_off) if ry == 7 else 0
                    pygame.draw.rect(lienzo, colores[pixel],
                                     (sx + draw_rx, sy + ry + dy, 1, 1))

class Particula(GameObject):
    def __init__(self, x, y, color):
        size = random.randint(1, 3)
        super().__init__(x, y, size, size, color)
        self.vx       = random.uniform(-2.5,  2.5)
        self.vy       = random.uniform(-4.0, -0.5)
        self.vida     = random.randint(20, 45)
        self.vida_max = self.vida

    def actualizar(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.18
        self.vida -= 1
        if self.vida <= 0:
            self.activo = False

    def dibujar(self, lienzo, camara_x=0):
        alpha = self.vida / self.vida_max
        size  = max(1, int(self.ancho * alpha))
        pygame.draw.rect(lienzo, self.color,
                         (int(self.x - camara_x), int(self.y), size, size))

class GestorParticulas:
    def __init__(self):
        self.particulas = []

    def emitir(self, x, y, color, cantidad=12):
        for _ in range(cantidad):
            self.particulas.append(Particula(x, y, color))

    def actualizar(self):
        for p in self.particulas:
            p.actualizar()
        self.particulas = [p for p in self.particulas if p.activo]

    def dibujar(self, lienzo, camara_x=0):
        for p in self.particulas:
            p.dibujar(lienzo, camara_x)

class Camara:
    def __init__(self):
        self.x = 0.0

    def actualizar(self, jugador_x, ancho_nivel):
        target = jugador_x - ANCHO_JUEGO * 0.3
        self.x += (target - self.x) * 0.1
        self.x = max(0, min(self.x, ancho_nivel - ANCHO_JUEGO))

class Jugador(GameObject):
    VELOCIDAD    = 2.0
    FUERZA_SALTO = -5.5
    MAX_SALTOS   = 2

    def __init__(self, x, y):
        super().__init__(x, y, 7, 8, AMARILLO)
        self.vx          = 0.0
        self.vy          = 0.0
        self.en_suelo    = False
        self.saltos_disp = self.MAX_SALTOS
        self.mirando_der = True
        self.frame_timer = 0
        self.invencible  = 0
        self.muerto      = False

    def saltar(self):
        if self.saltos_disp > 0:
            self.vy          = self.FUERZA_SALTO
            self.saltos_disp -= 1
            self.en_suelo    = False
            return True
        return False

    def aplicar_gravedad(self):
        self.vy += GRAVEDAD
        if self.vy > 8:
            self.vy = 8

    def mover_y_colisionar(self, solidos):
        self.x += self.vx
        rect = self.obtener_rect()
        for s in solidos:
            sr = s.obtener_rect()
            if rect.colliderect(sr):
                if self.vx > 0: self.x = sr.left - self.ancho
                elif self.vx < 0: self.x = sr.right
                rect = self.obtener_rect()

        self.y += self.vy
        self.en_suelo = False
        rect = self.obtener_rect()
        for s in solidos:
            sr = s.obtener_rect()
            if rect.colliderect(sr):
                if self.vy > 0:
                    self.y = sr.top - self.alto
                    self.vy = 0
                    self.en_suelo = True
                    self.saltos_disp = self.MAX_SALTOS
                elif self.vy < 0:
                    self.y = sr.bottom
                    self.vy = 0
                rect = self.obtener_rect()

    def manejar_input(self, teclas, touch_izq=False, touch_der=False):
        ir_izq = teclas[pygame.K_LEFT] or teclas[pygame.K_a] or touch_izq
        ir_der = teclas[pygame.K_RIGHT] or teclas[pygame.K_d] or touch_der

        if ir_izq:
            self.vx = -self.VELOCIDAD
            self.mirando_der = False
        elif ir_der:
            self.vx = self.VELOCIDAD
            self.mirando_der = True
        else:
            self.vx = 0.0

    def actualizar(self):
        self.frame_timer += 1
        if self.invencible > 0:
            self.invencible -= 1

    def esta_invencible(self):
        return self.invencible > 0

    def dibujar(self, lienzo, camara_x=0):
        if self.muerto:
            return
        if self.invencible > 0 and (self.frame_timer // 4) % 2 == 0:
            return

        sx = int(self.x - camara_x)
        sy = int(self.y)

        sprite = [
            [0,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1],
            [1,1,2,1,1,2,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,2,2,2,2,1,1],
            [1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,0],
            [0,0,1,0,0,1,0,0],
        ]
        colores = {1: AMARILLO, 2: (40, 40, 40)}

        leg_off = 0
        if self.en_suelo and abs(self.vx) > 0:
            leg_off = (self.frame_timer // 6) % 2

        for ry, fila in enumerate(sprite):
            for rx, pixel in enumerate(fila):
                if pixel:
                    draw_rx = rx if self.mirando_der else (7 - rx)
                    dy = (leg_off if rx in [2, 5] else -leg_off) if ry == 7 else 0
                    pygame.draw.rect(lienzo, colores[pixel],
                                     (sx + draw_rx, sy + ry + dy, 1, 1))

        if not self.en_suelo:
            pygame.draw.rect(lienzo, (180, 150, 20), (sx - 1, sy + 2, 2, 4))

class Nivel:
    def __init__(self, indice):
        self.indice      = indice
        self.paleta      = PALETAS[indice]
        self.mapa        = MAPAS[indice]
        self.suelos      = []
        self.plataformas = []
        self.picos       = []
        self.enemigos    = []
        self.meta        = None
        self.ancho       = max(len(f) for f in self.mapa) * TILE
        self._construir()

    def _construir(self):
        for fi, fila in enumerate(self.mapa):
            for ci, char in enumerate(fila):
                x = ci * TILE
                y = fi * TILE
                if   char == '#': self.suelos.append(Suelo(x, y, self.paleta))
                elif char == 'P': self.plataformas.append(Plataforma(x, y, self.paleta))
                elif char == 'S': self.picos.append(Pico(x, y))
                elif char == 'E': self.enemigos.append(Enemigo(x, y - 2, self.paleta, self.indice))
                elif char == 'G': self.meta = _Meta(x, y, self.paleta)

    @property
    def solidos(self):
        return self.suelos + self.plataformas

    def inicio(self):
        return (TILE, TILE)

class GestorNiveles:
    TOTAL = 4

    def __init__(self):
        self.indice = 0
        self.nivel  = Nivel(0)

    def cargar(self, indice):
        self.indice = indice
        self.nivel  = Nivel(indice)

    def siguiente(self):
        if self.indice < self.TOTAL - 1:
            self.cargar(self.indice + 1)
            return True
        return False

class GestorTouch:
    ZONA_Y    = ALTO_JUEGO - 26
    BTN_ANCHO = 32

    def __init__(self):
        self.izquierda = False
        self.derecha   = False
        self._finger_izq = None
        self._finger_der = None

    def _lx(self, x_norm):
        return x_norm * ANCHO_JUEGO

    def _ly(self, y_norm):
        return y_norm * ALTO_JUEGO

    def _en_zona_botones(self, ly):
        return ly > self.ZONA_Y

    def _en_boton_izq(self, lx, ly):
        return self._en_zona_botones(ly) and lx < self.BTN_ANCHO

    def _en_boton_der(self, lx, ly):
        return (self._en_zona_botones(ly) and
                self.BTN_ANCHO <= lx < self.BTN_ANCHO * 2)

    def _en_boton_saltar(self, lx, ly):
        return self._en_zona_botones(ly) and lx > ANCHO_JUEGO - 50

    def finger_down(self, finger_id, x_norm, y_norm):
        lx = self._lx(x_norm)
        ly = self._ly(y_norm)

        if self._en_boton_izq(lx, ly):
            self.izquierda   = True
            self._finger_izq = finger_id
            return None
        elif self._en_boton_der(lx, ly):
            self.derecha     = True
            self._finger_der = finger_id
            return None
        else:
            return 'saltar'

    def finger_up(self, finger_id, x_norm, y_norm):
        if finger_id == self._finger_izq:
            self.izquierda   = False
            self._finger_izq = None
        if finger_id == self._finger_der:
            self.derecha     = False
            self._finger_der = None

    def finger_motion(self, finger_id, x_norm, y_norm):
        lx = self._lx(x_norm)
        ly = self._ly(y_norm)

        if finger_id == self._finger_izq and self._en_boton_der(lx, ly):
            self.izquierda   = False
            self._finger_izq = None
            self.derecha     = True
            self._finger_der = finger_id
        elif finger_id == self._finger_der and self._en_boton_izq(lx, ly):
            self.derecha     = False
            self._finger_der = None
            self.izquierda   = True
            self._finger_izq = finger_id

class Renderer:
    FUENTE = {
        'A':["010","101","111","101","101"], 'B':["110","101","110","101","110"],
        'C':["111","100","100","100","111"], 'D':["110","101","101","101","110"],
        'E':["111","100","110","100","111"], 'F':["111","100","110","100","100"],
        'G':["111","100","101","101","111"], 'H':["101","101","111","101","101"],
        'I':["111","010","010","010","111"], 'J':["001","001","001","101","111"],
        'K':["101","110","100","110","101"], 'L':["100","100","100","100","111"],
        'M':["101","111","111","101","101"], 'N':["101","111","111","101","101"],
        'O':["111","101","101","101","111"], 'P':["110","101","110","100","100"],
        'R':["110","101","110","101","101"], 'S':["111","100","111","001","111"],
        'T':["111","010","010","010","010"], 'U':["101","101","101","101","111"],
        'V':["101","101","101","101","010"], 'W':["101","101","111","111","101"],
        'X':["101","101","010","101","101"], 'Y':["101","101","010","010","010"],
        'Z':["111","001","010","100","111"],
        '0':["111","101","101","101","111"], '1':["010","110","010","010","111"],
        '2':["111","001","111","100","111"], '3':["111","001","111","001","111"],
        '4':["101","101","111","001","001"], '5':["111","100","111","001","111"],
        '6':["111","100","111","101","111"], '7':["111","001","001","001","001"],
        '8':["111","101","111","101","111"], '9':["111","101","111","001","111"],
        ' ':["000","000","000","000","000"], '-':["000","000","111","000","000"],
        '!':["010","010","010","000","010"], ':':["000","010","000","010","000"],
        '.':["000","000","000","000","010"], '<':["001","010","100","010","001"],
        '>':["100","010","001","010","100"],
    }

    def __init__(self, lienzo):
        self.lienzo = lienzo
        self.estrellas = [
            (random.randint(0, ANCHO_JUEGO * 4),
             random.randint(0, ALTO_JUEGO * 2 // 3))
            for _ in range(40)
        ]

    def texto(self, msg, x, y, color):
        cx = x
        for char in msg.upper():
            if char in self.FUENTE:
                for ry, fila in enumerate(self.FUENTE[char]):
                    for rx, bit in enumerate(fila):
                        if bit == '1':
                            pygame.draw.rect(self.lienzo, color,
                                             (cx + rx, y + ry, 1, 1))
                cx += 4

    def fondo(self, paleta, camara_x, tiempo):
        self.lienzo.fill(paleta["cielo"])
        for (ex, ey) in self.estrellas:
            px = int(ex - camara_x * 0.2) % ANCHO_JUEGO
            py = ey % (ALTO_JUEGO * 2 // 3)
            if math.sin(tiempo * 0.04 + ex * 0.1) > 0.4:
                pygame.draw.rect(self.lienzo, BLANCO, (px, py, 1, 1))

    def hud(self, vidas, nivel_idx, puntaje, progreso):
        pygame.draw.rect(self.lienzo, NEGRO, (0, 0, ANCHO_JUEGO, 10))

        for i in range(vidas):
            cx = 3 + i * 8
            pygame.draw.rect(self.lienzo, ROJO, (cx,   2, 3, 3))
            pygame.draw.rect(self.lienzo, ROJO, (cx+3, 2, 3, 3))
            pygame.draw.rect(self.lienzo, ROJO, (cx+1, 4, 4, 3))
            pygame.draw.rect(self.lienzo, ROJO, (cx+2, 6, 1, 1))

        nombre = PALETAS[nivel_idx]["nombre"]
        self.texto(nombre, ANCHO_JUEGO // 2 - len(nombre) * 2, 2,
                   PALETAS[nivel_idx]["acento"])

        pts = f"{puntaje:05d}"
        self.texto(pts, ANCHO_JUEGO - len(pts) * 4 - 2, 2, BLANCO)

        pygame.draw.rect(self.lienzo, (50,50,50),
                         (0, ALTO_JUEGO - 2, ANCHO_JUEGO, 2))
        pygame.draw.rect(self.lienzo, PALETAS[nivel_idx]["acento"],
                         (0, ALTO_JUEGO - 2,
                          int(ANCHO_JUEGO * progreso), 2))

    def botones_moviles(self, paleta, touch):
        BY = GestorTouch.ZONA_Y
        BH = ALTO_JUEGO - BY - 2

        color_izq = paleta["acento"] if touch.izquierda else (60, 60, 80)
        btn = pygame.Surface((30, BH), pygame.SRCALPHA)
        btn.fill((*color_izq, 160))
        self.lienzo.blit(btn, (2, BY))
        pygame.draw.rect(self.lienzo, paleta["acento"], (2, BY, 30, BH), 1)
        self.texto("<", 12, BY + BH // 2 - 2,
                   NEGRO if touch.izquierda else paleta["acento"])

        color_der = paleta["acento"] if touch.derecha else (60, 60, 80)
        btn2 = pygame.Surface((30, BH), pygame.SRCALPHA)
        btn2.fill((*color_der, 160))
        self.lienzo.blit(btn2, (34, BY))
        pygame.draw.rect(self.lienzo, paleta["acento"], (34, BY, 30, BH), 1)
        self.texto(">", 44, BY + BH // 2 - 2,
                   NEGRO if touch.derecha else paleta["acento"])

        BW = 46
        BX = ANCHO_JUEGO - BW - 2
        btn3 = pygame.Surface((BW, BH), pygame.SRCALPHA)
        btn3.fill((*paleta["acento"], 180))
        self.lienzo.blit(btn3, (BX, BY))
        pygame.draw.rect(self.lienzo, BLANCO, (BX, BY, BW, BH), 1)
        self.texto("SALTAR", BX + 3, BY + BH // 2 - 2, NEGRO)

    def pantalla_menu(self, tiempo, es_movil):
        self.lienzo.fill((10, 15, 30))
        for i in range(30):
            ex = (i * 37 + 5) % ANCHO_JUEGO
            ey = (i * 19 + 3) % (ALTO_JUEGO - 40)
            if math.sin(tiempo * 0.04 + i) > 0.4:
                pygame.draw.rect(self.lienzo, BLANCO, (ex, ey, 1, 1))

        self.texto("PIXEL DASH", ANCHO_JUEGO // 2 - 22, 22, (80, 60, 0))
        self.texto("PIXEL DASH", ANCHO_JUEGO // 2 - 22, 21, ORO)
        self.texto("4 NIVELES DE PLATAFORMAS",
                   ANCHO_JUEGO // 2 - 48, 36, GRIS)

        pulse = abs(math.sin(tiempo * 0.06)) > 0.5
        color_btn = PALETAS[0]["acento"] if pulse else BLANCO

        if es_movil:
            self.texto("TAP PARA JUGAR",
                       ANCHO_JUEGO // 2 - 28, 58, color_btn)
            self.texto("TAP PANTALLA - SALTAR",   20, 78, GRIS)
            self.texto("BOTONES ABAJO - MOVER",   20, 86, GRIS)
        else:
            self.texto("ESPACIO PARA JUGAR",
                       ANCHO_JUEGO // 2 - 36, 58, color_btn)
            self.texto("A D FLECHAS - MOVER",     20, 78, GRIS)
            self.texto("ESPACIO W - SALTAR",       20, 86, GRIS)
            self.texto("DOBLE SALTO PERMITIDO",    20, 94, GRIS)
            self.texto("R REINICIAR  ESC MENU",    20,102, GRIS)

    def overlay_muerte(self, vidas, timer, es_movil):
        s = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO), pygame.SRCALPHA)
        s.fill((200, 0, 0, 70))
        self.lienzo.blit(s, (0, 0))
        if timer % 30 < 15:
            accion = "TAP" if es_movil else "ESPACIO"
            if vidas > 0:
                self.texto("PERDISTE UNA VIDA",  22, 45, BLANCO)
                self.texto(f"VIDAS: {vidas}",    50, 57, ROJO)
                self.texto(f"{accion} CONTINUAR", 22, 69, GRIS)
            else:
                self.texto("SIN VIDAS",          45, 50, ROJO)
                self.texto(f"{accion} REINICIAR", 22, 62, GRIS)

    def overlay_nivel_completo(self, nivel_idx, timer, es_movil):
        s = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO), pygame.SRCALPHA)
        s.fill((0, 180, 0, 60))
        self.lienzo.blit(s, (0, 0))
        if timer % 30 < 20:
            accion = "TAP" if es_movil else "ESPACIO"
            self.texto("NIVEL COMPLETO!", 28, 44, ORO)
            if nivel_idx < 3:
                self.texto(f"{accion} CONTINUAR", 22, 60, BLANCO)
            else:
                self.texto("GANASTE EL JUEGO!", 22, 60, ORO)
                self.texto("ERES UN CAMPEON",   26, 72, AMARILLO)

    def pantalla_game_over(self, puntaje, tiempo, es_movil):
        self.lienzo.fill((20, 0, 0))
        pulse = abs(math.sin(tiempo * 0.06)) > 0.5
        self.texto("GAME OVER",
                   ANCHO_JUEGO // 2 - 18, 38,
                   ROJO if pulse else (140, 0, 0))
        self.texto(f"PUNTAJE: {puntaje}",
                   ANCHO_JUEGO // 2 - 20, 58, BLANCO)
        accion = "TAP" if es_movil else "ESPACIO"
        self.texto(f"{accion} REINICIAR",
                   ANCHO_JUEGO // 2 - 36, 76, GRIS)

class Juego:
    MENU           = "menu"
    JUGANDO        = "jugando"
    MUERTO         = "muerto"
    NIVEL_COMPLETO = "nivel_completo"
    GAME_OVER      = "game_over"

    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO_REAL, ALTO_REAL))
        pygame.display.set_caption("Pixel Dash")

        self.lienzo = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO))
        self.reloj  = pygame.time.Clock()

        self.renderer   = Renderer(self.lienzo)
        self.gestor_niv = GestorNiveles()
        self.camara     = Camara()
        self.particulas = GestorParticulas()

        self.movil = es_web()

        if self.movil:
            self.touch = GestorTouch()
        else:
            self.touch = None

        self.estado       = self.MENU
        self.timer_estado = 0
        self.tiempo       = 0

        self.vidas   = 3
        self.puntaje = 0
        self.jugador = None

    def _iniciar_partida(self):
        self.vidas   = 3
        self.puntaje = 0
        self.gestor_niv.cargar(0)
        self._cargar_jugador()
        self.estado = self.JUGANDO

    def _cargar_jugador(self):
        ix, iy      = self.gestor_niv.nivel.inicio()
        self.jugador = Jugador(ix, iy)
        self.camara  = Camara()
        self.particulas = GestorParticulas()

    def _reiniciar_jugador(self):
        ix, iy      = self.gestor_niv.nivel.inicio()
        self.jugador = Jugador(ix, iy)
        self.jugador.invencible = 120
        self.camara  = Camara()

    def _morir(self):
        self.vidas -= 1
        self.particulas.emitir(
            self.jugador.x + 4, self.jugador.y + 4, AMARILLO, 15)
        self.particulas.emitir(
            self.jugador.x + 4, self.jugador.y + 4, ROJO, 8)
        self.jugador.muerto = True
        self.estado         = self.MUERTO
        self.timer_estado   = 0

    def _ganar_nivel(self):
        self.puntaje += self.vidas * 100 + (4 - self.gestor_niv.indice) * 50
        niv = self.gestor_niv.nivel
        for _ in range(4):
            self.particulas.emitir(
                niv.meta.x + 8, niv.meta.y, niv.paleta["acento"], 12)
        self.particulas.emitir(niv.meta.x + 8, niv.meta.y, ORO, 10)
        self.estado       = self.NIVEL_COMPLETO
        self.timer_estado = 0

    def _accion_tap(self):
        if self.estado == self.MENU:
            self._iniciar_partida()

        elif self.estado == self.MUERTO and self.timer_estado > 60:
            if self.vidas > 0:
                self._reiniciar_jugador()
                self.estado = self.JUGANDO
            else:
                self.estado = self.GAME_OVER

        elif self.estado == self.NIVEL_COMPLETO and self.timer_estado > 60:
            if self.gestor_niv.siguiente():
                self._cargar_jugador()
                self.estado = self.JUGANDO
            else:
                self.estado = self.MENU

        elif self.estado == self.GAME_OVER:
            self._iniciar_partida()

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                self._keydown(evento.key)

            if self.touch is not None:
                if evento.type == pygame.FINGERDOWN:
                    accion = self.touch.finger_down(
                        evento.finger_id, evento.x, evento.y)
                    if accion == 'saltar':
                        if self.estado == self.JUGANDO:
                            if self.jugador.saltar():
                                self.particulas.emitir(
                                    self.jugador.x + 4,
                                    self.jugador.y + 8,
                                    self.gestor_niv.nivel.paleta["acento"], 5)
                        else:
                            self._accion_tap()

                if evento.type == pygame.FINGERUP:
                    self.touch.finger_up(
                        evento.finger_id, evento.x, evento.y)

                if evento.type == pygame.FINGERMOTION:
                    self.touch.finger_motion(
                        evento.finger_id, evento.x, evento.y)

    def _keydown(self, key):
        if key == pygame.K_ESCAPE:
            self.estado = self.MENU
            return

        if self.estado == self.MENU:
            if key == pygame.K_SPACE:
                self._iniciar_partida()

        elif self.estado == self.JUGANDO:
            if key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                if self.jugador.saltar():
                    self.particulas.emitir(
                        self.jugador.x + 4, self.jugador.y + 8,
                        self.gestor_niv.nivel.paleta["acento"], 5)
            if key == pygame.K_r:
                self._reiniciar_jugador()

        elif self.estado == self.MUERTO and self.timer_estado > 60:
            if key == pygame.K_SPACE:
                if self.vidas > 0:
                    self._reiniciar_jugador()
                    self.estado = self.JUGANDO
                else:
                    self.estado = self.GAME_OVER

        elif self.estado == self.NIVEL_COMPLETO and self.timer_estado > 60:
            if key == pygame.K_SPACE:
                if self.gestor_niv.siguiente():
                    self._cargar_jugador()
                    self.estado = self.JUGANDO
                else:
                    self.estado = self.MENU

        elif self.estado == self.GAME_OVER:
            if key == pygame.K_SPACE:
                self._iniciar_partida()

    def actualizar(self):
        self.tiempo       += 1
        self.timer_estado += 1

        self.particulas.actualizar()
        niv = self.gestor_niv.nivel
        if niv.meta and self.estado in (self.JUGANDO, self.NIVEL_COMPLETO):
            niv.meta.actualizar()

        if self.estado != self.JUGANDO:
            return

        j = self.jugador

        j.aplicar_gravedad()
        teclas = pygame.key.get_pressed()

        touch_izq = self.touch.izquierda if self.touch else False
        touch_der = self.touch.derecha   if self.touch else False
        j.manejar_input(teclas, touch_izq, touch_der)

        j.mover_y_colisionar(niv.solidos)
        j.actualizar()

        for e in niv.enemigos:
            e.actualizar()

        self.camara.actualizar(j.x, niv.ancho)

        if j.y > ALTO_JUEGO + 30:
            self._morir()
            return

        jr = j.obtener_rect()

        for pico in niv.picos:
            if not j.esta_invencible():
                if jr.colliderect(pico.obtener_hitbox()):
                    self._morir()
                    return

        for e in niv.enemigos:
            if not j.esta_invencible():
                if jr.colliderect(e.obtener_rect()):
                    self._morir()
                    return

        if niv.meta and jr.colliderect(niv.meta.obtener_rect()):
            self._ganar_nivel()
            return

        self.puntaje = max(
            self.puntaje,
            int(j.x / max(1, niv.ancho - TILE * 2) * 1000)
            + self.gestor_niv.indice * 1000
        )

    def dibujar(self):
        niv   = self.gestor_niv.nivel
        cam_x = self.camara.x

        if self.estado == self.MENU:
            self.renderer.pantalla_menu(self.tiempo, self.movil)

        elif self.estado == self.GAME_OVER:
            self.renderer.pantalla_game_over(
                self.puntaje, self.tiempo, self.movil)

        else:
            self.renderer.fondo(niv.paleta, cam_x, self.tiempo)

            for obj in niv.solidos:
                obj.dibujar(self.lienzo, cam_x)
            for pico in niv.picos:
                pico.dibujar(self.lienzo, cam_x)

            if niv.meta:
                niv.meta.dibujar(self.lienzo, cam_x)

            for e in niv.enemigos:
                e.dibujar(self.lienzo, cam_x)

            self.particulas.dibujar(self.lienzo, cam_x)

            self.jugador.dibujar(self.lienzo, cam_x)

            progreso = min(1.0, self.jugador.x / max(1, niv.ancho - TILE * 2))
            self.renderer.hud(
                self.vidas, self.gestor_niv.indice, self.puntaje, progreso)

            if self.movil and self.touch is not None:
                self.renderer.botones_moviles(niv.paleta, self.touch)

            if self.estado == self.MUERTO:
                self.renderer.overlay_muerte(
                    self.vidas, self.timer_estado, self.movil)
            elif self.estado == self.NIVEL_COMPLETO:
                self.renderer.overlay_nivel_completo(
                    self.gestor_niv.indice, self.timer_estado, self.movil)

        escalado = pygame.transform.scale(self.lienzo, (ANCHO_REAL, ALTO_REAL))
        self.pantalla.blit(escalado, (0, 0))
        pygame.display.flip()

    async def ejecutar(self):
        while True:
            self.manejar_eventos()
            self.actualizar()
            self.dibujar()
            self.reloj.tick(FPS)
            await asyncio.sleep(0)

if __name__ == "__main__":
    juego = Juego()
    asyncio.run(juego.ejecutar())