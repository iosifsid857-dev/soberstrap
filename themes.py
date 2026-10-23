"""Праздничные темы: все картинки рисуются кодом, чужих файлов нет.

Каждая тема — набор частей; каждая часть отдаёт {путь внутри overlay: QImage}.
Солнце и луна в Roblox рисуются сложением цветов: чёрный = прозрачный.
"""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QConicalGradient, QImage, QPainter, QPainterPath, QPen, QRadialGradient

SKY = "content/sky"
SPINNER = "content/textures/ui/LoadingScreen/LoadingSpinner.png"
GLOW = "content/textures/ui/InGameMenu"
SPARKLES = "content/textures/particles/sparkles_main.dds"
CURSORS = "content/textures/Cursors/KeyboardMouse"

THEMES = {
    "newyear": {
        "name": "Новый год",
        "main": "#e8f1ff", "accent": "#d94a4a", "second": "#4caf6a", "glow": "#7fb4ff",
        "overlay": "snow",
    },
    "halloween": {
        "name": "Хэллоуин",
        "main": "#ff8c1a", "accent": "#9b59d0", "second": "#2b1b3d", "glow": "#ff7a1a",
        "overlay": "embers",
    },
}

PARTS = {
    "cursor": "Курсор",
    "sky": "Солнце и луна",
    "menu": "Значок загрузки и меню паузы",
    "particles": "Искры (эффект Sparkles в играх)",
    "overlay": "Снег поверх игры (на Хэллоуин — угольки)",
}


def canvas(w, h=None, fill=Qt.transparent):
    img = QImage(w, h or w, QImage.Format_ARGB32)
    img.fill(fill)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    return img, p


def snowflake(p, c, r, color, width):
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    for i in range(6):
        a = math.radians(60 * i - 90)
        tip = QPointF(c.x() + r * math.cos(a), c.y() + r * math.sin(a))
        p.drawLine(c, tip)
        for k in (0.45, 0.7):  # веточки
            base = QPointF(c.x() + r * k * math.cos(a), c.y() + r * k * math.sin(a))
            for s in (-1, 1):
                b = a + s * math.radians(40)
                L = r * (0.32 if k < 0.6 else 0.22)
                p.drawLine(base, QPointF(base.x() + L * math.cos(b), base.y() + L * math.sin(b)))


def bat(p, c, size, color):
    """Силуэт летучей мыши."""
    s = size / 20
    x, y = c.x(), c.y()
    path = QPainterPath(QPointF(x, y - 2 * s))
    path.cubicTo(x + 3 * s, y - 6 * s, x + 7 * s, y - 7 * s, x + 10 * s, y - 4 * s)
    path.quadTo(x + 8 * s, y - 1 * s, x + 8 * s, y + 2 * s)
    path.quadTo(x + 6 * s, y, x + 4.5 * s, y + 2.5 * s)
    path.quadTo(x + 3 * s, y + 0.5 * s, x + 1.5 * s, y + 3 * s)
    path.lineTo(x, y + 1 * s)
    path.lineTo(x - 1.5 * s, y + 3 * s)
    path.quadTo(x - 3 * s, y + 0.5 * s, x - 4.5 * s, y + 2.5 * s)
    path.quadTo(x - 6 * s, y, x - 8 * s, y + 2 * s)
    path.quadTo(x - 8 * s, y - 1 * s, x - 10 * s, y - 4 * s)
    path.cubicTo(x - 7 * s, y - 7 * s, x - 3 * s, y - 6 * s, x, y - 2 * s)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawPath(path)


# ---------- курсор ----------

def arrow(scale):
    pts = [(0, 17), (4.2, 13), (7, 19.5), (9.6, 18.3), (6.9, 12), (12.5, 12)]
    path = QPainterPath(QPointF(32, 32))
    for x, y in pts:
        path.lineTo(32 + x * scale, 32 + y * scale)
    path.closeSubpath()
    return path


def cursor(theme, hover):
    t = THEMES[theme]
    img, p = canvas(64)
    path = arrow(1.4)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 70))
    p.drawPath(path.translated(1.2, 1.6))
    if theme == "newyear":
        # леденец: белый с красными полосками; над кнопками — зелёные полоски
        p.setBrush(QColor("#ffffff"))
        p.drawPath(path)
        p.save()
        p.setClipPath(path)
        stripe = QPen(QColor(t["second"] if hover else t["accent"]), 3.2)
        p.setPen(stripe)
        for i in range(-4, 12):
            x = 32 + i * 6
            p.drawLine(QPointF(x, 32), QPointF(x - 30, 62))
        p.restore()
        p.setPen(QPen(QColor("#5a1a1a"), 1.6))
    else:
        p.setBrush(QColor(t["accent"] if hover else t["main"]))
        p.drawPath(path)
        p.setPen(QPen(QColor("#1a0f24"), 1.6))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    p.end()
    return img


# ---------- небо ----------

def moon(theme):
    img, p = canvas(128, fill=QColor("black"))
    c = QPointF(64, 64)
    if theme == "newyear":
        g = QRadialGradient(c, 56)
        g.setColorAt(0, QColor("#ffffff"))
        g.setColorAt(0.85, QColor("#cfe0ff"))
        g.setColorAt(1, QColor("#6f8fd0"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(c, 52, 52)
        rnd = random.Random(7)
        for _ in range(9):  # мягкие «моря»
            q = QPointF(64 + rnd.uniform(-30, 30), 64 + rnd.uniform(-30, 30))
            p.setBrush(QColor(150, 175, 220, 90))
            p.drawEllipse(q, rnd.uniform(5, 12), rnd.uniform(5, 12))
        snowflake(p, QPointF(64, 64), 26, "#8fb3f0", 3)
    else:
        # тыква-луна: вырезанное лицо остаётся тёмным, то есть прозрачным
        g = QRadialGradient(QPointF(54, 50), 64)
        g.setColorAt(0, QColor("#ffd27a"))
        g.setColorAt(0.6, QColor("#ff8c1a"))
        g.setColorAt(1, QColor("#b34700"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(c, 54, 52)
        p.setBrush(QColor("black"))
        for sx in (-1, 1):
            eye = QPainterPath(QPointF(64 + sx * 26, 58))
            eye.lineTo(64 + sx * 12, 58)
            eye.lineTo(64 + sx * 19, 42)
            eye.closeSubpath()
            p.drawPath(eye)
        mouth = QPainterPath(QPointF(30, 74))
        mouth.quadTo(64, 108, 98, 74)
        for i, x in enumerate(range(90, 30, -10)):
            mouth.lineTo(x - 5, 80 + (6 if i % 2 else 0))
        mouth.closeSubpath()
        p.drawPath(mouth)
    p.end()
    return img


def sun(theme):
    img, p = canvas(128, fill=QColor("black"))
    c = QPointF(64, 64)
    inner, outer = ("#ffffff", "#7fb4ff") if theme == "newyear" else ("#fff0d0", "#d9381e")
    g = QRadialGradient(c, 62)
    g.setColorAt(0, QColor(inner))
    g.setColorAt(0.35, QColor(inner))
    g.setColorAt(0.55, QColor(outer))
    g.setColorAt(1, QColor("black"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(c, 62, 62)
    p.end()
    return img


# ---------- меню ----------

def spinner(theme):
    t = THEMES[theme]
    img, p = canvas(100)
    rect = QRectF(10, 10, 80, 80)
    g = QConicalGradient(QPointF(50, 50), 90)
    g.setColorAt(0, QColor(t["accent"]))
    g.setColorAt(0.5, QColor(t["second"] if theme == "newyear" else t["main"]))
    g.setColorAt(0.75, QColor(0, 0, 0, 0))
    g.setColorAt(1, QColor(0, 0, 0, 0))
    pen = QPen(g, 9)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.drawArc(rect, 90 * 16, 270 * 16)
    if theme == "newyear":
        snowflake(p, QPointF(50, 50), 17, t["main"], 2.6)
    else:
        bat(p, QPointF(50, 52), 30, t["main"])
    p.end()
    return img


def glow(theme, size):
    img, p = canvas(size)
    c = QPointF(size / 2, size / 2)
    g = QRadialGradient(c, size / 2)
    col = QColor(THEMES[theme]["glow"])
    g.setColorAt(0, QColor(col.red(), col.green(), col.blue(), 120))
    g.setColorAt(1, QColor(col.red(), col.green(), col.blue(), 0))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRect(0, 0, size, size)
    p.end()
    return img


# ---------- частицы ----------

def sparkle(theme):
    img, p = canvas(128)
    c = QPointF(64, 64)
    g = QRadialGradient(c, 40)
    g.setColorAt(0, QColor(255, 255, 255, 160))
    g.setColorAt(1, QColor(255, 255, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(c, 40, 40)
    if theme == "newyear":
        snowflake(p, c, 44, "#ffffff", 5)
    else:
        bat(p, c, 90, "#ffffff")  # частицы красит игра — силуэт белый
    p.end()
    return img


# ---------- сборка ----------

def theme_files(theme, parts):
    """{путь внутри overlay: QImage}; формат файла — по расширению пути."""
    files = {}
    if "cursor" in parts:
        files[f"{CURSORS}/ArrowFarCursor.png"] = cursor(theme, False)
        files[f"{CURSORS}/ArrowCursor.png"] = cursor(theme, True)
    if "sky" in parts:
        files[f"{SKY}/moon.jpg"] = moon(theme)
        files[f"{SKY}/sun.jpg"] = sun(theme)
    if "menu" in parts:
        files[SPINNER] = spinner(theme)
        files[f"{GLOW}/BackgroundGlow.png"] = glow(theme, 256)
        files[f"{GLOW}/BackgroundGlow@2x.png"] = glow(theme, 512)
    if "particles" in parts:
        files[SPARKLES] = sparkle(theme)
    return files
