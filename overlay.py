#!/usr/bin/env python3
"""Снег (или угольки) поверх Roblox: прозрачное окно, сквозь которое проходят клики.

Roblox не трогается — это просто окно сверху, как уведомление.
  overlay.py --watch        показывать, пока запущен Sober и в теме включён снег (автозапуск)
  overlay.py --demo THEME   показать 8 секунд для проверки
"""
import json
import math
import os
import random
import sys

if os.environ.get("WAYLAND_DISPLAY"):
    # «поверх всего» и сквозные клики на Wayland у обычных окон нет — берём XWayland
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QRadialGradient
from PySide6.QtWidgets import QApplication, QWidget

HOME = os.path.expanduser(os.environ.get("SOBERSTRAP_HOME", "~/.local/share/soberstrap"))
STATE = f"{HOME}/state.json"
FPS = 30


def sober_running():
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                with open(f"/proc/{pid}/comm") as f:
                    if f.read().strip() == "sober":
                        return True
            except OSError:
                pass
    return False


def wanted_style():
    try:
        with open(STATE) as f:
            s = json.load(f)
    except (OSError, ValueError):
        return None
    if s.get("theme", "off") == "off" or "overlay" not in s.get("theme_parts", []):
        return None
    return {"newyear": "snow", "halloween": "embers"}.get(s["theme"])


class Particle:
    def __init__(self, w, h, style, anywhere):
        self.style = style
        self.depth = random.uniform(0.35, 1.0)  # дальние — меньше, медленнее, прозрачнее
        self.x = random.uniform(0, w)
        if style == "snow":
            self.y = random.uniform(-h, h) if anywhere else random.uniform(-40, -5)
            self.vy = 25 + 55 * self.depth
            self.r = 1.2 + 2.8 * self.depth
        else:
            self.y = random.uniform(0, 2 * h) if anywhere else h + random.uniform(5, 40)
            self.vy = -(18 + 40 * self.depth)
            self.r = 1.0 + 2.2 * self.depth
        self.phase = random.uniform(0, math.tau)
        self.sway = random.uniform(10, 30)


class Overlay(QWidget):
    def __init__(self):
        super().__init__(None, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                         | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.style = None
        self.parts = []
        self.t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)

    def start(self, style):
        geo = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(geo)
        self.style = style
        count = 140 if style == "snow" else 80
        self.parts = [Particle(geo.width(), geo.height(), style, True) for _ in range(count)]
        self.show()
        self.timer.start(1000 // FPS)

    def stop(self):
        self.timer.stop()
        self.hide()
        self.style = None

    def step(self):
        dt = 1 / FPS
        self.t += dt
        w, h = self.width(), self.height()
        for i, p in enumerate(self.parts):
            p.y += p.vy * dt
            if (p.style == "snow" and p.y > h + 10) or (p.style != "snow" and p.y < -10):
                self.parts[i] = Particle(w, h, p.style, False)
        self.update()

    def paintEvent(self, _):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(Qt.NoPen)
        for p in self.parts:
            x = p.x + math.sin(self.t * 0.8 + p.phase) * p.sway * p.depth
            if p.style == "snow":
                qp.setBrush(QColor(255, 255, 255, int(110 + 120 * p.depth)))
                qp.drawEllipse(QPointF(x, p.y), p.r, p.r)
            else:
                flicker = 0.6 + 0.4 * math.sin(self.t * 6 + p.phase * 3)
                g = QRadialGradient(QPointF(x, p.y), p.r * 3)
                g.setColorAt(0, QColor(255, 190, 90, int(255 * min(1, (0.3 + flicker) * p.depth))))
                g.setColorAt(0.35, QColor(255, 110, 20, int(140 * flicker * p.depth)))
                g.setColorAt(1, QColor(255, 80, 0, 0))
                qp.setBrush(g)
                qp.drawEllipse(QPointF(x, p.y), p.r * 3, p.r * 3)


def main():
    app = QApplication(sys.argv)
    ov = Overlay()
    if len(sys.argv) >= 3 and sys.argv[1] == "--demo":
        ov.start({"newyear": "snow", "halloween": "embers"}.get(sys.argv[2], sys.argv[2]))
        QTimer.singleShot(8000, app.quit)
    elif "--watch" in sys.argv:
        def check():
            style = wanted_style() if sober_running() else None
            if style != ov.style:
                ov.stop()
                if style:
                    ov.start(style)
        poll = QTimer()
        poll.timeout.connect(check)
        poll.start(3000)
        check()
    else:
        print(__doc__)
        return
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
