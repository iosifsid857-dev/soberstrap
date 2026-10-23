"""Цвет эффектов Roblox: взрывы и силовое поле перекрашиваются из оригинальных текстур самого Roblox.

Оригиналы берутся из APK, который Sober уже скачал, — чужих файлов в программе нет.
"""
import colorsys
import glob
import io
import os
import zipfile

import numpy as np
from PIL import Image

PARTICLES = "content/textures/particles"
EXPLOSION = ["explosion_color.dds", "explosion01_core_main.dds"]
FORCEFIELD = ["forcefield_vortex_color.dds"]

# цвет: (название, оттенок 0..1 или None для радуги)
COLORS = {
    "off": ("Как в Roblox", None),
    "blue": ("Синий (плазма)", 0.58),
    "purple": ("Фиолетовый", 0.76),
    "pink": ("Розовый", 0.9),
    "green": ("Зелёный (кислота)", 0.33),
    "cyan": ("Бирюзовый", 0.5),
    "rainbow": ("Радуга", None),
}


def apk_path(sober_data):
    found = glob.glob(f"{sober_data}/packages/*/com.roblox.client/base.apk")
    return found[0] if found else None


def original(apk, name):
    with zipfile.ZipFile(apk) as z:
        return Image.open(io.BytesIO(z.read(f"assets/{PARTICLES}/{name}"))).convert("RGBA")


def recolor(img, key):
    """Меняет оттенок, сохраняя яркость и прозрачность; у радуги оттенок идёт вдоль текстуры."""
    a = np.asarray(img, dtype=np.float32) / 255
    rgb, alpha = a[..., :3], a[..., 3:]
    hsv = np.array(np.vectorize(colorsys.rgb_to_hsv, otypes=[float, float, float])(
        rgb[..., 0], rgb[..., 1], rgb[..., 2]))
    h, s, v = hsv
    if key == "rainbow":
        h = np.broadcast_to(np.linspace(0, 0.85, img.width)[None, :], h.shape)
    else:
        h = np.full_like(h, COLORS[key][1])
    s = np.clip(s * 1.1 + 0.1 * (v > 0.2), 0, 1)
    r, g, b = np.vectorize(colorsys.hsv_to_rgb, otypes=[float, float, float])(h, s, v)
    out = np.concatenate([np.stack([r, g, b], -1), alpha], -1)
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def effect_files(sober_data, explosion, forcefield):
    """{путь внутри overlay: байты DDS}."""
    apk = apk_path(sober_data)
    if not apk:
        return {}
    files = {}
    for key, names in ((explosion, EXPLOSION), (forcefield, FORCEFIELD)):
        if key in COLORS and key != "off":
            for name in names:
                buf = io.BytesIO()
                recolor(original(apk, name), key).save(buf, "DDS")
                files[f"{PARTICLES}/{name}"] = buf.getvalue()
    return files


def preview(sober_data, key, size=64):
    apk = apk_path(sober_data)
    if not apk or key == "off":
        return None
    img = original(apk, "explosion01_core_main.dds").resize((size, size))
    return recolor(img, key)


if __name__ == "__main__":
    data = os.path.expanduser("~/.var/app/org.vinegarhq.Sober/data/sober")
    out = Image.new("RGBA", (64 * (len(COLORS) - 1), 64), (40, 40, 50, 255))
    for i, k in enumerate(k for k in COLORS if k != "off"):
        out.alpha_composite(preview(data, k), (i * 64, 0))
    out.save("/tmp/effects-preview.png")
