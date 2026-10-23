"""Своё небо для Roblox: шесть граней куба sky512_*.tex (KTX) рисуются кодом или из своей панорамы.

Это небо по умолчанию — его видно в играх, где автор не поставил своё (Sky без картинок или без Sky).
Грани считаются через направление взгляда, поэтому стыков между ними нет.
"""
import struct

import numpy as np
from PIL import Image

SKY_DIR = "android/textures/sky"
SIZE = 1024
FACES = ("rt", "lf", "up", "dn", "ft", "bk")


def face_dirs(face, n):
    """Единичные направления для каждого пикселя грани (как у кубических карт OpenGL)."""
    t = (np.arange(n) + 0.5) / n * 2 - 1
    u, v = np.meshgrid(t, t)
    one = np.ones_like(u)
    x, y, z = {
        "rt": (one, -v, -u), "lf": (-one, -v, u),
        "up": (u, one, v), "dn": (u, -one, -v),
        "ft": (u, -v, one), "bk": (-u, -v, -one),
    }[face]
    d = np.stack([x, y, z], -1)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


# ---------- шум ----------

def _hash3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 144665) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def noise3(p, seed=0):
    """Значения шума 0..1 с плавной интерполяцией; p — (..., 3)."""
    i = np.floor(p).astype(np.int64)
    f = p - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) \
                    * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * _hash3(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def fbm(p, octaves=4, seed=0):
    total, amp, norm = 0, 1.0, 0
    for o in range(octaves):
        total = total + amp * noise3(p * (2 ** o), seed + o)
        norm += amp
        amp *= 0.5
    return total / norm


def stars(d, density, seed=1):
    """Звёзды: случайные яркие точки по направлению, размер в пикселях грани не зависит от грани."""
    cells = 420
    q = np.floor(d * cells).astype(np.int64)
    h = _hash3(q[..., 0], q[..., 1], q[..., 2], seed)
    b = _hash3(q[..., 0], q[..., 1], q[..., 2], seed + 7)
    s = np.where(h > 1 - density, 0.35 + 0.65 * b ** 3, 0.0)
    return s


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return a * (1 - t) + b * t


def col(hexstr):
    return np.array([int(hexstr[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------- готовые небеса ----------

def sky_night(d):
    h = d[..., 1]
    c = mix(np.broadcast_to(col("#1b2a4a"), d.shape), np.broadcast_to(col("#050814"), d.shape), smooth(-0.05, 0.7, h))
    band = np.exp(-((d[..., 0] * 0.6 + d[..., 1] * 0.8 - 0.2) ** 2) * 18)  # млечный путь
    c = c + band[..., None] * (fbm(d * 6, 4, 3)[..., None] * 0.18) * col("#8fa8ff")
    c = c + stars(d, 0.004 + 0.01 * band)[..., None]
    return c


def sky_aurora(d):
    c = sky_night(d) * 0.9
    h = d[..., 1]
    az = np.arctan2(d[..., 2], d[..., 0])
    wave = fbm(np.stack([np.cos(az) * 2, np.sin(az) * 2, np.zeros_like(az)], -1) * 1.5, 3, 11)
    curtain_h = 0.3 + 0.22 * wave
    curtain = smooth(curtain_h - 0.14, curtain_h + 0.02, h) * (1 - smooth(curtain_h + 0.04, curtain_h + 0.32, h))
    rays = fbm(np.stack([np.cos(az) * 30, np.sin(az) * 30, h * 0.5], -1), 2, 5)
    strength = curtain * (0.25 + 0.75 * rays) * smooth(0.05, 0.25, h)
    green, purple = col("#5dffb0"), col("#b46cff")
    tint = mix(np.broadcast_to(green, d.shape), np.broadcast_to(purple, d.shape), smooth(curtain_h, curtain_h + 0.3, h))
    return c + strength[..., None] * tint * 0.65


def sky_sunset(d):
    h = d[..., 1]
    c = mix(np.broadcast_to(col("#ff9a5a"), d.shape), np.broadcast_to(col("#ff6f91"), d.shape), smooth(-0.02, 0.18, h))
    c = mix(c, np.broadcast_to(col("#6a4c9c"), d.shape), smooth(0.15, 0.55, h))
    c = mix(c, np.broadcast_to(col("#2b2950"), d.shape), smooth(0.55, 1.0, h))
    c = mix(c, np.broadcast_to(col("#3a2a40"), d.shape), smooth(0.0, -0.3, h))
    sun = np.clip(d[..., 2], 0, 1) ** 60 * smooth(-0.1, 0.05, h)
    c = c + sun[..., None] * col("#ffd9a0") * 1.2
    clouds = smooth(0.55, 0.75, fbm(d * np.array([3, 9, 3]), 5, 21)) * smooth(0.02, 0.12, h) * (1 - smooth(0.3, 0.5, h))
    return mix(c, c * 0.6 + col("#ffb38a") * 0.4, clouds)


def sky_space(d):
    neb = fbm(d * 2.5, 5, 31)
    neb2 = fbm(d * 4 + 7, 4, 41)
    c = np.broadcast_to(col("#03030a"), d.shape).copy()
    c = c + smooth(0.5, 0.85, neb)[..., None] * col("#7a3cff") * 0.55
    c = c + smooth(0.55, 0.9, neb2)[..., None] * col("#ff4fa3") * 0.4
    c = c + smooth(0.6, 0.95, neb * neb2 * 1.6)[..., None] * col("#5ad1ff") * 0.35
    return c + stars(d, 0.012)[..., None]


def sky_pastel(d):
    h = d[..., 1]
    c = mix(np.broadcast_to(col("#ffd6e8"), d.shape), np.broadcast_to(col("#a8c8ff"), d.shape), smooth(-0.05, 0.8, h))
    clouds = smooth(0.5, 0.72, fbm(d * np.array([2.5, 6, 2.5]), 5, 51)) * smooth(-0.05, 0.25, h)
    return mix(c, np.broadcast_to(col("#ffffff"), d.shape), clouds * 0.85)


def sky_tokyo(d):
    h = d[..., 1]
    c = mix(np.broadcast_to(col("#3d59a1"), d.shape), np.broadcast_to(col("#1a1b26"), d.shape), smooth(-0.05, 0.5, h))
    c = mix(c, np.broadcast_to(col("#16161e"), d.shape), smooth(0.5, 1.0, h))
    c = mix(c, np.broadcast_to(col("#16161e"), d.shape), smooth(0.0, -0.3, h))
    glow = np.exp(-np.abs(h) * 6)
    c = c + glow[..., None] * col("#bb9af7") * 0.22
    return c + stars(d, 0.003)[..., None] * col("#c0caf5")


PRESETS = {
    "night": ("Звёздная ночь", sky_night),
    "aurora": ("Северное сияние", sky_aurora),
    "sunset": ("Закат", sky_sunset),
    "space": ("Космос", sky_space),
    "pastel": ("Пастельные облака", sky_pastel),
    "tokyo": ("Tokyo Night", sky_tokyo),
}


def panorama_fn(path):
    """Своя картинка как панорама 360° (лучше 2:1; обычное фото растянется по кругу)."""
    img = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255
    hgt, wid = img.shape[:2]

    def fn(d):
        az = np.arctan2(d[..., 0], -d[..., 2])
        el = np.arcsin(np.clip(d[..., 1], -1, 1))
        x = ((az / (2 * np.pi) + 0.5) * wid).astype(int) % wid
        y = np.clip(((0.5 - el / np.pi) * hgt).astype(int), 0, hgt - 1)
        return img[y, x]
    return fn


# ---------- запись ----------

def render_face(fn, face, n=SIZE):
    rgb = np.clip(fn(face_dirs(face, n)), 0, 1)
    return Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), "RGB")


def ktx_rgba(img):
    """KTX 1 без сжатия (RGBA8) со всеми мип-уровнями."""
    levels = []
    cur = img.convert("RGBA")
    while True:
        levels.append(cur)
        if cur.width == 1 and cur.height == 1:
            break
        cur = cur.resize((max(1, cur.width // 2), max(1, cur.height // 2)), Image.LANCZOS)
    head = b"\xabKTX 11\xbb\r\n\x1a\n" + struct.pack(
        "<13I", 0x04030201, 0x1401, 1, 0x1908, 0x8058, 0x1908, img.width, img.height, 0, 0, 1, len(levels), 0)
    body = b"".join(struct.pack("<I", lv.width * lv.height * 4) + lv.tobytes() for lv in levels)
    return head + body


def sky_files(preset, image_path=""):
    """{путь внутри overlay: байты} для всех шести граней."""
    fn = panorama_fn(image_path) if preset == "file" else PRESETS[preset][1]
    return {f"{SKY_DIR}/sky512_{face}.tex": ktx_rgba(render_face(fn, face)) for face in FACES}


def preview(preset, image_path="", w=360, h=120):
    """Развёртка неба для окна программы (горизонт посередине)."""
    fn = panorama_fn(image_path) if preset == "file" else PRESETS[preset][1]
    az = (np.arange(w) + 0.5) / w * 2 * np.pi - np.pi
    el = np.pi / 2 - (np.arange(h) + 0.5) / h * np.pi * 0.75
    az, el = np.meshgrid(az, el)
    d = np.stack([np.sin(az) * np.cos(el), np.sin(el), -np.cos(az) * np.cos(el)], -1)
    rgb = np.clip(fn(d), 0, 1)
    return Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), "RGB")
