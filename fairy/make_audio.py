"""Voice clips (espeak-ng), banjo music and SFX -> audio/mix.wav + audio/timeline.json."""
import json
import os
import subprocess
import wave
import numpy as np
from story import VOICES, SCENES, GAP, FPS_ANIM

SR = 44100
OUT = "audio"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(3)


def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(axis=1)
    return a


def tts(i, speaker, text):
    voice, pitch, speed, filt = VOICES[speaker]
    raw, out = f"{OUT}/raw_{i:02d}.wav", f"{OUT}/line_{i:02d}.wav"
    subprocess.run(["espeak-ng", "-v", voice, "-p", str(pitch), "-s", str(speed), "-w", raw, text], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                    "-af", f"aresample={SR},{filt},silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                           "silenceremove=start_periods=1:start_threshold=-50dB,areverse",
                    "-ac", "1", out], check=True)
    return read_wav(out)


# ---------- voices + timeline ----------
timeline = {"scenes": [], "lines": []}
clips = []
t = 0.0
i = 0
for sc in SCENES:
    start = t
    t += sc["lead"]
    for speaker, spoken, sub in sc["lines"]:
        a = tts(i, speaker, spoken)
        dur = len(a) / SR
        # loudness envelope at animation rate, for mouth flaps
        hop = SR // FPS_ANIM
        env = [float(np.sqrt(np.mean(a[k:k + hop] ** 2))) for k in range(0, len(a), hop)]
        peak = max(env) or 1
        timeline["lines"].append({"scene": sc["id"], "speaker": speaker, "sub": sub, "start": t,
                                  "dur": dur, "env": [round(e / peak, 3) for e in env]})
        clips.append((t, a))
        t += dur + GAP
        i += 1
    t += sc["tail"] - GAP
    timeline["scenes"].append({"id": sc["id"], "start": start, "end": t})
TOTAL = t
timeline["total"] = TOTAL
print(f"total {TOTAL:.1f}s")


# ---------- banjo (Karplus-Strong) ----------
def pluck(freq, dur=1.4, bright=0.5, decay=0.996):
    n = int(SR * dur)
    N = int(SR / freq)
    buf = rng.uniform(-1, 1, N)
    buf = np.convolve(buf, [bright, 1 - bright], mode="same")
    out = np.zeros(n)
    out[:N] = buf
    for k in range(N, n, N):
        prev = out[k - N:k]
        nxt = decay * 0.5 * (prev + np.roll(prev, 1))
        m = min(N, n - k)
        out[k:k + m] = nxt[:m]
    # banjo twang: quick attack, a bit of metallic ring
    env = np.exp(-np.arange(n) / (SR * 0.45))
    return out * env


NOTE = {n: 440 * 2 ** (s / 12) for n, s in {
    "G2": -26, "C3": -21, "D3": -19, "G3": -14, "A3": -12, "B3": -10, "C4": -9, "D4": -7, "E4": -5,
    "F#4": -3, "G4": -2, "A4": 0, "B4": 2, "D5": 5}.items()}
cache = {}


def note(n):
    if n not in cache:
        cache[n] = pluck(NOTE[n])
    return cache[n]


CHORDS = {"G": ["G3", "B3", "D4", "G4", "B4"], "C": ["C3", "E4", "G4", "C4", "E4"],
          "D": ["D3", "A3", "D4", "F#4", "A4"]}
BASS = {"G": "G2", "C": "C3", "D": "D3"}
prog = ["G", "G", "C", "G", "G", "D", "G", "G"]
beat = 60 / 132 / 2  # eighth notes at 132 bpm
roll = [1, 2, 4, 1, 3, 4, 2, 4]  # forward-roll-ish picking pattern
music = np.zeros(int(SR * (TOTAL + 2)))
k = 0
tt = 0.0
while tt < TOTAL + 1:
    ch = prog[(k // 8) % len(prog)]
    pos = k % 8
    s = int(tt * SR)
    n = BASS[ch] if pos in (0, 4) else CHORDS[ch][roll[pos]]
    w = note(n) * (1.0 if pos in (0, 4) else 0.7)
    m = min(len(w), len(music) - s)
    music[s:s + m] += w[:m]
    k += 1
    tt += beat
music = music[: int(SR * TOTAL)]
music /= np.abs(music).max()

# ---------- voice track ----------
voice = np.zeros(int(SR * TOTAL) + SR)
for st, a in clips:
    s = int(st * SR)
    voice[s:s + len(a)] += a
voice = voice[: int(SR * TOTAL)]

# duck the music under the voice
act = np.convolve((np.abs(voice) > 0.02).astype(float), np.ones(SR // 5) / (SR // 5), mode="same")
act = np.clip(act * 4, 0, 1)
music_gain = 0.22 - 0.13 * act


# ---------- SFX ----------
def place(track, at, sig, gain=1.0):
    s = int(at * SR)
    m = min(len(sig), len(track) - s)
    if m > 0:
        track[s:s + m] += sig[:m] * gain


tsec = lambda d: np.arange(int(SR * d)) / SR


def horn():
    x = tsec(0.55)
    sq = np.sign(np.sin(2 * np.pi * 330 * x)) + 0.7 * np.sign(np.sin(2 * np.pi * 415 * x))
    env = np.minimum(1, x * 40) * np.where(x < 0.22, 1, np.where(x < 0.3, 0, 1))
    return 0.25 * sq * env * np.exp(-x * 1.5)


def moo():
    x = tsec(1.3)
    f = 155 - 45 * x / 1.3
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    saw = np.convolve(saw, np.ones(30) / 30, mode="same")
    env = np.sin(np.pi * np.minimum(1, x / 1.3)) ** 0.6
    return 0.6 * saw * env


def whoosh():
    x = tsec(0.6)
    nz = rng.normal(0, 1, len(x))
    nz = np.convolve(nz, np.ones(12) / 12, mode="same")
    return 0.5 * nz * np.sin(np.pi * x / 0.6) ** 2


def pop():
    x = tsec(0.9)
    nz = rng.normal(0, 1, len(x)) * np.exp(-x * 7)
    crackle = (rng.uniform(0, 1, len(x)) > 0.995) * rng.normal(0, 1, len(x)) * np.exp(-x * 3)
    return 0.6 * np.convolve(nz, np.ones(6) / 6, mode="same") + 0.4 * crackle


def rattle():
    x = tsec(1.0)
    return 0.25 * rng.normal(0, 1, len(x)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 28 * x))) * np.exp(-x * 1.5)


sfx = np.zeros(int(SR * TOTAL))
sc = {s["id"]: s for s in timeline["scenes"]}
for s in timeline["scenes"][1:]:
    place(sfx, s["start"] - 0.3, whoosh(), 0.5)
place(sfx, sc["ranch"]["start"] + 9.0, moo(), 0.5)
place(sfx, sc["truck"]["start"] + 0.2, horn(), 0.9)
place(sfx, sc["truck"]["end"] - 1.2, horn(), 0.7)
place(sfx, sc["snake"]["start"] + 0.2, rattle(), 0.8)
for j in range(7):
    place(sfx, sc["party"]["start"] + 1.0 + j * 1.3 + rng.uniform(0, 0.4), pop(), 0.6)
for j in range(3):
    place(sfx, sc["moral"]["end"] - 3.0 + j * 0.6, pop(), 0.5)

mix = voice + music * music_gain + sfx
fade = np.minimum(1, np.minimum(np.arange(len(mix)) / (SR * 0.5), (len(mix) - np.arange(len(mix))) / (SR * 1.5)))
mix *= fade
mix /= max(1e-6, np.abs(mix).max() / 0.92)
with wave.open(f"{OUT}/mix.wav", "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
json.dump(timeline, open(f"{OUT}/timeline.json", "w"), ensure_ascii=False)
for s in timeline["scenes"]:
    print(f"{s['id']:11s} {s['start']:6.2f} - {s['end']:6.2f}")
