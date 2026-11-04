"""Widgets simples: botones, sliders, texto."""
import pygame


def draw_text(surf, font, text, pos, color=(255, 255, 255), center=False, shadow=True, topright=False):
    img = font.render(text, True, color)
    r = img.get_rect()
    if center:
        r.center = pos
    elif topright:
        r.topright = pos
    else:
        r.topleft = pos
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        surf.blit(sh, r.move(2, 2))
    surf.blit(img, r)
    return r


def gradient(size, top, bottom):
    s = pygame.Surface(size)
    for y in range(size[1]):
        k = y / max(1, size[1] - 1)
        pygame.draw.line(s, tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)), (0, y), (size[0], y))
    return s


def draw_tipo_tag(surf, assets, tipo, pos, size=13):
    """Etiqueta de color con el nombre del tipo."""
    from .tipos import COLORES, NOMBRES
    img = assets.font(size).render(NOMBRES[tipo], True, (255, 255, 255))
    box = pygame.Rect(pos[0], pos[1], img.get_width() + 8, img.get_height() + 2)
    pygame.draw.rect(surf, COLORES[tipo], box, border_radius=6)
    pygame.draw.rect(surf, (0, 0, 0), box, 1, border_radius=6)
    surf.blit(img, (box.x + 4, box.y + 1))
    return box


class Button:
    def __init__(self, rect, text, callback, size=26, color=(70, 130, 200), enabled=True):
        self.rect = pygame.Rect(rect)
        self.text, self.callback, self.size, self.color, self.enabled = text, callback, size, color, enabled

    def handle_event(self, e, app):
        if self.enabled and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            app.audio.play("click")
            self.callback()
            return True
        return False

    def draw(self, surf, app):
        hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        col = self.color if self.enabled else (90, 90, 90)
        if hover:
            col = tuple(min(255, c + 35) for c in col)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        pygame.draw.rect(surf, (255, 255, 255), self.rect, 2, border_radius=10)
        draw_text(surf, app.assets.font(self.size), self.text, self.rect.center, center=True)


def handle_buttons(buttons, e, app):
    for b in buttons:
        if b.handle_event(e, app):
            return True
    return False


class Slider:
    def __init__(self, rect, value, on_change):
        self.rect = pygame.Rect(rect)
        self.value, self.on_change, self.drag = value, on_change, False

    def _set(self, x):
        self.value = max(0.0, min(1.0, (x - self.rect.x) / self.rect.w))
        self.on_change(self.value)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.inflate(16, 24).collidepoint(e.pos):
            self.drag = True
            self._set(e.pos[0])
        elif e.type == pygame.MOUSEMOTION and self.drag:
            self._set(e.pos[0])
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = False

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (40, 40, 40), r, border_radius=6)
        pygame.draw.rect(surf, (90, 200, 110), (r.x, r.y, int(r.w * self.value), r.h), border_radius=6)
        pygame.draw.circle(surf, (255, 255, 255), (r.x + int(r.w * self.value), r.centery), r.h)