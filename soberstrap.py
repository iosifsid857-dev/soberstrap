#!/usr/bin/env python3
"""SoberStrap — менеджер косметических модов и настроек для Sober (Roblox на Linux).

Моды кладутся в asset_overlay Sober: файлы оттуда Roblox берёт вместо своих.
Меняется только то, что видит и слышит сам игрок; игровой процесс не трогается.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QSlider, QTabWidget, QVBoxLayout, QWidget,
)

APP = "SoberStrap"
SOBER_ID = "org.vinegarhq.Sober"
SOBER_DATA = os.path.expanduser(f"~/.var/app/{SOBER_ID}/data/sober")
OVERLAY = f"{SOBER_DATA}/asset_overlay"
SOBER_CONFIG = os.path.expanduser(f"~/.var/app/{SOBER_ID}/config/sober/config.json")
HOME = os.path.expanduser(os.environ.get("SOBERSTRAP_HOME", "~/.local/share/soberstrap"))
STATE = f"{HOME}/state.json"
MANIFEST = f"{HOME}/applied.json"
MODS_DIR = f"{HOME}/mods"
GAMES_CACHE = f"{HOME}/games.json"
ICONS_DIR = f"{HOME}/icons"
SOBER_LOGS = f"{SOBER_DATA}/sober_logs"
HERE = os.path.dirname(os.path.realpath(__file__))
AUTOSTART = os.path.expanduser("~/.config/autostart/soberstrap-overlay.desktop")
sys.path.insert(0, HERE)
import themes  # noqa: E402 — рядом с этим файлом

CURSOR_DIR = "content/textures/Cursors/KeyboardMouse"
CURSOR_FILES = {"ArrowFarCursor.png": "normal", "ArrowCursor.png": "hover"}
FONT_TARGETS = {  # файл Roblox -> вес
    "content/fonts/BuilderSans-Regular.otf": 400,
    "content/fonts/BuilderSans-Medium.otf": 500,
    "content/fonts/BuilderSans-Bold.otf": 700,
    "content/fonts/BuilderSans-ExtraBold.otf": 800,
    "content/fonts/SourceSansPro-Light.ttf": 300,
    "content/fonts/SourceSansPro-Regular.ttf": 400,
    "content/fonts/SourceSansPro-Semibold.ttf": 600,
    "content/fonts/SourceSansPro-Bold.ttf": 700,
}

# Флаги из официального списка разрешённых (с сентября 2025 остальные Roblox игнорирует)
OUR_FLAGS = ["DFIntDebugFRMQualityLevelOverride", "FIntDebugForceMSAASamples", "DFFlagTextureQualityOverrideEnabled",
             "DFIntTextureQualityOverride", "FIntFRMMaxGrassDistance", "FIntFRMMinGrassDistance", "FFlagDebugSkyGray"]

SOBER_TOGGLES = {  # настройки самого Sober в config.json
    "discord_rpc_enabled": "Показывать игру в статусе Discord",
    "discord_rpc_show_join_button": "Кнопка «Присоединиться» в Discord для друзей",
    "server_location_indicator_enabled": "Показывать, в какой стране сервер",
    "close_on_leave": "Закрывать Roblox при выходе из игры",
    "enable_gamemode": "GameMode (система отдаёт игре больше ресурсов)",
}

DEFAULT_STATE = {
    "cursor": "off", "cursor_file": "",
    "font": "off", "font_file": "",
    "mods": {},
    "graphics_mode": "quality", "quality": 0, "msaa": 0, "textures": -1, "grass": True, "gray_sky": False,
    "theme": "off", "theme_parts": list(themes.PARTS),
}

# Tokyo Night, спокойно
COLORS = {"bg": "#1a1b26", "panel": "#24283b", "line": "#3b4261", "text": "#c0caf5", "dim": "#7a83aa",
          "accent": "#7aa2f7", "green": "#9ece6a", "red": "#f7768e"}
STYLE = f"""
QWidget {{ background: {COLORS['bg']}; color: {COLORS['text']}; font-size: 14px; }}
QTabWidget::pane {{ border: 1px solid {COLORS['line']}; border-radius: 8px; top: -1px; }}
QTabBar::tab {{ background: {COLORS['bg']}; color: {COLORS['dim']}; padding: 8px 18px; border: none; }}
QTabBar::tab:selected {{ color: {COLORS['text']}; border-bottom: 2px solid {COLORS['accent']}; }}
QGroupBox {{ background: {COLORS['panel']}; border: 1px solid {COLORS['line']}; border-radius: 8px;
            margin-top: 14px; padding: 12px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; color: {COLORS['accent']}; }}
QGroupBox QWidget {{ background: {COLORS['panel']}; }}
QLabel#hint {{ color: {COLORS['dim']}; font-size: 12px; }}
QComboBox, QPushButton {{ background: {COLORS['bg']}; border: 1px solid {COLORS['line']}; border-radius: 6px;
                         padding: 6px 10px; }}
QPushButton:hover, QComboBox:hover {{ border-color: {COLORS['accent']}; }}
QPushButton#primary {{ background: {COLORS['accent']}; color: {COLORS['bg']}; border: none; font-weight: bold; }}
QPushButton#primary:hover {{ background: #89b4fa; }}
QComboBox QAbstractItemView {{ background: {COLORS['panel']}; selection-background-color: {COLORS['line']}; }}
QSlider::groove:horizontal {{ height: 4px; background: {COLORS['line']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {COLORS['accent']}; width: 14px; margin: -6px 0; border-radius: 7px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; }}
"""


# ---------- данные ----------

def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp, path)


def read_sober_config():
    """config.json Sober начинается с //-комментариев — отделяем их и сохраняем как есть."""
    with open(SOBER_CONFIG) as f:
        text = f.read()
    head = "".join(line for line in text.splitlines(True) if line.lstrip().startswith("//"))
    body = "".join(line for line in text.splitlines(True) if not line.lstrip().startswith("//"))
    return head, json.loads(body)


def write_sober_config(head, cfg):
    shutil.copy2(SOBER_CONFIG, SOBER_CONFIG + ".soberstrap-backup")
    tmp = SOBER_CONFIG + ".tmp"
    with open(tmp, "w") as f:
        f.write(head + json.dumps(cfg, indent=4, ensure_ascii=False) + "\n")
    os.replace(tmp, SOBER_CONFIG)


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


def folder_mods():
    """Свои моды: ~/.local/share/soberstrap/mods/<имя>/content/... (+ необязательный mod.json)."""
    mods = []
    for name in sorted(os.listdir(MODS_DIR)) if os.path.isdir(MODS_DIR) else []:
        path = f"{MODS_DIR}/{name}"
        if not os.path.isdir(f"{path}/content"):
            continue
        meta = load_json(f"{path}/mod.json", {})
        mods.append({"id": name, "path": path, "name": meta.get("name", name),
                     "description": meta.get("description", "")})
    return mods


# ---------- история игр ----------

JOIN_RE = re.compile(r"Roblox: (\S+?Z),.*Joining game '([0-9a-f-]+)' place (\d+)")
TS_RE = re.compile(r"Roblox: (\d{4}-\d\d-\d\dT[\d:.]+Z),")


def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


def game_history():
    """Сессии из логов Sober: [{place, job, start, end}], новые сверху."""
    sessions = []
    for path in sorted(glob.glob(f"{SOBER_LOGS}/*.log")):
        if os.path.islink(path):
            continue
        cur, last_ts = None, None
        with open(path, errors="replace") as f:
            for line in f:
                m = TS_RE.search(line)
                if m:
                    last_ts = m.group(1)
                m = JOIN_RE.search(line)
                if m:
                    if cur:
                        sessions.append(cur)
                    cur = {"place": m.group(3), "job": m.group(2), "start": m.group(1), "end": None}
                elif cur and ("onGameLeaveBegin" in line or '"type":"game_left"' in line):
                    cur["end"] = last_ts
                    sessions.append(cur)
                    cur = None
        if cur:  # лог оборвался — считаем до последней строки
            cur["end"] = last_ts
            sessions.append(cur)
    return sessions[::-1]


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SoberStrap"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def fetch_games(places):
    """Название и иконка игр через публичное API Roblox; кэш в games.json."""
    cache = load_json(GAMES_CACHE, {})
    todo = [p for p in places if p not in cache]
    universes = {}
    for place in todo:
        try:
            universes[place] = str(http_json(f"https://apis.roblox.com/universes/v1/places/{place}/universe")["universeId"])
        except (OSError, ValueError, KeyError, TypeError):
            pass
    if universes:
        ids = ",".join(sorted(set(universes.values())))
        try:
            names = {str(g["id"]): g["name"] for g in http_json(f"https://games.roblox.com/v1/games?universeIds={ids}")["data"]}
            icons = {str(i["targetId"]): i.get("imageUrl") for i in http_json(
                f"https://thumbnails.roblox.com/v1/games/icons?universeIds={ids}&size=150x150&format=Png")["data"]}
        except (OSError, ValueError, KeyError):
            names, icons = {}, {}
        os.makedirs(ICONS_DIR, exist_ok=True)
        for place, uni in universes.items():
            icon = f"{ICONS_DIR}/{uni}.png"
            if icons.get(uni) and not os.path.exists(icon):
                try:
                    req = urllib.request.Request(icons[uni], headers={"User-Agent": "SoberStrap"})
                    with urllib.request.urlopen(req, timeout=10) as r, open(icon, "wb") as f:
                        f.write(r.read())
                except OSError:
                    pass
            if uni in names:
                cache[place] = {"universe": uni, "name": names[uni], "icon": icon if os.path.exists(icon) else ""}
        save_json(GAMES_CACHE, cache)
    return cache


# ---------- курсоры ----------

def arrow_path(scale=1.0):
    pts = [(0, 0), (0, 17), (4.2, 13), (7, 19.5), (9.6, 18.3), (6.9, 12), (12.5, 12)]
    path = QPainterPath(QPointF(32, 32))
    for x, y in pts[1:]:
        path.lineTo(32 + x * scale, 32 + y * scale)
    path.closeSubpath()
    return path


def draw_cursor(style, role):
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    fill = QColor(COLORS["accent"] if role == "hover" else "#e6e9f5")
    outline = QPen(QColor(COLORS["bg"]), 1.6)
    if style == "arrow":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawPath(arrow_path(1.4).translated(1.2, 1.6))
        p.setPen(outline)
        p.setBrush(fill)
        p.drawPath(arrow_path(1.4))
    elif style == "dot":
        p.setPen(outline)
        p.setBrush(fill)
        r = 4.5 if role == "hover" else 3.5
        p.drawEllipse(QPointF(32, 32), r, r)
    elif style == "cross":
        for color, width in ((QColor(COLORS["bg"]), 4.2), (fill, 2.0)):
            pen = QPen(color, width)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            for a, b in (((32, 22), (32, 28)), ((32, 36), (32, 42)), ((22, 32), (28, 32)), ((36, 32), (42, 32))):
                p.drawLine(QPointF(*a), QPointF(*b))
        p.setPen(Qt.NoPen)
        p.setBrush(fill)
        p.drawEllipse(QPointF(32, 32), 1.3, 1.3)
    p.end()
    return img


def custom_cursor(path):
    """Своя картинка: вписывается в 32x32, левый верхний угол картинки = кончик курсора."""
    src = QImage(path)
    if src.isNull():
        raise ValueError(f"не открывается картинка: {path}")
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.drawImage(32, 32, src.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    p.end()
    return img


CURSORS = {"off": "Стандартный", "arrow": "Аккуратная стрелка", "dot": "Точка (для шутеров)",
           "cross": "Прицел-крестик", "file": "Своя картинка…"}


# ---------- шрифты ----------

def font_families():
    out = subprocess.run(["fc-list", ":lang=ru", "family"], capture_output=True, text=True).stdout
    fams = {line.split(",")[0].strip() for line in out.splitlines() if line.strip()}
    return sorted(f for f in fams if not re.search(r"emoji|symbol|awesome|mono|math|dingbat", f, re.I))


def font_file(family, weight):
    fc_weight = {300: "light", 400: "regular", 500: "medium", 600: "semibold", 700: "bold", 800: "extrabold"}[weight]
    out = subprocess.run(["fc-match", "-f", "%{file}", f"{family}:weight={fc_weight}:slant=0"],
                         capture_output=True, text=True).stdout.strip()
    return out or None


# ---------- применение ----------

def build_files(state):
    """Что положить в overlay: {путь внутри overlay: ('image', QImage) | ('copy', файл)}."""
    files = {}
    if state["theme"] in themes.THEMES:  # своя настройка курсора ниже перекрывает курсор темы
        for rel, img in themes.theme_files(state["theme"], state["theme_parts"]).items():
            files[rel] = ("image", img)
    if state["cursor"] == "file" and state["cursor_file"]:
        img = custom_cursor(state["cursor_file"])
        for name in CURSOR_FILES:
            files[f"{CURSOR_DIR}/{name}"] = ("image", img)
    elif state["cursor"] in ("arrow", "dot", "cross"):
        for name, role in CURSOR_FILES.items():
            files[f"{CURSOR_DIR}/{name}"] = ("image", draw_cursor(state["cursor"], role))
    if state["font"] == "file" and state["font_file"]:
        for target in FONT_TARGETS:
            files[target] = ("copy", state["font_file"])
    elif state["font"] not in ("off", "file"):
        for target, weight in FONT_TARGETS.items():
            src = font_file(state["font"], weight)
            if src:
                files[target] = ("copy", src)
    for mod in folder_mods():
        if state["mods"].get(mod["id"]):
            for root, _, names in os.walk(f"{mod['path']}/content"):
                for n in names:
                    src = f"{root}/{n}"
                    files[os.path.relpath(src, mod["path"])] = ("copy", src)
    return files


def clear_overlay():
    for rel in load_json(MANIFEST, []):
        try:
            os.remove(f"{OVERLAY}/{rel}")
        except FileNotFoundError:
            pass
        d = os.path.dirname(f"{OVERLAY}/{rel}")
        while d.startswith(OVERLAY + "/"):  # убираем опустевшие папки
            try:
                os.rmdir(d)
            except OSError:
                break
            d = os.path.dirname(d)
    save_json(MANIFEST, [])


def apply_mods(state):
    clear_overlay()
    files = build_files(state)
    for rel, (kind, src) in files.items():
        dst = f"{OVERLAY}/{rel}"
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if kind == "image":
            fmt = {"jpg": "JPG", "dds": "DDS"}.get(rel.rsplit(".", 1)[-1], "PNG")
            if not src.save(dst, fmt):
                raise OSError(f"не удалось записать {dst}")
        else:
            shutil.copyfile(src, dst)
    save_json(MANIFEST, sorted(files))
    return len(files)


def apply_config(state):
    head, cfg = read_sober_config()
    cfg["graphics_optimization_mode"] = state["graphics_mode"]
    flags = {k: v for k, v in cfg.get("fflags", {}).items() if k not in OUR_FLAGS and k != "FFlagExample"}
    if state["quality"] > 0:
        flags["DFIntDebugFRMQualityLevelOverride"] = state["quality"]
    if state["msaa"] > 0:
        flags["FIntDebugForceMSAASamples"] = state["msaa"]
    if state["textures"] >= 0:
        flags["DFFlagTextureQualityOverrideEnabled"] = True
        flags["DFIntTextureQualityOverride"] = state["textures"]
    if not state["grass"]:
        flags["FIntFRMMaxGrassDistance"] = 0
        flags["FIntFRMMinGrassDistance"] = 0
    if state["gray_sky"]:
        flags["FFlagDebugSkyGray"] = True
    cfg["fflags"] = flags
    for key, value in state.get("sober", {}).items():
        if key in SOBER_TOGGLES:
            cfg[key] = value
    write_sober_config(head, cfg)


def set_overlay(state):
    """Снег поверх игры: автозапуск наблюдателя overlay.py --watch, если в теме он включён."""
    on = state["theme"] in themes.THEMES and "overlay" in state["theme_parts"]
    if not on:
        if os.path.exists(AUTOSTART):
            os.remove(AUTOSTART)
        return  # уже запущенный наблюдатель сам спрячет окно: он перечитывает state.json
    os.makedirs(os.path.dirname(AUTOSTART), exist_ok=True)
    with open(AUTOSTART, "w") as f:
        f.write("[Desktop Entry]\nType=Application\nName=SoberStrap: снег поверх Roblox\n"
                f"Exec=python3 {HERE}/overlay.py --watch\nNoDisplay=true\nX-KDE-autostart-phase=2\n")
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                if b"overlay.py\0--watch" in f.read():
                    return
        except OSError:
            pass
    subprocess.Popen([sys.executable, f"{HERE}/overlay.py", "--watch"], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------- окно ----------

class Loader(QObject):
    done = Signal(dict)


def hint(text):
    lbl = QLabel(text)
    lbl.setObjectName("hint")
    lbl.setWordWrap(True)
    return lbl


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.state = {**DEFAULT_STATE, **load_json(STATE, {})}
        self.setWindowTitle(APP)
        self.setWindowIcon(QIcon(f"{HERE}/icon.svg"))
        self.resize(620, 640)

        tabs = QTabWidget()
        tabs.addTab(self.mods_tab(), "Моды")
        tabs.addTab(self.themes_tab(), "Темы")
        tabs.addTab(self.graphics_tab(), "Графика")
        tabs.addTab(self.history_tab(), "История игр")
        tabs.addTab(self.about_tab(), "О программе")

        self.status = hint("")
        apply_btn = QPushButton("Применить")
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self.apply)
        play_btn = QPushButton("Применить и играть")
        play_btn.clicked.connect(self.apply_and_play)
        bottom = QHBoxLayout()
        bottom.addWidget(self.status, 1)
        bottom.addWidget(play_btn)
        bottom.addWidget(apply_btn)

        root = QVBoxLayout(self)
        title = QLabel(f"<span style='font-size:20px; font-weight:bold'>{APP}</span>"
                       f"<span style='color:{COLORS['dim']}'>  ·  моды для Sober</span>")
        root.addWidget(title)
        root.addWidget(tabs, 1)
        root.addLayout(bottom)

    # --- вкладки ---
    def mods_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        box = QGroupBox("Курсор")
        f = QVBoxLayout(box)
        row = QHBoxLayout()
        self.cursor_combo = QComboBox()
        for key, name in CURSORS.items():
            self.cursor_combo.addItem(name, key)
        self.cursor_combo.setCurrentIndex(max(0, self.cursor_combo.findData(self.state["cursor"])))
        self.cursor_combo.currentIndexChanged.connect(self.on_cursor)
        self.cursor_preview = QLabel()
        self.cursor_preview.setFixedSize(64, 64)
        self.cursor_preview.setStyleSheet("background: #4f6d4f; border-radius: 6px;")
        row.addWidget(self.cursor_combo, 1)
        row.addWidget(self.cursor_preview)
        f.addLayout(row)
        f.addWidget(hint("Обычный курсор и курсор над кнопками. «Своя картинка»: левый верхний угол — кончик."))
        lay.addWidget(box)

        box = QGroupBox("Шрифт интерфейса")
        f = QVBoxLayout(box)
        self.font_combo = QComboBox()
        self.font_combo.addItem("Стандартный (Builder Sans)", "off")
        for fam in font_families():
            self.font_combo.addItem(fam, fam)
        self.font_combo.addItem("Свой файл шрифта…", "file")
        self.font_combo.setCurrentIndex(max(0, self.font_combo.findData(self.state["font"])))
        self.font_combo.currentIndexChanged.connect(self.on_font)
        f.addWidget(self.font_combo)
        f.addWidget(hint("Меняет шрифт меню, чата и списка игроков. Шрифты, которые выбрал автор игры, не трогаются. "
                         "В списке только шрифты с русскими буквами."))
        lay.addWidget(box)

        box = QGroupBox("Свои моды")
        f = QVBoxLayout(box)
        self.mod_checks = {}
        mods = folder_mods()
        for mod in mods:
            cb = QCheckBox(mod["name"])
            cb.setChecked(bool(self.state["mods"].get(mod["id"])))
            self.mod_checks[mod["id"]] = cb
            f.addWidget(cb)
            if mod["description"]:
                f.addWidget(hint(mod["description"]))
        if not mods:
            f.addWidget(hint("Пока пусто. Мод — это папка с файлами в той же структуре, что и у Roblox "
                             "(content/textures/…, content/fonts/…). Положи её в папку модов и перезапусти окно."))
        btn = QPushButton("Открыть папку модов")
        btn.clicked.connect(lambda: (os.makedirs(MODS_DIR, exist_ok=True),
                                     subprocess.Popen(["xdg-open", MODS_DIR])))
        f.addWidget(btn, 0, Qt.AlignLeft)
        lay.addWidget(box)
        lay.addStretch(1)
        self.update_preview()
        return w

    def themes_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        box = QGroupBox("Тема")
        f = QVBoxLayout(box)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Без темы", "off")
        for key, t in themes.THEMES.items():
            self.theme_combo.addItem(t["name"], key)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.state["theme"])))
        self.theme_combo.currentIndexChanged.connect(self.update_theme_preview)
        f.addWidget(self.theme_combo)
        self.theme_preview = QLabel()
        self.theme_preview.setFixedHeight(96)
        f.addWidget(self.theme_preview)
        lay.addWidget(box)

        box = QGroupBox("Что менять")
        f = QVBoxLayout(box)
        self.part_checks = {}
        for key, label in themes.PARTS.items():
            cb = QCheckBox(label)
            cb.setChecked(key in self.state["theme_parts"])
            self.part_checks[key] = cb
            f.addWidget(cb)
        f.addWidget(hint("Солнце и луна меняются в играх, где автор оставил стандартные. Небо, которое игра "
                         "ставит сама, не меняется. Курсор на вкладке «Моды» важнее курсора темы."))
        f.addWidget(hint("Снег поверх игры — отдельное прозрачное окно над Roblox, клики проходят сквозь него. "
                         "Для Хэллоуина это летящие угольки. Включается сам, когда запущен Roblox."))
        lay.addWidget(box)
        lay.addStretch(1)
        self.update_theme_preview()
        return w

    def update_theme_preview(self):
        key = self.theme_combo.currentData()
        if key not in themes.THEMES:
            self.theme_preview.clear()
            return
        imgs = [themes.cursor(key, False).scaled(80, 80), themes.moon(key).scaled(80, 80),
                themes.sun(key).scaled(80, 80), themes.spinner(key).scaled(80, 80), themes.sparkle(key).scaled(80, 80)]
        pix = QPixmap(5 * 92, 92)
        pix.fill(QColor(COLORS["bg"]))
        p = QPainter(pix)
        for i, img in enumerate(imgs):
            p.drawImage(i * 92 + 6, 6, img)
        p.end()
        self.theme_preview.setPixmap(pix)

    def graphics_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        box = QGroupBox("Качество")
        form = QFormLayout(box)
        self.mode_combo = QComboBox()
        for key, name in (("quality", "Как на компьютере"), ("balanced", "Сбалансированно (как на телефоне)"),
                          ("performance", "Максимум FPS")):
            self.mode_combo.addItem(name, key)
        self.mode_combo.setCurrentIndex(max(0, self.mode_combo.findData(self.state["graphics_mode"])))
        form.addRow("Режим Sober", self.mode_combo)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 21)
        self.quality_slider.setValue(self.state["quality"])
        self.quality_label = QLabel()
        self.quality_slider.valueChanged.connect(self.on_quality)
        row = QHBoxLayout()
        row.addWidget(self.quality_slider, 1)
        row.addWidget(self.quality_label)
        form.addRow("Дальность и детали", row)
        self.on_quality(self.state["quality"])

        self.msaa_combo = QComboBox()
        for v, name in ((0, "Как решит игра"), (1, "Выкл"), (2, "2x"), (4, "4x")):
            self.msaa_combo.addItem(name, v)
        self.msaa_combo.setCurrentIndex(max(0, self.msaa_combo.findData(self.state["msaa"])))
        form.addRow("Сглаживание", self.msaa_combo)

        self.tex_combo = QComboBox()
        for v, name in ((-1, "Как решит игра"), (0, "Низкие"), (1, "Средние"), (2, "Высокие"), (3, "Максимальные")):
            self.tex_combo.addItem(name, v)
        self.tex_combo.setCurrentIndex(max(0, self.tex_combo.findData(self.state["textures"])))
        form.addRow("Текстуры", self.tex_combo)
        lay.addWidget(box)

        box = QGroupBox("Прочее")
        f = QVBoxLayout(box)
        self.grass_check = QCheckBox("Трава")
        self.grass_check.setChecked(self.state["grass"])
        self.sky_check = QCheckBox("Серое небо (меньше отвлекает)")
        self.sky_check.setChecked(self.state["gray_sky"])
        f.addWidget(self.grass_check)
        f.addWidget(self.sky_check)
        lay.addWidget(box)

        box = QGroupBox("Sober")
        f = QVBoxLayout(box)
        try:
            cfg = read_sober_config()[1]
        except (OSError, ValueError):
            cfg = {}
        self.sober_checks = {}
        for key, label in SOBER_TOGGLES.items():
            cb = QCheckBox(label)
            cb.setChecked(bool(cfg.get(key, False)))
            self.sober_checks[key] = cb
            f.addWidget(cb)
        lay.addWidget(box)
        lay.addWidget(hint("Используются только флаги из официального списка, который Roblox разрешил с сентября 2025. "
                           "Настройки качества в самой игре тоже работают — эти просто сильнее."))
        lay.addStretch(1)
        return w

    def history_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        self.history_list = QListWidget()
        self.history_list.setIconSize(QSize(48, 48))
        self.history_list.setStyleSheet(f"QListWidget {{ background: {COLORS['panel']}; border: 1px solid "
                                        f"{COLORS['line']}; border-radius: 8px; padding: 4px; }}"
                                        f"QListWidget::item {{ padding: 6px; border-radius: 6px; }}"
                                        f"QListWidget::item:selected {{ background: {COLORS['line']}; }}")
        self.history_list.itemDoubleClicked.connect(lambda _: self.play_again(False))
        lay.addWidget(self.history_list, 1)
        row = QHBoxLayout()
        for text, slot in (("Играть снова", lambda: self.play_again(False)),
                           ("На тот же сервер", lambda: self.play_again(True)),
                           ("Страница игры", self.open_page)):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(hint("Берётся из логов Sober. Названия и иконки игр подгружаются с сайта Roblox. "
                           "«На тот же сервер» сработает, только если сервер ещё жив."))
        self.sessions = game_history()
        self.games = load_json(GAMES_CACHE, {})
        self.fill_history()
        self.loader = Loader()
        self.loader.done.connect(self.on_games)
        places = sorted({s["place"] for s in self.sessions} - set(self.games))
        if places:
            threading.Thread(target=lambda: self.loader.done.emit(fetch_games(places)), daemon=True).start()
        return w

    def fill_history(self):
        self.history_list.clear()
        if not self.sessions:
            self.history_list.addItem("Пока пусто — поиграй, и здесь появятся игры.")
            return
        for s in self.sessions:
            game = self.games.get(s["place"], {})
            start = parse_ts(s["start"]).astimezone()
            text = f"{game.get('name', 'Игра ' + s['place'])}\n{start:%d.%m %H:%M}"
            if s["end"]:
                minutes = int((parse_ts(s["end"]) - parse_ts(s["start"])).total_seconds() // 60)
                text += f"  ·  {minutes // 60} ч {minutes % 60} мин" if minutes >= 60 else f"  ·  {minutes} мин"
            item = QListWidgetItem(text)
            if game.get("icon"):
                item.setIcon(QIcon(game["icon"]))
            item.setData(Qt.UserRole, s)
            self.history_list.addItem(item)

    def on_games(self, games):
        self.games = games
        self.fill_history()

    def selected_session(self):
        item = self.history_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def play_again(self, same_server):
        s = self.selected_session()
        if not s:
            return
        url = f"roblox://experiences/start?placeId={s['place']}"
        if same_server:
            url += f"&gameInstanceId={s['job']}"
        subprocess.Popen(["flatpak", "run", SOBER_ID, url], start_new_session=True)

    def open_page(self):
        s = self.selected_session()
        if s:
            subprocess.Popen(["xdg-open", f"https://www.roblox.com/games/{s['place']}"])

    def about_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel(f"<b>{APP}</b> — косметические моды для Roblox через Sober."))
        lay.addWidget(hint("Только внешний вид и удобство: курсоры, шрифты, графика. Никаких преимуществ в игре — "
                           "SoberStrap меняет файлы у тебя на компьютере, другие игроки ничего не видят. "
                           "Всё снимается кнопкой ниже."))
        lay.addSpacing(12)
        btn = QPushButton("Вернуть всё как было")
        btn.clicked.connect(self.reset)
        lay.addWidget(btn, 0, Qt.AlignLeft)
        lay.addWidget(hint(f"Моды: {OVERLAY}\nНастройки Sober: {SOBER_CONFIG}"))
        lay.addStretch(1)
        return w

    # --- обработчики ---
    def on_cursor(self):
        if self.cursor_combo.currentData() == "file":
            path, _ = QFileDialog.getOpenFileName(self, "Картинка курсора", os.path.expanduser("~"),
                                                  "Картинки (*.png *.jpg *.webp *.svg)")
            if path:
                self.state["cursor_file"] = path
            elif not self.state["cursor_file"]:
                self.cursor_combo.setCurrentIndex(0)
        self.update_preview()

    def on_font(self):
        if self.font_combo.currentData() == "file":
            path, _ = QFileDialog.getOpenFileName(self, "Файл шрифта", os.path.expanduser("~"),
                                                  "Шрифты (*.ttf *.otf)")
            if path:
                self.state["font_file"] = path
            elif not self.state["font_file"]:
                self.font_combo.setCurrentIndex(0)

    def on_quality(self, v):
        self.quality_label.setText("авто" if v == 0 else str(v))

    def update_preview(self):
        key = self.cursor_combo.currentData()
        try:
            if key == "file" and self.state["cursor_file"]:
                img = custom_cursor(self.state["cursor_file"])
            elif key in ("arrow", "dot", "cross"):
                img = draw_cursor(key, "normal")
            else:
                self.cursor_preview.clear()
                return
            self.cursor_preview.setPixmap(QPixmap.fromImage(img))
        except ValueError:
            self.cursor_preview.clear()

    def collect(self):
        s = self.state
        s["cursor"] = self.cursor_combo.currentData()
        s["font"] = self.font_combo.currentData()
        s["mods"] = {k: cb.isChecked() for k, cb in self.mod_checks.items()}
        s["graphics_mode"] = self.mode_combo.currentData()
        s["quality"] = self.quality_slider.value()
        s["msaa"] = self.msaa_combo.currentData()
        s["textures"] = self.tex_combo.currentData()
        s["grass"] = self.grass_check.isChecked()
        s["gray_sky"] = self.sky_check.isChecked()
        s["sober"] = {k: cb.isChecked() for k, cb in self.sober_checks.items()}
        s["theme"] = self.theme_combo.currentData()
        s["theme_parts"] = [k for k, cb in self.part_checks.items() if cb.isChecked()]
        return s

    def apply(self):
        if sober_running():
            QMessageBox.information(self, APP, "Roblox (Sober) сейчас запущен. Закрой его — изменения "
                                               "подхватятся только при следующем запуске.")
            return False
        try:
            state = self.collect()
            n = apply_mods(state)
            apply_config(state)
            save_json(STATE, state)
            set_overlay(state)
        except Exception as e:  # noqa: BLE001 — показываем пользователю любую ошибку
            QMessageBox.warning(self, APP, f"Не получилось применить:\n{e}")
            return False
        self.status.setText(f"Готово: файлов модов — {n}. Запусти Roblox.")
        return True

    def apply_and_play(self):
        if self.apply():
            subprocess.Popen(["flatpak", "run", SOBER_ID], start_new_session=True)
            self.close()

    def reset(self):
        if sober_running():
            QMessageBox.information(self, APP, "Сначала закрой Roblox (Sober).")
            return
        clear_overlay()
        state = {**DEFAULT_STATE, "graphics_mode": "balanced"}
        apply_config(state)
        save_json(STATE, state)
        set_overlay(state)
        QMessageBox.information(self, APP, "Всё вернул как было. Окно закроется.")
        self.close()


def main():
    if not os.path.exists(SOBER_CONFIG):
        print("Sober не найден: поставь его (flatpak install flathub org.vinegarhq.Sober) и запусти один раз.")
        sys.exit(1)
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setDesktopFileName("soberstrap")
    app.setStyleSheet(STYLE)
    win = Window()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
