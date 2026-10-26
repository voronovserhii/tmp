"""Paper cut-out helpers: torn edges, paper grain, drop shadows, safe blits, rotation around a pivot."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

rng = np.random.default_rng(11)
_GRAIN = None


def grain(w, h):
    """Near-white fibre texture to multiply over coloured paper."""
    global _GRAIN
    if _GRAIN is None:
        coarse = rng.normal(0, 1, (700, 500)).astype(np.float32)
        coarse = np.array(Image.fromarray(coarse).resize((2000, 2800), Image.BICUBIC))
        fine = rng.normal(0, 1, (2800, 2000)).astype(np.float32)
        fib = np.array(Image.fromarray(rng.normal(0, 1, (2800, 160)).astype(np.float32)).resize((2000, 2800), Image.BILINEAR))
        g = 236 + coarse * 7 + fine * 5 + fib * 4
        _GRAIN = Image.fromarray(np.clip(g, 190, 255).astype(np.uint8))
    x = int(rng.integers(0, max(1, 2000 - w)))
    y = int(rng.integers(0, max(1, 2800 - h)))
    if w > 2000 or h > 2800:
        return _GRAIN.resize((max(w, 2000), max(h, 2800))).crop((0, 0, w, h))
    return _GRAIN.crop((x, y, x + w, y + h))


def roughen(alpha, amount=0.35, blur=1.6):
    a = np.asarray(alpha.filter(ImageFilter.GaussianBlur(blur)), dtype=np.float32) / 255
    h, w = a.shape
    nz = rng.normal(0, 1, (h // 3 + 2, w // 3 + 2)).astype(np.float32)
    nz = np.array(Image.fromarray(nz).resize((w, h), Image.BILINEAR))
    a = a + nz * amount * 0.25
    a = np.clip((a - 0.45) / 0.1, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


class Sprite:
    def __init__(self, img, pad=0):
        self.img = img
        self.pad = pad

    @property
    def w(self):
        return self.img.width - 2 * self.pad

    @property
    def h(self):
        return self.img.height - 2 * self.pad

    def scaled(self, s):
        if s == 1:
            return self
        im = self.img.resize((max(1, int(self.img.width * s)), max(1, int(self.img.height * s))), Image.LANCZOS)
        return Sprite(im, int(self.pad * s))


def cut(w, h, draw_fn, rough=0.35, shadow=True, tex=True, edge=None):
    """Draw with draw_fn(draw, layer) onto a w×h layer and turn it into a paper piece."""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d, layer)
    r, g, b, a = layer.split()
    if rough:
        a = roughen(a, rough)
    rgb = Image.merge("RGB", (r, g, b))
    if tex:
        gr = grain(w, h).convert("RGB")
        rgb = Image.fromarray((np.asarray(rgb, dtype=np.uint16) * np.asarray(gr, dtype=np.uint16) // 255).astype(np.uint8))
    if edge:
        # slightly darker cut edge
        inner = a.filter(ImageFilter.MinFilter(edge * 2 + 1))
        rim = Image.fromarray(np.clip(np.asarray(a, np.int16) - np.asarray(inner, np.int16), 0, 255).astype(np.uint8))
        dark = Image.new("RGB", (w, h), (0, 0, 0))
        rgb = Image.composite(dark, rgb, rim.point(lambda v: v * 0.25))
    piece = rgb.convert("RGBA")
    piece.putalpha(a)
    pad = 16 if shadow else 0
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sa = Image.new("L", out.size, 0)
        sa.paste(a, (pad + 5, pad + 7))
        sa = sa.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.42))
        sh = Image.new("RGBA", out.size, (35, 20, 8, 0))
        sh.putalpha(sa)
        out = sh
    out.alpha_composite(piece, (pad, pad))
    return Sprite(out, pad)


def blit(canvas, img, x, y):
    """alpha_composite that tolerates negative / out-of-bounds positions."""
    x, y = int(round(x)), int(round(y))
    W, H = canvas.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(img.width, W - x), min(img.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    part = img if (sx0, sy0, sx1, sy1) == (0, 0, img.width, img.height) else img.crop((sx0, sy0, sx1, sy1))
    canvas.alpha_composite(part, (x + sx0, y + sy0))


def put(canvas, sp, x, y, s=1.0):
    """Place sprite so its unpadded top-left lands at (x, y)."""
    if s != 1:
        sp = sp.scaled(s)
    blit(canvas, sp.img, x - sp.pad, y - sp.pad)


def put_c(canvas, sp, cx, cy, s=1.0):
    if s != 1:
        sp = sp.scaled(s)
    blit(canvas, sp.img, cx - sp.img.width / 2, cy - sp.img.height / 2)


def put_rot(canvas, sp, pivot, at, angle, s=1.0):
    """Rotate sprite by angle (degrees, CCW) around pivot (in unpadded sprite coords) and place pivot at `at`."""
    if s != 1:
        sp = sp.scaled(s)
        pivot = (pivot[0] * s, pivot[1] * s)
    im = sp.img
    cx, cy = im.width / 2, im.height / 2
    vx, vy = pivot[0] + sp.pad - cx, pivot[1] + sp.pad - cy
    if abs(angle) > 0.05:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    th = math.radians(angle)
    rvx = vx * math.cos(th) + vy * math.sin(th)
    rvy = -vx * math.sin(th) + vy * math.cos(th)
    blit(canvas, im, at[0] - (im.width / 2 + rvx), at[1] - (im.height / 2 + rvy))


def star_pts(cx, cy, r, inner=0.45, n=5, rot=-90):
    pts = []
    for k in range(n * 2):
        rr = r if k % 2 == 0 else r * inner
        a = math.radians(rot + k * 180 / n)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def wavy_band(w, top, h_total, color, amp=14, waves=3, seed=0):
    """Polygon for a horizontal paper band whose top edge is wavy."""
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6)
    pts = [(x, top + amp * math.sin(ph + x / w * waves * 2 * math.pi) + r.normal(0, 1.5)) for x in range(-10, w + 11, 12)]
    pts += [(w + 10, h_total + 10), (-10, h_total + 10)]
    return pts
