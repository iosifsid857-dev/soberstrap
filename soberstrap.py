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
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
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
import effects  # noqa: E402 — модули лежат рядом с этим файлом
import sky  # noqa: E402
import themes  # noqa: E402

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

MANGOHUD_DIRS = ["/var/lib/flatpak/runtime/org.freedesktop.Platform.VulkanLayer.MangoHud",
                 os.path.expanduser("~/.local/share/flatpak/runtime/org.freedesktop.Platform.VulkanLayer.MangoHud")]
HUD_STYLE = ("font_size=18,background_alpha=0.35,round_corners=8,background_color=1a1b26,text_color=c0caf5,"
             "gpu_color=7aa2f7,cpu_color=9ece6a,ram_color=bb9af7,vram_color=bb9af7,engine_color=7aa2f7")
HUD_MODES = {
    "off": ("Выключен", None),
    "fps": ("Только FPS", "fps_only"),
    "temps": ("FPS, загрузка и температура", "fps,frametime=0,gpu_stats,gpu_temp,cpu_stats,cpu_temp,ram"),
    "full": ("Подробно (с графиком кадров)", "fps,frame_timing,gpu_stats,gpu_temp,gpu_core_clock,vram,cpu_stats,"
                                             "cpu_temp,ram"),
}
HUD_POSITIONS = {"top-left": "Слева сверху", "top-right": "Справа сверху",
                 "bottom-left": "Слева снизу", "bottom-right": "Справа снизу"}

VKBASALT_DIRS = ["/var/lib/flatpak/runtime/org.freedesktop.Platform.VulkanLayer.vkBasalt",
                 os.path.expanduser("~/.local/share/flatpak/runtime/org.freedesktop.Platform.VulkanLayer.vkBasalt")]
FILTERS_OUT = os.path.normpath(f"{SOBER_DATA}/../soberstrap-filters")
FILTERS = {  # ключ: (название, описание, [(uniform, подпись, мин, макс, по умолчанию)])
    "vivid": ("Сочно", "Бледные цвета становятся живее, яркие не пересвечиваются.",
              [("VividStrength", "Сила", 0.0, 2.0, 1.0)]),
    "cinema": ("Кино", "Тёплые света, бирюзовые тени, виньетка и плёночное зерно.",
               [("CinemaStrength", "Сила", 0.0, 1.0, 1.0)]),
    "dream": ("Мечта", "Мягкое свечение вокруг ярких мест, пастельные цвета.",
              [("DreamStrength", "Сила", 0.0, 1.5, 1.0)]),
    "toon": ("Мультик", "Плоские цвета и чёрные контуры, как в мультфильме.",
             [("ToonLevels", "Ступени цвета", 3.0, 12.0, 7.0), ("ToonOutline", "Контуры", 0.0, 1.0, 1.0)]),
    "comic": ("Комикс", "Точечный растр в тенях и контуры, как в напечатанном комиксе.",
              [("ComicStrength", "Сила", 0.0, 1.0, 1.0)]),
    "pixel": ("Пиксель-арт", "Крупные пиксели и мало цветов — Roblox как игра с NES.",
              [("PixelSize", "Размер пикселя", 2.0, 12.0, 4.0), ("PixelColors", "Цветов на канал", 3.0, 16.0, 8.0)]),
    "retro": ("Ретро-телевизор", "Строки развёртки, маска кинескопа, разъезд цветов.",
              [("RetroStrength", "Сила", 0.0, 1.0, 1.0)]),
    "noir": ("Нуар", "Чёрно-белое кино с жёстким контрастом.", [("NoirStrength", "Сила", 0.0, 1.0, 1.0)]),
    "winter": ("Зима", "Холодные оттенки и иней по краям экрана.", [("WinterStrength", "Сила", 0.0, 1.0, 1.0)]),
    "halloween": ("Хэллоуин", "Оранжевые света, фиолетовые тени, тёмные края.",
                  [("HalloweenStrength", "Сила", 0.0, 1.0, 1.0)]),
}

DEFAULT_STATE = {
    "cursor": "off", "cursor_file": "",
    "font": "off", "font_file": "",
    "mods": {},
    "graphics_mode": "quality", "quality": 0, "msaa": 0, "textures": -1, "grass": True, "gray_sky": False,
    "theme": "off", "theme_parts": list(themes.PARTS),
    "hud": "off", "hud_pos": "top-left",
    "filter": "off", "filter_params": {}, "sharpen": 0.0,
    "sky": "off", "sky_file": "", "explosion": "off", "forcefield": "off",
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
QPushButton:checked {{ border: 2px solid {COLORS['accent']}; color: {COLORS['accent']}; font-weight: bold; }}
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
    theme = themes.active(state["theme"])
    state["theme_applied"] = theme
    if theme in themes.THEMES:  # своя настройка курсора ниже перекрывает курсор темы
        for rel, img in themes.theme_files(theme, state["theme_parts"]).items():
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
    if state["sky"] in sky.PRESETS or (state["sky"] == "file" and state["sky_file"]):
        for rel, data in sky.sky_files(state["sky"], state["sky_file"]).items():
            files[rel] = ("bytes", data)
    for rel, data in effects.effect_files(SOBER_DATA, state["explosion"], state["forcefield"]).items():
        files[rel] = ("bytes", data)
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
        elif kind == "bytes":
            with open(dst, "wb") as f:
                f.write(src)
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
    if state["gray_sky"] and state["sky"] == "off":  # серое небо закрыло бы своё
        flags["FFlagDebugSkyGray"] = True
    cfg["fflags"] = flags
    for key, value in state.get("sober", {}).items():
        if key in SOBER_TOGGLES:
            cfg[key] = value
    write_sober_config(head, cfg)


def mangohud_installed():
    return any(os.path.isdir(d) for d in MANGOHUD_DIRS)


def vkbasalt_installed():
    return any(os.path.isdir(d) for d in VKBASALT_DIRS)


def write_filter_config(state):
    """Шейдеры и vkBasalt.conf — в папку данных Sober: из песочницы виден только её собственный каталог."""
    shutil.rmtree(FILTERS_OUT, ignore_errors=True)
    shutil.copytree(f"{HERE}/filters", FILTERS_OUT)
    effects, lines = [], []
    if state["sharpen"] > 0:
        effects.append("cas")
        lines.append(f"casSharpness = {state['sharpen']:.2f}")
    key = state["filter"]
    if key in FILTERS:
        effects.append(key)
        lines.append(f"{key} = {FILTERS_OUT}/{key}.fx")
        for uniform, _, lo, hi, default in FILTERS[key][2]:
            value = state["filter_params"].get(uniform, default)
            lines.append(f"{uniform} = {min(hi, max(lo, value)):g}")
    lines += [f"reshadeIncludePath = {FILTERS_OUT}", f"reshadeTexturePath = {FILTERS_OUT}"]
    with open(f"{FILTERS_OUT}/vkBasalt.conf", "w") as f:
        f.write(f"effects = {':'.join(effects)}\n" + "\n".join(lines) + "\n")
    return bool(effects)


def apply_env(state):
    """Счётчик FPS (MangoHud) и фильтры (vkBasalt) — переменные окружения Sober через flatpak override --user."""
    args = []
    opts = HUD_MODES.get(state["hud"], HUD_MODES["off"])[1]
    if opts and mangohud_installed():
        args += ["--env=MANGOHUD=1", f"--env=MANGOHUD_CONFIG={opts},position={state['hud_pos']},{HUD_STYLE}"]
    else:
        args += ["--unset-env=MANGOHUD", "--unset-env=MANGOHUD_CONFIG"]
    if vkbasalt_installed() and write_filter_config(state):
        args += ["--env=ENABLE_VKBASALT=1", f"--env=VKBASALT_CONFIG_FILE={FILTERS_OUT}/vkBasalt.conf"]
    else:
        args += ["--unset-env=ENABLE_VKBASALT", "--unset-env=VKBASALT_CONFIG_FILE"]
    subprocess.run(["flatpak", "override", "--user", *args, SOBER_ID], check=True, capture_output=True)


def set_overlay(state):
    """Наблюдатель overlay.py --watch в автозапуске: снег поверх игры и смена темы «по дате»."""
    on = state["theme"] == "auto" or (state["theme"] in themes.THEMES and "overlay" in state["theme_parts"])
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
        self.resize(780, 700)

        tabs = QTabWidget()
        tabs.addTab(self.mods_tab(), "Моды")
        tabs.addTab(self.themes_tab(), "Темы")
        tabs.addTab(self.world_tab(), "Небо и эффекты")
        tabs.addTab(self.filters_tab(), "Фильтры")
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

    def world_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        box = QGroupBox("Небо (экспериментально)")
        f = QVBoxLayout(box)
        self.sky_combo = QComboBox()
        self.sky_combo.addItem("Как в Roblox", "off")
        for key, (name, _) in sky.PRESETS.items():
            self.sky_combo.addItem(name, key)
        self.sky_combo.addItem("Своя панорама…", "file")
        self.sky_combo.setCurrentIndex(max(0, self.sky_combo.findData(self.state["sky"])))
        self.sky_combo.currentIndexChanged.connect(self.on_sky)
        f.addWidget(self.sky_combo)
        self.sky_preview = QLabel()
        self.sky_preview.setFixedHeight(130)
        f.addWidget(self.sky_preview)
        f.addWidget(hint("Меняется небо по умолчанию: его видно в играх, где автор не поставил своё. "
                         "Своя картинка лучше всего — панорама 360° (ширина в 2 раза больше высоты). "
                         "Своё небо отключает «серое небо». Пока не подтверждено, что Roblox принимает этот формат."))
        lay.addWidget(box)

        box = QGroupBox("Цвет эффектов")
        form = QFormLayout(box)
        self.expl_combo = QComboBox()
        self.ff_combo = QComboBox()
        for combo, key in ((self.expl_combo, "explosion"), (self.ff_combo, "forcefield")):
            for k, (name, _) in effects.COLORS.items():
                combo.addItem(name, k)
            combo.setCurrentIndex(max(0, combo.findData(self.state[key])))
        self.expl_combo.currentIndexChanged.connect(self.update_expl_preview)
        self.expl_preview = QLabel()
        self.expl_preview.setFixedSize(64, 64)
        row = QHBoxLayout()
        row.addWidget(self.expl_combo, 1)
        row.addWidget(self.expl_preview)
        form.addRow("Взрывы", row)
        form.addRow("Силовое поле", self.ff_combo)
        form.addRow(hint("Перекрашиваются стандартные взрывы и силовое поле Roblox. "
                         "Если игра рисует свои эффекты, они останутся как есть."))
        lay.addWidget(box)
        lay.addStretch(1)
        self.update_sky_preview()
        self.update_expl_preview()
        return w

    def on_sky(self):
        if self.sky_combo.currentData() == "file":
            path, _ = QFileDialog.getOpenFileName(self, "Панорама неба", os.path.expanduser("~"),
                                                  "Картинки (*.png *.jpg *.jpeg *.webp)")
            if path:
                self.state["sky_file"] = path
            elif not self.state["sky_file"]:
                self.sky_combo.setCurrentIndex(0)
        self.update_sky_preview()

    def update_sky_preview(self):
        key = self.sky_combo.currentData()
        if key == "off" or (key == "file" and not self.state["sky_file"]):
            self.sky_preview.clear()
            return
        try:
            img = sky.preview(key, self.state["sky_file"], 540, 130)
        except OSError:
            self.sky_preview.clear()
            return
        self.sky_preview.setPixmap(QPixmap.fromImage(QImage(img.tobytes(), img.width, img.height,
                                                            img.width * 3, QImage.Format_RGB888).copy()))

    def update_expl_preview(self):
        img = effects.preview(SOBER_DATA, self.expl_combo.currentData())
        if img is None:
            self.expl_preview.clear()
            return
        self.expl_preview.setPixmap(QPixmap.fromImage(QImage(img.tobytes(), img.width, img.height,
                                                             img.width * 4, QImage.Format_RGBA8888).copy()))

    def themes_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        box = QGroupBox("Тема")
        f = QVBoxLayout(box)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Без темы", "off")
        self.theme_combo.addItem("Сама по дате (Хэллоуин, Новый год)", "auto")
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
        key = themes.active(self.theme_combo.currentData())
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

    def filters_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        if not vkbasalt_installed():
            lay.addWidget(hint("Для фильтров нужно расширение vkBasalt для Flatpak (см. README: "
                               "scripts/build-vkbasalt-ext.sh)."))
        self.filter_key = self.state["filter"]
        self.filter_buttons = {}
        grid = QGridLayout()
        for i, (key, (name, desc, _)) in enumerate([("off", ("Без фильтра", "Как задумал Roblox.", []))]
                                                   + list(FILTERS.items())):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setToolTip(desc)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda _=False, k=key: self.pick_filter(k))
            self.filter_buttons[key] = btn
            grid.addWidget(btn, i // 3, i % 3)
        lay.addLayout(grid)
        self.filter_desc = hint("")
        lay.addWidget(self.filter_desc)

        self.param_box = QGroupBox("Настройка")
        self.param_form = QFormLayout(self.param_box)
        self.param_sliders = {}
        lay.addWidget(self.param_box)

        box = QGroupBox("Чёткость")
        form = QFormLayout(box)
        self.sharpen_slider = QSlider(Qt.Horizontal)
        self.sharpen_slider.setRange(0, 100)
        self.sharpen_slider.setValue(int(self.state["sharpen"] * 100))
        form.addRow("Резкость (AMD CAS)", self.sharpen_slider)
        form.addRow(hint("Работает с любым фильтром и без него: картинка чётче, особенно при сглаживании."))
        lay.addWidget(box)
        lay.addWidget(hint("Фильтры рисуются поверх готового кадра (vkBasalt, как ReShade на Windows). "
                           "Другие игроки их не видят, игра не меняется. Меняются после перезапуска Roblox."))
        lay.addStretch(1)
        self.pick_filter(self.filter_key if self.filter_key in FILTERS else "off")
        return w

    def pick_filter(self, key):
        self.filter_key = key
        for k, btn in self.filter_buttons.items():
            btn.setChecked(k == key)
        self.filter_desc.setText(FILTERS[key][1] if key in FILTERS else "Без фильтра — как задумал Roblox.")
        while self.param_form.rowCount():
            self.param_form.removeRow(0)
        self.param_sliders = {}
        params = FILTERS[key][2] if key in FILTERS else []
        for uniform, label, lo, hi, default in params:
            sl = QSlider(Qt.Horizontal)
            sl.setRange(int(lo * 100), int(hi * 100))
            sl.setValue(int(self.state["filter_params"].get(uniform, default) * 100))
            self.param_sliders[uniform] = sl
            self.param_form.addRow(label, sl)
        self.param_box.setVisible(bool(params))

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

        box = QGroupBox("Счётчик FPS")
        form = QFormLayout(box)
        self.hud_combo = QComboBox()
        for key, (name, _) in HUD_MODES.items():
            self.hud_combo.addItem(name, key)
        self.hud_combo.setCurrentIndex(max(0, self.hud_combo.findData(self.state["hud"])))
        self.hud_pos_combo = QComboBox()
        for key, name in HUD_POSITIONS.items():
            self.hud_pos_combo.addItem(name, key)
        self.hud_pos_combo.setCurrentIndex(max(0, self.hud_pos_combo.findData(self.state["hud_pos"])))
        form.addRow("Показывать", self.hud_combo)
        form.addRow("Где", self.hud_pos_combo)
        form.addRow(hint("MangoHud. В игре прячется и показывается клавишами правый Shift + F12."
                         if mangohud_installed() else
                         "Нужен MangoHud: flatpak install flathub "
                         "runtime/org.freedesktop.Platform.VulkanLayer.MangoHud/x86_64/26.08"))
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
        s["filter"] = self.filter_key
        s["filter_params"] = {**s["filter_params"], **{u: sl.value() / 100 for u, sl in self.param_sliders.items()}}
        s["sharpen"] = self.sharpen_slider.value() / 100
        s["hud"] = self.hud_combo.currentData()
        s["hud_pos"] = self.hud_pos_combo.currentData()
        s["sky"] = self.sky_combo.currentData()
        s["explosion"] = self.expl_combo.currentData()
        s["forcefield"] = self.ff_combo.currentData()
        s["theme"] = self.theme_combo.currentData()
        s["theme_parts"] = [k for k, cb in self.part_checks.items() if cb.isChecked()]
        return s

    def apply(self):
        if sober_running():
            QMessageBox.information(self, APP, "Roblox (Sober) сейчас запущен. Закрой его — изменения "
                                               "подхватятся только при следующем запуске.")
            return False
        self.status.setText("Применяю… (своё небо рисуется секунд 15)")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            state = self.collect()
            n = apply_mods(state)
            apply_config(state)
            apply_env(state)
            save_json(STATE, state)
            set_overlay(state)
        except Exception as e:  # noqa: BLE001 — показываем пользователю любую ошибку
            QApplication.restoreOverrideCursor()
            self.status.setText("")
            QMessageBox.warning(self, APP, f"Не получилось применить:\n{e}")
            return False
        QApplication.restoreOverrideCursor()
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
        apply_env(state)
        save_json(STATE, state)
        set_overlay(state)
        QMessageBox.information(self, APP, "Всё вернул как было. Окно закроется.")
        self.close()


def main():
    if not os.path.exists(SOBER_CONFIG):
        print("Sober не найден: поставь его (flatpak install flathub org.vinegarhq.Sober) и запусти один раз.")
        sys.exit(1)
    if "--apply" in sys.argv:  # без окна: переложить моды по сохранённым настройкам
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QApplication(sys.argv)
        if sober_running():
            sys.exit("Roblox запущен — применю в следующий раз")
        state = {**DEFAULT_STATE, **load_json(STATE, {})}
        n = apply_mods(state)
        save_json(STATE, state)
        print(f"применено файлов: {n}, тема: {state['theme_applied']}")
        return
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setDesktopFileName("soberstrap")
    app.setStyleSheet(STYLE)
    win = Window()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
