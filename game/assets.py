"""Carga de imágenes con caché. Soporta png/jpg/webp/gif animado.
Busca en assets/images/<clave>.<ext>. Si no existe, usa el placeholder dibujado por código."""
import pygame
from pathlib import Path
from .placeholders import make as make_placeholder

EXTS = (".gif", ".png", ".webp", ".jpg", ".jpeg")


class Assets:
    def __init__(self, root):
        self.root = Path(root) / "images"
        self._cache = {}
        self._raw = {}
        self._fonts = {}

    # ---- búsqueda / carga ----
    def find(self, key):
        for ext in EXTS:
            p = self.root / f"{key}{ext}"
            if p.is_file():
                return p
        return None

    def _load_raw(self, path):
        if path in self._raw:
            return self._raw[path]
        frames = []
        if path.suffix.lower() == ".gif":
            try:
                from PIL import Image, ImageSequence
                im = Image.open(path)
                for fr in ImageSequence.Iterator(im):
                    rgba = fr.convert("RGBA")
                    mk = getattr(pygame.image, "frombytes", None) or pygame.image.fromstring
                    frames.append(mk(rgba.tobytes(), rgba.size, "RGBA").convert_alpha())
            except ImportError:
                print("Pillow no está instalado: el GIF se carga sin animación (pip install pillow)")
        if not frames:
            frames = [pygame.image.load(str(path)).convert_alpha()]
        self._raw[path] = frames
        return frames

    @staticmethod
    def _trim(frames):
        rects = [f.get_bounding_rect() for f in frames]
        u = rects[0].unionall(rects[1:])
        if u.w <= 0 or u.h <= 0:
            return frames
        return [f.subsurface(u).copy() for f in frames]

    @staticmethod
    def _scale(raw, size, flip, mode):
        out = []
        for f in raw:
            if mode == "stretch":
                s = pygame.transform.smoothscale(f, size)
            else:  # "fit": mantiene proporciones y centra
                fw, fh = f.get_size()
                k = min(size[0] / fw, size[1] / fh)
                nw, nh = max(1, int(fw * k)), max(1, int(fh * k))
                sc = pygame.transform.scale(f, (nw, nh)) if k > 1 else pygame.transform.smoothscale(f, (nw, nh))
                s = pygame.Surface(size, pygame.SRCALPHA)
                s.blit(sc, ((size[0] - nw) // 2, (size[1] - nh) // 2))
            if flip:
                s = pygame.transform.flip(s, True, False)
            out.append(s)
        return out

    def frames(self, key, size, flip=False, placeholder=None, mode="fit"):
        """Devuelve lista de Surfaces. `key` puede ser un str o una lista (se usa el primero que exista).
        Si no hay archivo ni placeholder devuelve None."""
        keys = [key] if isinstance(key, str) else list(key)
        ck = (tuple(keys), tuple(size), flip, mode, placeholder)
        if ck in self._cache:
            return self._cache[ck]
        result = None
        for k in keys:
            p = self.find(k)
            if p:
                try:
                    raw = self._load_raw(p)
                    if mode == "fit":
                        raw = self._trim(raw)
                    result = self._scale(raw, tuple(size), flip, mode)
                    break
                except Exception as e:  # archivo corrupto, etc.
                    print(f"Error cargando {p}: {e}")
        if result is None and placeholder is not None:
            result = [make_placeholder(placeholder, tuple(size))]
        self._cache[ck] = result
        return result

    def font(self, size, bold=True):
        k = (size, bold)
        if k not in self._fonts:
            self._fonts[k] = pygame.font.SysFont("arial,dejavusans,verdana", size, bold=bold)
        return self._fonts[k]
