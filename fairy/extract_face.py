"""Cut the face out of the photo and make paper cut-out variants (closed / open mouth / tilted)."""
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

SRC, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378,
        400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54,
        103, 67, 109]

img = cv2.cvtColor(cv2.imread(SRC), cv2.COLOR_BGR2RGB)
h, w = img.shape[:2]
det = vision.FaceLandmarker.create_from_options(
    vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), num_faces=5))
res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=img))
# biggest face = the hero
faces = sorted(res.face_landmarks, key=lambda f: -(max(p.x for p in f) - min(p.x for p in f)))
lm = np.array([[p.x * w, p.y * h] for p in faces[0]])

pts = lm[OVAL].copy()
center = lm[OVAL].mean(axis=0)
nose_y = lm[1][1]
# pull the upper part of the oval up/out a bit to reach the hairline
for i, (x, y) in enumerate(pts):
    if y < nose_y:
        k = 1.0 + 0.12 * (nose_y - y) / (nose_y - pts[:, 1].min())
        pts[i] = center + (pts[i] - center) * np.array([1.0 + 0.03 * (k - 1) / 0.12, k])

mask = Image.new("L", (w, h), 0)
ImageDraw.Draw(mask).polygon([tuple(p) for p in pts], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(1.5))

x0, y0 = pts.min(axis=0).astype(int) - 30
x1, y1 = pts.max(axis=0).astype(int) + 30
box = (max(x0, 0), max(y0, 0), min(x1, w), min(y1, h))
face = Image.fromarray(img).convert("RGBA")
face.putalpha(mask)
face = face.crop(box)
ox, oy = box[0], box[1]

# jaw piece: everything below the lip line
lip_y = (lm[13][1] + lm[14][1]) / 2 - oy
mouth_l, mouth_r = lm[61] - [ox, oy], lm[291] - [ox, oy]


def paper(im, border=9):
    a = im.split()[3]
    a_big = a.filter(ImageFilter.MaxFilter(border * 2 + 1))
    W, H = im.size
    pad = 30
    out = Image.new("RGBA", (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", out.size, (40, 25, 10, 0))
    sh_a = Image.new("L", out.size, 0)
    sh_a.paste(a_big, (pad + 6, pad + 8))
    shadow.putalpha(sh_a.filter(ImageFilter.GaussianBlur(6)).point(lambda v: v * 0.45))
    out = Image.alpha_composite(out, shadow)
    white = Image.new("RGBA", im.size, (250, 246, 236, 255))
    white.putalpha(a_big)
    out.alpha_composite(white, (pad, pad))
    out.alpha_composite(im, (pad, pad))
    return out


def open_mouth(im, gap=14):
    W, H = im.size
    a = np.array(im)
    jaw = a.copy()
    jaw[: int(lip_y)] = 0
    top = a.copy()
    top[int(lip_y):, :, 3] = 0
    canvas = Image.new("RGBA", (W, H + gap), (0, 0, 0, 0))
    canvas.alpha_composite(Image.fromarray(top))
    # stretch the skin row at the lip line over the gap so the outline stays closed
    row = a[int(lip_y) - 1: int(lip_y)]
    canvas.alpha_composite(Image.fromarray(np.repeat(row, gap + 2, axis=0)), (0, int(lip_y) - 1))
    # dark mouth hole
    d = ImageDraw.Draw(canvas)
    cx = (mouth_l[0] + mouth_r[0]) / 2
    hw = (mouth_r[0] - mouth_l[0]) / 2 * 0.85
    d.ellipse([cx - hw, lip_y - 4, cx + hw, lip_y + gap + 6], fill=(70, 20, 20, 255))
    canvas.alpha_composite(Image.fromarray(jaw), (0, gap))
    return canvas


closed = face
opened = open_mouth(face)
paper(closed).save(f"{OUT}/face_closed.png")
paper(opened).save(f"{OUT}/face_open.png")
paper(closed.rotate(12, resample=Image.BICUBIC, expand=True)).save(f"{OUT}/face_tilt.png")
print("face size", face.size)
