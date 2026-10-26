"""All paper cut-out pieces: McDenis, armadillo, wise men, props and backgrounds."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from paper import Sprite, cut, put, put_c, put_rot, blit, star_pts, wavy_band

W, H = 1080, 1920
GROUND = 1500

# ---------- palette ----------
OCHRE = (214, 150, 62)
TERRA = (190, 92, 52)
RUST = (150, 62, 38)
RED = (178, 42, 36)
DENIM = (58, 88, 140)
DENIM_D = (40, 62, 104)
LEATHER = (120, 70, 36)
LEATHER_D = (84, 46, 22)
CREAM = (246, 236, 210)
GREEN = (92, 140, 70)
GREEN_D = (64, 104, 50)
GOLD = (232, 182, 56)
INK = (40, 26, 18)
WHITE = (250, 248, 240)


def texas_pts(x, y, w, h):
    n = [(0.25, 0), (0.42, 0), (0.42, 0.38), (0.62, 0.42), (0.8, 0.45), (1.0, 0.5), (0.98, 0.7), (0.85, 0.78),
         (0.7, 0.88), (0.62, 1.0), (0.52, 0.9), (0.45, 0.72), (0.32, 0.66), (0.2, 0.72), (0.05, 0.55), (0.0, 0.42),
         (0.25, 0.42)]
    return [(x + a * w, y + b * h) for a, b in n]


def plaid(w, h, base=(176, 36, 34), dark=(70, 16, 18), light=(230, 210, 190)):
    im = Image.new("RGBA", (w, h), base + (255,))
    d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, w, 56):
        d.rectangle([x, 0, x + 18, h], fill=dark + (130,))
        d.rectangle([x + 34, 0, x + 37, h], fill=light + (110,))
    for y in range(0, h, 56):
        d.rectangle([0, y, w, y + 18], fill=dark + (130,))
        d.rectangle([0, y + 34, w, y + 37], fill=light + (110,))
    im.putalpha(255)
    return im


def fill_pattern(layer, poly, pattern):
    m = Image.new("L", layer.size, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    layer.paste(pattern.crop((0, 0) + layer.size), (0, 0), m)


# =====================================================================
# McDenis
# =====================================================================
class Hero:
    PW, PH = 800, 1340

    def __init__(self, face_dir="face"):
        fc = Image.open(f"{face_dir}/face_closed.png").convert("RGBA")
        fo = Image.open(f"{face_dir}/face_open.png").convert("RGBA")
        s = 0.9
        fc = fc.resize((int(fc.width * s), int(fc.height * s)), Image.LANCZOS)
        fo = fo.resize((int(fo.width * s), int(fo.height * s)), Image.LANCZOS)
        self.faces = {"closed": fc, "open": fo,
                      "tilt": fc.rotate(11, resample=Image.BICUBIC, expand=True),
                      "tilt_open": fo.rotate(11, resample=Image.BICUBIC, expand=True)}
        a = np.asarray(fc)
        cy, cx = a.shape[0] // 2, a.shape[1] // 2
        patch = a[cy - 20:cy + 20, cx - 60:cx - 20, :3].reshape(-1, 3)
        self.skin = tuple(int(v) for v in np.median(patch, axis=0))
        self._build()

    def _build(self):
        skin = self.skin
        skin_d = tuple(int(v * 0.85) for v in skin)

        def hat(d, L):
            d.polygon([(120, 150), (140, 40), (175, 14), (230, 36), (285, 14), (320, 40), (340, 150)], fill=(146, 98, 52))
            d.polygon([(130, 118), (330, 118), (334, 150), (126, 150)], fill=LEATHER_D)
            d.polygon(star_pts(230, 134, 15), fill=GOLD)
            d.pieslice([0, 110, 460, 230], 180, 360, fill=(160, 108, 58))
            d.ellipse([20, 150, 440, 205], fill=(160, 108, 58))
            d.polygon([(0, 120), (30, 150), (40, 190), (6, 170)], fill=(160, 108, 58))
            d.polygon([(460, 120), (430, 150), (420, 190), (454, 170)], fill=(160, 108, 58))
            d.arc([20, 150, 440, 205], 0, 180, fill=LEATHER_D, width=4)
        self.hat = cut(460, 210, hat, edge=2)

        def torso(d, L):
            poly = [(30, 60), (70, 18), (290, 18), (330, 60), (318, 400), (42, 400)]
            fill_pattern(L, poly, plaid(360, 410))
            d.polygon([(130, 14), (180, 90), (105, 70)], fill=(120, 26, 26))
            d.polygon([(230, 14), (180, 90), (255, 70)], fill=(120, 26, 26))
            for y in range(120, 390, 60):
                d.ellipse([173, y, 187, y + 14], fill=CREAM)
            d.line([(180, 90), (180, 400)], fill=(90, 20, 20), width=3)
            d.rectangle([182, 150, 250, 210], outline=(90, 20, 20), width=3)
        self.torso = cut(360, 410, torso, edge=2)

        def neck(d, L):
            d.rectangle([0, 0, 90, 90], fill=skin_d)
        self.neck = cut(90, 90, neck, shadow=False)

        def belt(d, L):
            d.rectangle([0, 30, 300, 74], fill=LEATHER_D)
            for x in range(12, 300, 26):
                d.line([(x, 36), (x + 10, 36)], fill=(160, 110, 60), width=2)
                d.line([(x, 68), (x + 10, 68)], fill=(160, 110, 60), width=2)
            d.polygon(texas_pts(100, 0, 104, 100), fill=(180, 130, 40))
            d.polygon(texas_pts(108, 8, 88, 84), fill=GOLD)
            d.polygon(star_pts(152, 50, 16), fill=(250, 230, 150))
        self.belt = cut(300, 104, belt, edge=2)

        def leg(d, L):
            d.polygon([(0, 0), (125, 0), (118, 300), (8, 300)], fill=DENIM)
            d.line([(62, 10), (60, 296)], fill=DENIM_D, width=3)
            d.line([(10, 270), (116, 270)], fill=(200, 160, 80), width=2)
        self.leg = cut(125, 300, leg, edge=2)

        def boot(d, L):
            d.polygon([(10, 0), (110, 0), (112, 60), (170, 70), (180, 95), (10, 95)], fill=LEATHER)
            d.rectangle([10, 82, 50, 98], fill=LEATHER_D)
            d.arc([30, 10, 100, 50], 0, 180, fill=GOLD, width=3)
        bl = cut(185, 100, boot, edge=2)
        self.boot_r = bl
        self.boot_l = Sprite(bl.img.transpose(Image.FLIP_LEFT_RIGHT), bl.pad)

        def arm(d, L):
            fill_pattern(L, [(5, 0), (95, 0), (90, 270), (10, 270)], plaid(100, 340))
            d.rectangle([8, 250, 92, 275], fill=(120, 26, 26))
            d.ellipse([10, 262, 90, 340], fill=skin)
            d.ellipse([60, 270, 98, 300], fill=skin)
        self.arm = cut(100, 340, arm, edge=2)

        def banjo(d, L):
            d.rectangle([0, 52, 250, 78], fill=LEATHER)
            d.rectangle([0, 46, 40, 84], fill=LEATHER_D)
            for x in (8, 24):
                d.ellipse([x, 36, x + 10, 46], fill=CREAM)
                d.ellipse([x, 84, x + 10, 94], fill=CREAM)
            d.ellipse([230, 0, 370, 140], fill=(190, 190, 196))
            d.ellipse([242, 12, 358, 128], fill=CREAM)
            d.line([(30, 60), (330, 60)], fill=INK, width=1)
            d.line([(30, 70), (330, 70)], fill=INK, width=1)
            d.rectangle([318, 54, 330, 76], fill=INK)
        self.banjo = cut(372, 142, banjo, edge=2)

    def render(self, face="closed", arms=(0, 0), legs=(0, 0), hat_dy=0, hat_angle=0, prop=None, strum=0):
        P = Image.new("RGBA", (self.PW, self.PH), (0, 0, 0, 0))
        cx = self.PW // 2
        hip_y = 880
        # legs + boots
        for side, ang in ((-1, legs[0]), (1, legs[1])):
            lx = cx - 135 if side < 0 else cx + 10
            leg = Image.new("RGBA", (300, 460), (0, 0, 0, 0))
            put(leg, self.leg, 88, 0)
            bt = self.boot_l if side < 0 else self.boot_r
            put(leg, bt, 88 - 50 if side < 0 else 88 - 10, 285)
            put_rot(P, Sprite(leg), (150, 10), (lx + 62, hip_y + 10), ang)
        put(P, self.neck, cx - 45, 430)
        put(P, self.torso, cx - 180, 480)
        put(P, self.belt, cx - 150, 838)
        # arms (behind the banjo when holding it)
        shoulders = ((cx - 168, 525), (cx + 168, 525))
        if prop == "banjo":
            put_rot(P, self.arm, (50, 30), shoulders[0], -8 + arms[0])
            put_rot(P, self.banjo, (186, 71), (cx + 10, 720), 28)
            put_rot(P, self.arm, (50, 30), shoulders[1], 32 + strum + arms[1])
        else:
            put_rot(P, self.arm, (50, 30), shoulders[0], arms[0])
            put_rot(P, self.arm, (50, 30), shoulders[1], arms[1])
        f = self.faces[face]
        blit(P, f, cx - f.width // 2, 150 + (0 if not face.startswith("tilt") else -18))
        put_rot(P, self.hat, (230, 180), (cx, 226 + hat_dy), hat_angle)
        return P

    def head(self, face="closed"):
        """Face + hat only (for the truck window)."""
        P = Image.new("RGBA", (self.PW, 600), (0, 0, 0, 0))
        f = self.faces[face]
        blit(P, f, self.PW // 2 - f.width // 2, 150)
        put_rot(P, self.hat, (230, 180), (self.PW // 2, 226), 0)
        return P.crop((140, 60, 660, 560))


def place_puppet(canvas, P, x_center, y_feet, s=1.0, angle=0):
    """Place a hero puppet so its feet centre lands at (x_center, y_feet)."""
    sp = Sprite(P)
    put_rot(canvas, sp, (P.width / 2, 1250), (x_center, y_feet), angle, s)


# =====================================================================
# Villain & friends
# =====================================================================
def armadillo(hat=False, ribs=False):
    def body(d, L):
        d.polygon([(0, 210), (110, 168), (120, 220)], fill=(170, 140, 120))
        shell = Image.new("L", L.size, 0)
        ImageDraw.Draw(shell).ellipse([90, 40, 410, 260], fill=255)
        ImageDraw.Draw(shell).rectangle([0, 205, 520, 300], fill=0)
        stripes = Image.new("RGBA", L.size, (150, 126, 108, 255))
        sd = ImageDraw.Draw(stripes)
        for x in range(150, 380, 34):
            sd.rectangle([x, 0, x + 10, 300], fill=(112, 92, 80, 255))
        for x in range(100, 410, 20):
            for y in range(70, 200, 26):
                sd.ellipse([x, y, x + 8, y + 6], fill=(176, 152, 132, 255))
        L.paste(stripes, (0, 0), shell)
        d.rectangle([92, 196, 408, 214], fill=(120, 98, 84))
        d.polygon([(380, 110), (512, 168), (506, 190), (384, 222)], fill=(196, 160, 140))
        d.ellipse([370, 70, 408, 140], fill=(176, 140, 124))
        d.ellipse([382, 82, 400, 128], fill=(220, 160, 150))
        d.ellipse([496, 166, 516, 186], fill=INK)
        # bandit mask
        d.polygon([(388, 134), (470, 146), (468, 176), (392, 168)], fill=(20, 20, 24))
        d.polygon([(388, 140), (360, 128), (366, 150)], fill=(20, 20, 24))
        d.ellipse([418, 142, 446, 168], fill=WHITE)
        d.ellipse([430, 148, 442, 162], fill=INK)
        d.arc([440, 176, 490, 206], 200, 320, fill=INK, width=3)
        if ribs:
            d.rounded_rectangle([170, 0, 360, 62], 22, fill=(126, 58, 28))
            for x in range(190, 350, 34):
                d.line([(x, 8), (x + 20, 54)], fill=(70, 30, 12), width=6)
                d.ellipse([x - 4, 50, x + 20, 76], fill=CREAM)
        if hat:
            d.polygon([(380, 30), (390, -0 + 4), (450, 4), (460, 30)], fill=(90, 60, 30))
            d.ellipse([350, 22, 490, 52], fill=(110, 72, 36))
    b = cut(520, 300, body, edge=2)

    def legf(d, L):
        d.rounded_rectangle([0, 0, 40, 70], 14, fill=(170, 140, 124))
        d.polygon([(0, 62), (50, 62), (50, 74), (0, 74)], fill=(110, 90, 80))
    return b, cut(52, 76, legf)


def draw_armadillo(canvas, parts, x, y, t, run=0.0, s=1.0, flip=False):
    """x,y = top-left of body. run: 0 = idle, 1 = full run cycle."""
    body, leg = parts
    layer = Image.new("RGBA", (580, 380), (0, 0, 0, 0))
    bob = -abs(math.sin(t * 14)) * 14 * run
    for k, lx in enumerate((160, 210, 300, 350)):
        ang = math.sin(t * 14 + k * math.pi / 2 + (k % 2) * math.pi) * 35 * run
        put_rot(layer, leg, (26, 6), (lx + 20, 240 + bob), ang)
    put(layer, body, 20, 20 + bob)
    if flip:
        layer = layer.transpose(Image.FLIP_LEFT_RIGHT)
    if s != 1:
        layer = layer.resize((int(580 * s), int(380 * s)), Image.LANCZOS)
    blit(canvas, layer, x, y)


def tumbleweed():
    r = np.random.default_rng(5)

    def f(d, L):
        for _ in range(70):
            a0 = r.uniform(0, 360)
            rr = r.uniform(40, 140)
            cx, cy = 150 + r.normal(0, 20), 150 + r.normal(0, 20)
            d.arc([cx - rr, cy - rr * r.uniform(0.6, 1), cx + rr, cy + rr], a0, a0 + r.uniform(60, 200),
                  fill=(150 + r.integers(0, 40), 110 + r.integers(0, 30), 60), width=int(r.integers(4, 8)))
    return cut(300, 300, f, rough=0.1)


def draw_face_features(canvas, cx, cy, talk, s=1.0, mouth_w=46, eye_gap=44, look=0):
    d = ImageDraw.Draw(canvas)
    for ex in (-eye_gap, eye_gap):
        d.ellipse([cx + (ex - 22) * s, cy - 22 * s, cx + (ex + 22) * s, cy + 22 * s], fill=WHITE, outline=INK, width=3)
        d.ellipse([cx + (ex - 9 + look) * s, cy - 9 * s, cx + (ex + 9 + look) * s, cy + 9 * s], fill=INK)
    my = cy + 50 * s
    if talk:
        d.ellipse([cx - mouth_w / 2 * s, my - 12 * s, cx + mouth_w / 2 * s, my + 22 * s], fill=(90, 20, 20), outline=INK, width=3)
    else:
        d.arc([cx - mouth_w / 2 * s, my - 22 * s, cx + mouth_w / 2 * s, my + 8 * s], 20, 160, fill=INK, width=4)


def cactus():
    def f(d, L):
        g, gd = GREEN, GREEN_D
        d.rounded_rectangle([40, 210, 105, 400], 32, fill=g)
        d.rounded_rectangle([40, 335, 170, 395], 30, fill=g)
        d.rounded_rectangle([320, 290, 385, 480], 32, fill=g)
        d.rounded_rectangle([250, 420, 385, 478], 28, fill=g)
        d.rounded_rectangle([130, 60, 290, 820], 78, fill=g)
        for x in (165, 210, 255):
            d.line([(x, 110), (x, 800)], fill=gd, width=5)
        r = np.random.default_rng(2)
        for _ in range(90):
            x, y = r.uniform(140, 280), r.uniform(80, 800)
            d.line([(x, y), (x + r.choice([-9, 9]), y - 7)], fill=(240, 230, 190), width=2)
        # sheriff hat
        d.polygon([(160, 30), (170, -0 + 2), (250, 2), (260, 30)], fill=(110, 72, 36))
        d.ellipse([100, 22, 320, 70], fill=(130, 84, 42))
        # moustache
        d.ellipse([150, 220, 214, 256], fill=INK)
        d.ellipse([206, 220, 270, 256], fill=INK)
        d.polygon(star_pts(210, 390, 46), fill=GOLD)
        d.polygon(star_pts(210, 390, 30), fill=(250, 220, 110))
    return cut(420, 830, f, edge=2)


def snake():
    def f(d, L):
        body = (128, 150, 60)
        for box in ([20, 470, 420, 600], [50, 410, 390, 520], [90, 360, 350, 460]):
            d.ellipse(box, fill=body, outline=(80, 100, 36), width=3)
        pts = [(220, 400), (200, 330), (240, 270), (270, 210), (250, 160)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for k in range(12):
                x = x0 + (x1 - x0) * k / 12
                y = y0 + (y1 - y0) * k / 12
                d.ellipse([x - 42, y - 42, x + 42, y + 42], fill=body)
        for x, y in [(120, 520), (200, 540), (280, 530), (340, 520), (150, 450), (230, 470), (300, 440),
                     (180, 400), (260, 395), (215, 320), (250, 250)]:
            d.polygon([(x, y - 16), (x + 14, y), (x, y + 16), (x - 14, y)], fill=(90, 72, 30))
        d.ellipse([190, 60, 330, 170], fill=body)
        d.ellipse([214, 92, 250, 122], fill=(250, 220, 60))
        d.ellipse([272, 92, 308, 122], fill=(250, 220, 60))
        d.ellipse([228, 94, 236, 120], fill=INK)
        d.ellipse([286, 94, 294, 120], fill=INK)
        # fortune teller scarf
        d.polygon([(180, 90), (260, 10), (342, 90), (330, 70), (260, 34), (192, 72)], fill=(120, 50, 140))
        d.pieslice([184, 20, 336, 130], 180, 360, fill=(140, 60, 160))
        for x in range(196, 330, 22):
            d.ellipse([x, 70, x + 14, 84], fill=GOLD)
        d.ellipse([248, 30, 272, 54], fill=(60, 200, 210))
    return cut(440, 610, f, edge=2)


def crystal_ball():
    def f(d, L):
        d.polygon([(70, 200), (190, 200), (210, 240), (50, 240)], fill=GOLD)
        d.ellipse([30, 0, 230, 200], fill=(150, 200, 230))
        d.ellipse([70, 30, 120, 70], fill=(235, 250, 255))
    return cut(260, 245, f, rough=0.15)


def table():
    def f(d, L):
        d.polygon([(0, 0), (520, 0), (560, 300), (-0 + 0, 300)], fill=(100, 40, 120))
        for x in range(10, 520, 40):
            d.polygon([(x, 270), (x + 20, 300), (x + 40, 270)], fill=GOLD)
        d.polygon(star_pts(280, 150, 60), fill=(200, 150, 220))
    return cut(560, 300, f)


def pickup():
    def f(d, L):
        rust = (176, 52, 40)
        d.rounded_rectangle([0, 150, 770, 300], 30, fill=rust)
        d.polygon([(200, 160), (250, 30), (440, 30), (480, 160)], fill=rust)
        d.polygon([(470, 100), (760, 120), (770, 170), (470, 170)], fill=rust)
        d.rectangle([0, 100, 200, 170], fill=(150, 42, 34))
        d.rectangle([0, 96, 200, 108], fill=(120, 34, 28))
        r = np.random.default_rng(9)
        for _ in range(14):
            x, y = r.uniform(20, 740), r.uniform(160, 280)
            d.ellipse([x, y, x + r.uniform(14, 40), y + r.uniform(10, 26)], fill=(120, 66, 30))
        d.rectangle([740, 220, 786, 290], fill=(170, 170, 176))
        d.ellipse([725, 140, 765, 180], fill=(255, 230, 120))
        d.line([(480, 165), (480, 290)], fill=(110, 30, 24), width=4)
        d.rectangle([420, 190, 460, 200], fill=(170, 170, 176))
        # Texas flag sticker on the door
        d.rectangle([290, 190, 330, 260], fill=(40, 60, 140))
        d.polygon(star_pts(310, 225, 14), fill=WHITE)
        d.rectangle([330, 190, 400, 225], fill=WHITE)
        d.rectangle([330, 225, 400, 260], fill=(190, 30, 40))
        d.polygon([(258, 44), (434, 44), (452, 156), (244, 156)], fill=(0, 0, 0, 0))
    return cut(790, 310, f, edge=2)


def wheel():
    def f(d, L):
        d.ellipse([0, 0, 160, 160], fill=(30, 28, 30))
        d.ellipse([40, 40, 120, 120], fill=(180, 180, 186))
        for k in range(5):
            a = k * 2 * math.pi / 5
            x, y = 80 + 26 * math.cos(a), 80 + 26 * math.sin(a)
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(80, 80, 86))
        d.rectangle([76, 10, 84, 30], fill=(70, 70, 70))
    return cut(160, 160, f, rough=0.15)


def grill():
    def f(d, L):
        d.rectangle([210, 0, 248, 90], fill=(40, 40, 44))
        d.line([(60, 200), (20, 340)], fill=(40, 40, 44), width=12)
        d.line([(240, 200), (280, 340)], fill=(40, 40, 44), width=12)
        d.rounded_rectangle([10, 70, 290, 220], 60, fill=(32, 32, 36))
        d.line([(16, 140), (284, 140)], fill=(90, 90, 96), width=4)
        d.rectangle([120, 110, 180, 124], fill=(160, 160, 166))
        d.polygon(star_pts(70, 180, 22), fill=GOLD)
    return cut(300, 345, f, edge=2)


def smoke_puff():
    return cut(120, 100, lambda d, L: (d.ellipse([0, 20, 70, 90], fill=(236, 232, 226)),
                                        d.ellipse([40, 0, 120, 80], fill=(236, 232, 226)),
                                        d.ellipse([30, 40, 100, 100], fill=(236, 232, 226))), rough=0.2)


def ribs():
    def f(d, L):
        d.rounded_rectangle([0, 10, 200, 80], 26, fill=(126, 58, 28))
        for x in range(20, 190, 34):
            d.line([(x, 18), (x + 18, 72)], fill=(70, 30, 12), width=7)
            d.ellipse([x - 4, 66, x + 20, 92], fill=CREAM)
    return cut(204, 94, f)


def cow_head():
    def f(d, L):
        d.polygon([(30, 70), (0, 20), (50, 50)], fill=CREAM)
        d.polygon([(250, 70), (280, 20), (230, 50)], fill=CREAM)
        d.ellipse([0, 70, 70, 110], fill=(240, 240, 236))
        d.ellipse([210, 70, 280, 110], fill=(240, 240, 236))
        d.rounded_rectangle([40, 40, 240, 280], 90, fill=(248, 248, 244))
        d.ellipse([50, 60, 130, 150], fill=INK)
        d.rounded_rectangle([60, 190, 220, 290], 50, fill=(240, 170, 170))
        d.ellipse([95, 225, 115, 250], fill=(150, 80, 80))
        d.ellipse([165, 225, 185, 250], fill=(150, 80, 80))
        d.ellipse([90, 120, 112, 142], fill=WHITE)
        d.ellipse([170, 120, 192, 142], fill=INK)
    return cut(280, 295, f, edge=2)


def neighbor(shirt, hat_col, skin=(236, 196, 160), seed=0):
    def f(d, L):
        d.rectangle([60, 330, 110, 520], fill=DENIM_D)
        d.rectangle([130, 330, 180, 520], fill=DENIM_D)
        d.rounded_rectangle([40, 160, 200, 350], 40, fill=shirt)
        d.ellipse([60, 20, 180, 160], fill=skin)
        d.ellipse([90, 70, 104, 86], fill=INK)
        d.ellipse([136, 70, 150, 86], fill=INK)
        d.arc([90, 90, 150, 130], 20, 160, fill=INK, width=4)
        d.ellipse([20, 18, 220, 48], fill=hat_col)
        d.polygon([(70, 30), (80, 0), (160, 0), (170, 30)], fill=hat_col)
        d.rectangle([40, 500, 112, 530], fill=LEATHER)
        d.rectangle([128, 500, 200, 530], fill=LEATHER)
    return cut(240, 535, f, edge=2)


def banner(text, sub=None, w=960, h=300, font_main=None, font_sub=None, color=(170, 40, 32)):
    def f(d, L):
        d.polygon([(0, 30), (60, 0), (w - 60, 0), (w, 30), (w - 20, h // 2), (w, h - 30), (w - 60, h), (60, h),
                   (0, h - 30), (20, h // 2)], fill=CREAM)
        d.polygon([(14, 36), (70, 12), (w - 70, 12), (w - 14, 36), (w - 34, h // 2), (w - 14, h - 36),
                   (w - 70, h - 12), (70, h - 12), (14, h - 36), (34, h // 2)], outline=color, width=5)
        tw = d.textlength(text, font=font_main)
        ty = 40 if sub else (h - font_main.size) // 2 - 10
        d.text(((w - tw) / 2 + 3, ty + 4), text, font=font_main, fill=(60, 30, 20))
        d.text(((w - tw) / 2, ty), text, font=font_main, fill=color)
        if sub:
            sw = d.textlength(sub, font=font_sub)
            d.text(((w - sw) / 2, ty + font_main.size + 30), sub, font=font_sub, fill=INK)
    return cut(w, h, f, rough=0.2, edge=2)


# =====================================================================
# Backgrounds (static, full-frame)
# =====================================================================
def _layer_band(bg, color, top, amp=14, waves=3, seed=0, shadow=True):
    sp = cut(W, H, lambda d, L: d.polygon(wavy_band(W, top, H, color, amp, waves, seed), fill=color), shadow=shadow, rough=0.3)
    put(bg, sp, 0, 0)


def sky(colors, night=False):
    bg = Image.new("RGBA", (W, H), colors[0] + (255,))
    n = len(colors)
    for k, c in enumerate(colors[1:], 1):
        _layer_band(bg, c, int(180 + k * 900 / n), amp=18, waves=2 + k % 3, seed=k)
    return bg


def sunset_bg(with_ranch=True):
    bg = sky([(250, 214, 120), (246, 180, 96), (238, 140, 84), (220, 110, 92)])
    put_c(bg, cut(420, 420, lambda d, L: d.ellipse([0, 0, 420, 420], fill=(255, 226, 110)), rough=0.2), 540, 760)
    mesas = cut(W, 520, lambda d, L: (d.polygon([(0, 220), (80, 220), (110, 120), (300, 120), (340, 260), (520, 260),
                                                  (560, 180), (760, 180), (800, 300), (W, 300), (W, 520), (0, 520)],
                                                 fill=(170, 80, 70))), edge=2)
    put(bg, mesas, 0, 880)
    _layer_band(bg, OCHRE, 1260, amp=10, waves=2, seed=21)
    _layer_band(bg, (196, 132, 54), 1470, amp=8, waves=4, seed=22)
    if with_ranch:
        put(bg, ranch_house(), -40, 900)
        put(bg, water_tower(), 820, 690)
        put(bg, fence(), 0, 1330)
    return bg


def night_bg():
    bg = sky([(20, 24, 60), (30, 36, 84), (44, 48, 104), (60, 60, 120)])
    put(bg, cut(220, 220, lambda d, L: (d.ellipse([0, 0, 220, 220], fill=(250, 240, 200)),
                                        d.ellipse([60, -20, 260, 180], fill=(0, 0, 0, 0))), rough=0.15), 760, 180)
    r = np.random.default_rng(4)
    for _ in range(30):
        x, y, s = r.uniform(20, 1060), r.uniform(40, 900), r.uniform(8, 20)
        put_c(bg, cut(int(2 * s) + 2, int(2 * s) + 2, lambda d, L, s=s: d.polygon(star_pts(s + 1, s + 1, s), fill=(250, 240, 180)),
                      shadow=False, rough=0.05), x, y)
    _layer_band(bg, (40, 40, 70), 1150, amp=12, seed=31)
    rh = ranch_house().img
    dark = Image.new("RGBA", rh.size, (30, 24, 46, 255))
    dark.putalpha(rh.split()[3])
    blit(bg, Image.blend(rh, dark, 0.65), -40, 840)
    _layer_band(bg, (70, 56, 50), 1420, amp=8, seed=32)
    return bg


def road_layers():
    """Three wide strips (2W each) for parallax: far mesas, mid cacti, road."""
    far = Image.new("RGBA", (2 * W, H), (0, 0, 0, 0))
    m = cut(2 * W, 500, lambda d, L: d.polygon(
        [(0, 260), (200, 260), (240, 140), (520, 140), (560, 280), (900, 280), (940, 200), (1180, 200), (1220, 300),
         (1500, 300), (1540, 160), (1800, 160), (1840, 260), (2 * W, 260), (2 * W, 500), (0, 500)], fill=(176, 88, 74)), edge=2)
    put(far, m, 0, 800)
    mid = Image.new("RGBA", (2 * W, H), (0, 0, 0, 0))
    small_c = cut(120, 260, lambda d, L: (d.rounded_rectangle([40, 0, 80, 260], 20, fill=GREEN),
                                          d.rounded_rectangle([0, 80, 40, 160], 18, fill=GREEN),
                                          d.rounded_rectangle([0, 140, 60, 170], 14, fill=GREEN),
                                          d.rounded_rectangle([80, 50, 120, 130], 18, fill=GREEN),
                                          d.rounded_rectangle([60, 110, 120, 140], 14, fill=GREEN)), edge=2)
    _band = cut(2 * W, 600, lambda d, L: d.polygon(wavy_band(2 * W, 40, 600, OCHRE, 10, 6, 41), fill=OCHRE))
    put(mid, _band, 0, 1180)
    for x in (100, 520, 900, 1300, 1700, 2000):
        put(mid, small_c, x, 1000)
    road = Image.new("RGBA", (2 * W, H), (0, 0, 0, 0))
    put(road, cut(2 * W, 420, lambda d, L: d.rectangle([0, 0, 2 * W, 420], fill=(96, 86, 80))), 0, 1340)
    for x in range(0, 2 * W, 240):
        put(road, cut(120, 18, lambda d, L: d.rectangle([0, 0, 120, 18], fill=(250, 220, 90)), shadow=False), x + 40, 1500)
    return far, mid, road


def desert_bg(variant="plain"):
    bg = sky([(250, 222, 150), (246, 200, 120), (240, 176, 104)])
    put_c(bg, cut(300, 300, lambda d, L: d.ellipse([0, 0, 300, 300], fill=(255, 236, 140)), rough=0.2), 820, 360)
    far, mid, _ = road_layers()
    blit(bg, far, -300, 0)
    _layer_band(bg, OCHRE, 1250, amp=12, waves=2, seed=51)
    _layer_band(bg, (200, 136, 58), 1460, amp=8, waves=3, seed=52)
    if variant == "sheriff":
        def sign(d, L):
            d.rectangle([140, 160, 170, 520], fill=LEATHER_D)
            d.polygon([(0, 20), (300, 0), (310, 150), (10, 170)], fill=(170, 116, 64))
            d.text((40, 50), "SHERIFF", font=FONT_SIGN, fill=INK)
        put(bg, cut(320, 520, sign, edge=2), 400, 900)
    if variant == "wind":
        for k, y in enumerate((420, 560, 700, 1040)):
            put(bg, cut(420, 40, lambda d, L: d.arc([0, 0, 420, 80], 200, 340, fill=WHITE, width=10), shadow=False), 100 + k * 90, y)
    return bg


def tent_bg():
    bg = Image.new("RGBA", (W, H), (60, 24, 70, 255))
    for k, x in enumerate(range(-40, W + 80, 130)):
        col = (130, 50, 140) if k % 2 == 0 else (230, 170, 60)
        put(bg, cut(140, 1500, lambda d, L, col=col: d.polygon([(0, 0), (140, 0), (120, 1500), (20, 1500)], fill=col)), x, -40)
    put(bg, cut(W + 40, 260, lambda d, L: d.polygon(
        [(0, 0), (W + 40, 0)] + [(W + 40 - k * 90, 160 + (60 if k % 2 else 0)) for k in range(13)], fill=(100, 30, 110)),
        edge=2), -20, -10)
    r = np.random.default_rng(6)
    for _ in range(14):
        x, y = r.uniform(40, 1040), r.uniform(250, 1100)
        put_c(bg, cut(50, 50, lambda d, L: d.polygon(star_pts(25, 25, 24), fill=GOLD), shadow=False), x, y)
    _layer_band(bg, (80, 40, 50), 1420, amp=6, seed=61)
    return bg


def canyon_bg():
    bg = sky([(250, 200, 130), (244, 170, 110)])
    for k, (col, top) in enumerate([((190, 96, 60), 600), ((170, 76, 48), 820), ((150, 62, 40), 1040)]):
        put(bg, cut(420, H, lambda d, L, col=col, top=top: d.polygon(
            [(0, top), (240 - k * 30, top + 30), (300 - k * 30, top + 260), (360, top + 300), (380, H), (0, H)], fill=col),
            edge=2), 0, 0)
        put(bg, cut(560, H, lambda d, L, col=col, top=top: d.polygon(
            [(560, top - 120), (300 + k * 30, top - 90), (240 + k * 30, top + 200), (140, top + 240), (100, H), (560, H)], fill=col),
            edge=2), W - 560, 0)
    put(bg, cut(330, 420, lambda d, L: d.pieslice([0, 0, 330, 640], 180, 360, fill=(30, 20, 20))), 700, 1020)
    _layer_band(bg, (204, 120, 66), 1400, amp=8, seed=71)
    return bg


def party_bg():
    bg = sky([(40, 24, 70), (64, 36, 96), (90, 50, 110)])
    def barn(d, L):
        d.polygon([(0, 260), (330, 0), (660, 260), (660, 760), (0, 760)], fill=(160, 40, 36))
        d.polygon([(0, 260), (330, 0), (660, 260), (630, 270), (330, 40), (30, 270)], fill=WHITE)
        d.rectangle([210, 420, 450, 760], fill=(120, 28, 26))
        d.line([(210, 420), (450, 760)], fill=WHITE, width=10)
        d.line([(450, 420), (210, 760)], fill=WHITE, width=10)
        d.rectangle([280, 200, 380, 290], fill=(250, 220, 120))
    put(bg, cut(660, 760, barn, edge=2), 210, 600)
    _layer_band(bg, (110, 70, 40), 1330, amp=8, seed=81)
    _layer_band(bg, (150, 100, 56), 1480, amp=6, seed=82)
    return bg


def ranch_house():
    def f(d, L):
        d.rectangle([20, 160, 520, 470], fill=(170, 112, 66))
        for y in range(170, 470, 28):
            d.line([(20, y), (520, y)], fill=(130, 80, 44), width=3)
        d.polygon([(0, 170), (270, 20), (540, 170)], fill=(140, 40, 34))
        d.rectangle([60, 240, 160, 330], fill=(250, 220, 130))
        d.line([(110, 240), (110, 330)], fill=LEATHER_D, width=5)
        d.rectangle([330, 280, 410, 470], fill=LEATHER_D)
        d.rectangle([0, 230, 540, 250], fill=(110, 70, 40))
        for x in (10, 200, 520):
            d.rectangle([x, 240, x + 14, 470], fill=(110, 70, 40))
        d.text((210, 70), "RANCH", font=FONT_SIGN_S, fill=CREAM)
    return cut(560, 480, f, edge=2)


def water_tower():
    def f(d, L):
        for x0, x1 in ((40, 10), (200, 230)):
            d.line([(x0, 240), (x1, 600)], fill=LEATHER_D, width=10)
        d.line([(20, 420), (220, 420)], fill=LEATHER_D, width=8)
        d.rounded_rectangle([0, 60, 240, 260], 20, fill=(150, 150, 156))
        d.polygon([(0, 70), (120, 0), (240, 70)], fill=(120, 120, 126))
        d.text((44, 130), "TEXAS", font=FONT_SIGN_S, fill=(170, 40, 32))
    return cut(244, 600, f, edge=2)


def fence():
    def f(d, L):
        for x in range(0, W, 120):
            d.rectangle([x, 0, x + 18, 150], fill=(140, 92, 50))
        d.rectangle([0, 30, W, 50], fill=(150, 100, 56))
        d.rectangle([0, 90, W, 110], fill=(150, 100, 56))
    return cut(W, 150, f, edge=2)


FONT_SIGN = None
FONT_SIGN_S = None


def set_fonts(big, small):
    global FONT_SIGN, FONT_SIGN_S
    FONT_SIGN, FONT_SIGN_S = big, small


def corn():
    def f(d, L):
        d.polygon([(0, 30), (60, 0), (90, 20), (40, 40)], fill=(110, 160, 70))
        d.polygon([(0, 30), (60, 60), (90, 44), (40, 22)], fill=(90, 140, 60))
        d.ellipse([50, 6, 260, 56], fill=(246, 200, 60))
        for x in range(64, 250, 16):
            for y in (16, 30, 42):
                d.ellipse([x, y - 4, x + 10, y + 4], fill=(250, 220, 110))
    return cut(262, 62, f, edge=1)


def heart():
    def f(d, L):
        d.ellipse([0, 0, 50, 50], fill=(220, 40, 60))
        d.ellipse([40, 0, 90, 50], fill=(220, 40, 60))
        d.polygon([(4, 34), (86, 34), (45, 84)], fill=(220, 40, 60))
    return cut(90, 86, f, rough=0.15)


def thought_bubble(ribs_sp):
    def f(d, L):
        d.ellipse([60, 0, 440, 260], fill=CREAM)
        d.ellipse([20, 60, 180, 220], fill=CREAM)
        d.ellipse([320, 50, 480, 230], fill=CREAM)
        d.ellipse([10, 270, 70, 330], fill=CREAM)
        d.ellipse([-0 + 0, 340, 34, 374], fill=CREAM)
    b = cut(490, 380, f, edge=2)
    put_c(b.img, ribs_sp, b.pad + 250, b.pad + 130, 1.2)
    dd = ImageDraw.Draw(b.img)
    o = b.pad
    dd.line([(o + 140, o + 50), (o + 360, o + 210)], fill=(210, 30, 30), width=22)
    dd.line([(o + 360, o + 50), (o + 140, o + 210)], fill=(210, 30, 30), width=22)
    return b
