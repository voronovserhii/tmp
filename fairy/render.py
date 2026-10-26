"""Render the paper cut-out fairy tale to output/texas_fairy_tale.mp4.

Usage: python3 render.py            -> full video
       python3 render.py --stills   -> a few key frames to output/keyframes/
"""
import json
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from paper import Sprite, cut, put, put_c, put_rot, blit, star_pts
import characters as C
from story import TRANSITION, FPS_ANIM

W, H = 1080, 1920
SLAB = "/usr/share/fonts/opentype/roboto/slab/RobotoSlab-Bold.otf"
F_SUB = ImageFont.truetype(SLAB, 50)
F_TITLE = ImageFont.truetype(SLAB, 100)
F_TITLE_S = ImageFont.truetype(SLAB, 52)
C.set_fonts(ImageFont.truetype(SLAB, 56), ImageFont.truetype(SLAB, 40))

TL = json.load(open("audio/timeline.json"))
TOTAL = TL["total"]
SCENES = TL["scenes"]
LINES = TL["lines"]

print("building pieces…", flush=True)
hero = C.Hero()
ARM = C.armadillo(ribs=True)
ARM_HAT = C.armadillo(hat=True)
TUMBLE = C.tumbleweed()
CACTUS = C.cactus()
SNAKE = C.snake()
BALL = C.crystal_ball()
TABLE = C.table()
TRUCK = C.pickup()
WHEEL = C.wheel()
GRILL = C.grill()
PUFF = C.smoke_puff()
RIBS = C.ribs()
COW = C.cow_head()
NEIGH = [C.neighbor((60, 120, 170), (200, 180, 140)), C.neighbor((220, 170, 60), (90, 60, 30)),
         C.neighbor((120, 160, 90), (240, 236, 220), skin=(170, 120, 90))]
TITLE = C.banner("McDenis Tarasis", "и Великий Броненосец", 980, 330, F_TITLE, F_TITLE_S)
THE_END = C.banner("The End, y'all!", None, 940, 230, ImageFont.truetype(SLAB, 104))
STAR_SP = {c: cut(80, 80, lambda d, L, c=c: d.polygon(star_pts(40, 40, 38), fill=c), shadow=False, rough=0.1)
           for c in [(250, 220, 90), (240, 80, 70), (90, 150, 240), (250, 250, 240)]}

print("building backgrounds…", flush=True)
BG = {
    "ranch": C.sunset_bg(True),
    "night": C.night_bg(),
    "tumbleweed": C.desert_bg("wind"),
    "cactus": C.desert_bg("sheriff"),
    "snake": C.tent_bg(),
    "canyon": C.canyon_bg(),
    "party": C.party_bg(),
    "moral": C.sunset_bg(False),
}
TRUCK_SKY = C.sky([(250, 214, 140), (246, 190, 110), (240, 160, 96)])
FAR, MID, ROAD = C.road_layers()

# subtitle strip
STRIP = cut(1020, 290, lambda d, L: d.polygon([(0, 12), (300, 0), (700, 8), (1020, 0), (1012, 280), (600, 290),
                                                (200, 282), (6, 290)], fill=(248, 240, 220)), edge=2)


def wrap(text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


_sub_cache = {}


def subtitle(canvas, line):
    key = line["sub"]
    if key not in _sub_cache:
        im = Image.new("RGBA", (980, 260), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ls = wrap(key, F_SUB, 930)
        col = (150, 30, 26) if line["speaker"] == "hero" else (50, 32, 22)
        y = (260 - len(ls) * 62) / 2
        for l in ls:
            x = (980 - F_SUB.getlength(l)) / 2
            d.text((x, y), l, font=F_SUB, fill=col)
            y += 62
        _sub_cache[key] = im
    put(canvas, STRIP, 30, 1610)
    blit(canvas, _sub_cache[key], 50, 1625)


def active_line(t):
    best = None
    for i, l in enumerate(LINES):
        end = l["start"] + l["dur"] + 0.45
        if i + 1 < len(LINES):
            end = min(end, LINES[i + 1]["start"] - 0.05)
        if l["start"] - 0.1 <= t <= end:
            best = l
    return best


def talking(speaker, t):
    for l in LINES:
        if l["speaker"] == speaker and l["start"] <= t < l["start"] + l["dur"]:
            k = int((t - l["start"]) * FPS_ANIM)
            if k < len(l["env"]):
                return l["env"][k] > 0.22
    return False


def lines_of(scene_id):
    return [l for l in LINES if l["scene"] == scene_id]


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# =====================================================================
# scenes: f(canvas, t_global, t_local, duration)
# =====================================================================
def sc_ranch(cv, T, t, d):
    cv.alpha_composite(BG["ranch"])
    # tumbleweed rolling far behind
    if 4 < t < 11:
        x = -200 + (t - 4) * 200
        put_rot(cv, TUMBLE, (150, 150), (x, 1290 - abs(math.sin(t * 5)) * 40), -t * 220, 0.4)
    if t > 8.6:
        k = ease((t - 8.6) / 0.5) - ease((t - 11.2) / 0.5)
        put_rot(cv, COW, (140, 150), (-120 + 250 * k, 1180), -12)
    sway = math.sin(t * 2.4) * 3
    P = hero.render("closed", prop="banjo", strum=math.sin(t * 16) * 9, legs=(0, -6 * abs(math.sin(t * 4.4))))
    C.place_puppet(cv, P, 640, 1560, 0.95, sway)
    if t < 3.4:
        y = 260 - 700 * ease((t - 2.6) / 0.8) + (1 - ease(t / 0.6)) * -400
        put_c(cv, TITLE, 540, y)


def sc_night(cv, T, t, d):
    cv.alpha_composite(BG["night"])
    for k, x in enumerate((640, 860)):
        put(cv, GRILL, x, 1180, 0.6)
    narr = lines_of("night")[0]
    hero_line = lines_of("night")[1]
    t_run_end = narr["start"] + narr["dur"] - SCENE_START["night"]
    if t < t_run_end + 0.5:
        p = t / (t_run_end + 0.5)
        x = -520 + p * 1700
        C.draw_armadillo(cv, ARM, x, 1180, t, run=1.0, s=0.95)
        # ribs flying off a grill
        if p < 0.55:
            put_rot(cv, RIBS, (100, 45), (690 + 40 * p, 1170 - 120 * math.sin(p * 5)), p * 300, 0.7)
    else:
        tt = t - t_run_end - 0.5
        C.draw_armadillo(cv, ARM, 1080 - 210 * ease(tt / 0.6), 1270, t, run=0.0, s=0.6, flip=True)
        talk = talking("hero", T)
        rise = ease(tt / 0.5)
        P = hero.render("tilt_open" if talk else "tilt", arms=(28, -28 + math.sin(t * 18) * 10 * talk))
        C.place_puppet(cv, P, 380, 1560 + (1 - rise) * 900, 1.0, math.sin(t * 9) * 2 * talk)


SCENE_START = {s["id"]: s["start"] for s in SCENES}


def sc_truck(cv, T, t, d):
    cv.alpha_composite(TRUCK_SKY)
    for layer, speed in ((FAR, 60), (MID, 260), (ROAD, 900)):
        off = -(t * speed) % (2 * W)
        blit(cv, layer, off - 2 * W, 0)
        blit(cv, layer, off, 0)
    x0 = 150 + 40 * math.sin(t * 0.8)
    bounce = abs(math.sin(t * 7.5)) * 16
    y0 = 1100 - bounce
    # dust confetti
    r = np.random.default_rng(int(t * FPS_ANIM))
    for k in range(18):
        age = (t * 3 + k / 18) % 1
        dx = x0 - 30 - age * 500 + r.uniform(-20, 20)
        dy = 1360 - age * 180 + math.sin(k * 7) * 50
        col = [(214, 170, 100), (190, 140, 80), (236, 200, 140)][k % 3]
        d_ = ImageDraw.Draw(cv)
        s = 18 * (1 - age) + 4
        d_.rectangle([dx, dy, dx + s, dy + s * 0.7], fill=col)
    # driver behind the window
    talk = talking("hero", T)
    head = hero.head("open" if talk else "closed")
    head = head.resize((int(head.width * 0.5), int(head.height * 0.5)), Image.LANCZOS)
    win = Image.new("RGBA", (220, 130), (70, 50, 40, 255))
    blit(win, head, 110 - head.width // 2, -78)
    blit(cv, win, x0 + 240, y0 + 50)
    put(cv, TRUCK, x0, y0)
    for wx in (170, 610):
        put_rot(cv, WHEEL, (80, 80), (x0 + wx, y0 + 300 + bounce * 0.6), -t * 900)


def sc_tumbleweed(cv, T, t, d):
    cv.alpha_composite(BG["tumbleweed"])
    P = hero.render("closed", arms=(6, -6))
    C.place_puppet(cv, P, 260, 1560, 0.75)
    tl = lines_of("tumbleweed")[1]
    t_talk = tl["start"] - SCENE_START["tumbleweed"]
    t_end = t_talk + tl["dur"]
    if t < t_talk:
        x = 1300 - 560 * ease(t / max(0.1, t_talk))
        rot = -(1300 - x) / 1.4
        y = 1240 - abs(math.sin(t * 6)) * 60
    elif t < t_end + 0.2:
        x, rot, y = 740, -400, 1240 - abs(math.sin(t * 8)) * 18
    else:
        k = t - t_end - 0.2
        x, rot, y = 740 + k * 900, -400 - k * 640, 1240 - abs(math.sin(t * 6)) * 60
    put_rot(cv, TUMBLE, (150, 150), (x, y), rot, 1.1)
    if t < t_end + 0.5:
        C.draw_face_features(cv, x, y - 20, talking("tumbleweed", T), 1.0, look=-8)


def sc_cactus(cv, T, t, d):
    cv.alpha_composite(BG["cactus"])
    P = hero.render("closed", arms=(-4, 30))
    C.place_puppet(cv, P, 260, 1560, 0.72)
    talk = talking("cactus", T)
    ang = math.sin(t * 2) * 2 + (math.sin(t * 20) * 1.5 if talk else 0)
    lay = Image.new("RGBA", (460, 880), (0, 0, 0, 0))
    put(lay, CACTUS, 20, 20)
    dr = ImageDraw.Draw(lay)
    for ex in (195, 265):
        dr.ellipse([ex - 18, 175, ex + 18, 211], fill=C.WHITE, outline=C.INK, width=3)
        dr.ellipse([ex - 15, 186, ex - 1, 202], fill=C.INK)
    if talk:
        dr.ellipse([206, 272, 254, 306], fill=(90, 20, 20), outline=C.INK, width=3)
    else:
        dr.line([(208, 286), (252, 286)], fill=C.INK, width=4)
    put_rot(cv, Sprite(lay), (230, 860), (740, 1510), ang)
    # glint on the star
    g = (t * 1.3) % 1
    if g < 0.3:
        put_c(cv, STAR_SP[(250, 250, 240)], 720 + 20, 1510 - 860 + 410 - 50, 0.3 + g)


def sc_snake(cv, T, t, d):
    cv.alpha_composite(BG["snake"])
    P = hero.render("closed", arms=(-30, 30))
    C.place_puppet(cv, P, 220, 1560, 0.7, math.sin(t * 3) * 2)
    talk = talking("snake", T)
    lay = Image.new("RGBA", (480, 660), (0, 0, 0, 0))
    put(lay, SNAKE, 20, 20)
    if int(t * 6) % 3 != 0 or talk:
        dr = ImageDraw.Draw(lay)
        L = 70 if talk else 40
        dr.line([(370, 160), (370 + L, 170)], fill=(200, 30, 40), width=6)
        dr.line([(370 + L, 170), (385 + L, 158)], fill=(200, 30, 40), width=5)
        dr.line([(370 + L, 170), (385 + L, 184)], fill=(200, 30, 40), width=5)
    put_rot(cv, Sprite(lay), (240, 620), (790, 1300), math.sin(t * 2.6) * 7, 1.2)
    put(cv, TABLE, 420, 1250)
    glow = 0.5 + 0.5 * math.sin(t * 5)
    gl = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([60, 60, 360, 360], fill=(150, 230, 255, int(90 + 90 * glow)))
    gl = gl.filter(ImageFilter.GaussianBlur(40))
    blit(cv, gl, 560 - 210, 1180 - 210)
    put_c(cv, BALL, 560, 1150)


def sc_canyon(cv, T, t, d):
    cv.alpha_composite(BG["canyon"])
    nl = lines_of("canyon")[1]
    t_out = nl["start"] - SCENE_START["canyon"] - 0.6
    # armadillo creeping out of the cave
    if t > t_out:
        k = ease((t - t_out) / 1.6)
        C.draw_armadillo(cv, ARM_HAT if False else (ARM[0], ARM[1]), 980 - 330 * k, 1240, t, run=0.6 * (k < 1), s=0.75, flip=True)
    put(cv, GRILL, 380, 1150)
    for k in range(7):
        age = (t * 0.45 + k / 7) % 1
        put_c(cv, PUFF, 540 + age * 420 + math.sin(age * 9 + k) * 30, 1150 - age * 380, 0.6 + age * 1.0)
    talk = talking("hero", T)
    P = hero.render("open" if talk else "closed", arms=(-10, 60 + math.sin(t * 6) * 12))
    C.place_puppet(cv, P, 210, 1560, 0.78)


def sc_party(cv, T, t, d):
    cv.alpha_composite(BG["party"])
    # fireworks
    r = np.random.default_rng(1)
    cols = list(STAR_SP)
    for b in range(7):
        bt = t - (1.0 + b * 1.3 + 0.2)
        if 0 < bt < 1.6:
            cx, cy = r.uniform(180, 900), r.uniform(220, 600)
            col = cols[b % len(cols)]
            for k in range(10):
                a = k * 2 * math.pi / 10
                rr = 260 * ease(bt / 0.9)
                put_c(cv, STAR_SP[col], cx + rr * math.cos(a), cy + rr * math.sin(a) + bt * 60, 0.55 * (1 - bt / 1.6) + 0.1)
        else:
            r.uniform(0, 1, 2)
    # string lights
    dr = ImageDraw.Draw(cv)
    for k in range(14):
        x = 40 + k * 76
        y = 660 + 40 * math.sin(k / 13 * math.pi)
        on = (k + int(t * 4)) % 3 != 0
        dr.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(255, 230, 120) if on else (120, 100, 60))
    dance = math.sin(t * 2 * math.pi * 132 / 120)
    b = abs(dance)
    put(cv, NEIGH[0], 40, 1080 - b * 30, 0.8)
    put(cv, NEIGH[1], 830, 1080 - (1 - b) * 30, 0.8)
    put_rot(cv, CACTUS, (210, 820), (930, 1500), dance * 6, 0.45)
    put_rot(cv, SNAKE, (220, 600), (140, 1500), -dance * 8, 0.42)
    put(cv, GRILL, 690, 1200, 0.65)
    C.draw_armadillo(cv, ARM_HAT, 560, 1270 - b * 40, t, run=0.4, s=0.6)
    put_rot(cv, TUMBLE, (150, 150), (330, 1380 - b * 70), t * 200, 0.45)
    P = hero.render("open" if talking("crowd", T) else "closed", arms=(-135 + dance * 15, 135 + dance * 15),
                    legs=(dance * 14, dance * 14), hat_dy=-b * 20)
    C.place_puppet(cv, P, 470, 1560 - b * 25, 0.8, dance * 5)


def sc_moral(cv, T, t, d):
    cv.alpha_composite(BG["moral"])
    talk = talking("narrator", T) and False
    end_t = d - 3.4
    lift = ease((t - end_t) / 0.4) - ease((t - end_t - 1.6) / 0.4)
    P = hero.render("tilt", arms=(-8, 40 + 100 * lift), hat_dy=-110 * lift, hat_angle=-14 * lift)
    C.place_puppet(cv, P, 540, 1600, 1.05, math.sin(t * 1.8) * 2)
    if t > end_t:
        k = ease((t - end_t) / 0.6)
        put_c(cv, THE_END, 540, -200 + 520 * k)
        r = np.random.default_rng(2)
        cols = list(STAR_SP)
        for j in range(26):
            x = r.uniform(0, W) + math.sin(t * 2 + j) * 30
            y = ((t - end_t) * r.uniform(220, 420) + r.uniform(-900, 0))
            if 0 < y < 1600:
                put_c(cv, STAR_SP[cols[j % 4]], x, y, 0.45)


SCENE_FN = {"ranch": sc_ranch, "night": sc_night, "truck": sc_truck, "tumbleweed": sc_tumbleweed,
            "cactus": sc_cactus, "snake": sc_snake, "canyon": sc_canyon, "party": sc_party, "moral": sc_moral}


def render_scene(idx, T):
    s = SCENES[idx]
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    SCENE_FN[s["id"]](cv, T, T - s["start"], s["end"] - s["start"])
    return cv


def frame(T):
    idx = max(i for i, s in enumerate(SCENES) if s["start"] <= T + 1e-6)
    cv = render_scene(idx, T)
    s = SCENES[idx]
    if idx > 0 and T - s["start"] < TRANSITION:
        # paper star wipe: new scene grows out of a star over the old one
        prev = render_scene(idx - 1, SCENES[idx - 1]["end"] - 0.01)
        k = ease((T - s["start"]) / TRANSITION)
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(star_pts(W / 2, H / 2 - 200, 60 + k * 2000, rot=-90 + k * 70), fill=255)
        cv = Image.composite(cv, prev, m)
    line = active_line(T)
    if line and T > 3.2:
        subtitle(cv, line)
    return cv.convert("RGB")


def main():
    os.makedirs("../output", exist_ok=True)
    if "--stills" in sys.argv:
        os.makedirs("../output/keyframes", exist_ok=True)
        picks = {"01_title": 1.5, "02_ranch": 6.0,
                 "03_night": SCENE_START["night"] + 6.8, "04_truck": SCENE_START["truck"] + 3.5,
                 "05_cactus": SCENE_START["cactus"] + 1.5, "05b_tumble": SCENE_START["tumbleweed"] + 3.0, "03b_night_run": SCENE_START["night"] + 2.5, "06_snake": SCENE_START["snake"] + 2.0,
                 "07_canyon": SCENE_START["canyon"] + 6.0, "08_party": SCENE_START["party"] + 2.2,
                 "09_end": TOTAL - 1.0}
        for name, T in picks.items():
            frame(T).save(f"../output/keyframes/{name}.png")
            print("saved", name, flush=True)
        return
    n = int(math.ceil(TOTAL * FPS_ANIM))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS_ANIM), "-i", "-", "-i", "audio/mix.wav",
                           "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                           "../output/texas_fairy_tale.mp4"], stdin=subprocess.PIPE)
    for i in range(n):
        T = i / FPS_ANIM
        im = frame(T)
        ff.stdin.write(im.tobytes())
        if i == int(SCENE_START["moral"] * FPS_ANIM) + 20:
            im.save("../output/thumbnail.png")
        if i % 60 == 0:
            print(f"frame {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("done")


if __name__ == "__main__":
    main()
