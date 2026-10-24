"""Английский перевод интерфейса. Язык: SOBERSTRAP_LANG=ru|en, иначе по системе (ru/uk/be → русский).

Строки в коде пишутся по-русски; localize() после сборки окна заменяет тексты виджетов,
а _() — для текстов, которые появляются позже (сообщения, подписи, история).
"""
import os

from PySide6.QtWidgets import QAbstractButton, QComboBox, QFormLayout, QGroupBox, QLabel, QTabWidget, QWidget

_lang = os.environ.get("SOBERSTRAP_LANG") or os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") \
    or os.environ.get("LANG", "")
RUSSIAN = _lang[:2].lower() in ("ru", "uk", "be")

EN = {
    # вкладки и кнопки
    "Моды": "Mods", "Темы": "Themes", "Эффекты": "Effects", "Фильтры": "Filters", "Графика": "Graphics",
    "История игр": "Game history", "О программе": "About", "Применить": "Apply",
    "Применить и играть": "Apply and play", "  ·  моды для Sober": "  ·  mods for Sober",
    # моды
    "Курсор": "Cursor", "Стандартный": "Default", "Аккуратная стрелка": "Clean arrow",
    "Точка (для шутеров)": "Dot (for shooters)", "Прицел-крестик": "Crosshair", "Своя картинка…": "Your picture…",
    "Обычный курсор и курсор над кнопками. «Своя картинка»: левый верхний угол — кончик.":
        "Normal cursor and the one over buttons. For your own picture, its top-left corner is the tip.",
    "Шрифт интерфейса": "UI font", "Стандартный (Builder Sans)": "Default (Builder Sans)",
    "Свой файл шрифта…": "Font file…",
    "Меняет шрифт меню, чата и списка игроков. Шрифты, которые выбрал автор игры, не трогаются. "
    "В списке только шрифты с русскими буквами.":
        "Changes the font of menus, chat and the player list. Fonts chosen by a game's author stay as they are. "
        "Only fonts with Cyrillic are listed.",
    "Свои моды": "Folder mods", "Открыть папку модов": "Open mods folder",
    "Пока пусто. Мод — это папка с файлами в той же структуре, что и у Roblox "
    "(content/textures/…, content/fonts/…). Положи её в папку модов и перезапусти окно.":
        "Nothing here yet. A mod is a folder with the same layout as Roblox's files "
        "(content/textures/…, content/fonts/…). Put it into the mods folder and reopen this window.",
    "Картинка курсора": "Cursor picture", "Картинки (*.png *.jpg *.webp *.svg)": "Images (*.png *.jpg *.webp *.svg)",
    "Файл шрифта": "Font file", "Шрифты (*.ttf *.otf)": "Fonts (*.ttf *.otf)",
    # эффекты
    "Цвет эффектов": "Effect colours", "Взрывы": "Explosions", "Силовое поле": "Force field",
    "Перекрашиваются стандартные взрывы и силовое поле Roblox. Если игра рисует свои эффекты, они останутся как есть.":
        "Recolours Roblox's standard explosions and force field. Effects a game draws itself stay as they are.",
    "Как в Roblox": "As in Roblox", "Синий (плазма)": "Blue (plasma)", "Фиолетовый": "Purple", "Розовый": "Pink",
    "Зелёный (кислота)": "Green (acid)", "Бирюзовый": "Cyan", "Радуга": "Rainbow",
    # темы
    "Тема": "Theme", "Без темы": "No theme", "Сама по дате (Хэллоуин, Новый год)": "By date (Halloween, New Year)",
    "Новый год": "New Year", "Хэллоуин": "Halloween", "Что менять": "What to change", "Солнце и луна": "Sun and moon",
    "Значок загрузки и меню паузы": "Loading spinner and pause menu",
    "Искры (эффект Sparkles в играх)": "Sparkles (the Sparkles effect in games)",
    "Снег поверх игры (на Хэллоуин — угольки)": "Snow over the game (embers on Halloween)",
    "Солнце и луна меняются в играх, где автор оставил стандартные. Небо, которое игра ставит сама, не меняется. "
    "Курсор на вкладке «Моды» важнее курсора темы.":
        "Sun and moon change in games that keep the default ones. A sky the game sets itself is not changed. "
        "The cursor on the Mods tab wins over the theme's cursor.",
    "Снег поверх игры — отдельное прозрачное окно над Roblox, клики проходят сквозь него. "
    "Для Хэллоуина это летящие угольки. Включается сам, когда запущен Roblox.":
        "Snow over the game is a separate transparent window above Roblox; clicks pass through it. "
        "On Halloween it's drifting embers. It turns on by itself while Roblox is running.",
    # фильтры
    "Без фильтра": "No filter", "Как задумал Roblox.": "As Roblox intended.",
    "Без фильтра — как задумал Roblox.": "No filter — as Roblox intended.",
    "Сочно": "Vivid", "Кино": "Cinema", "Мечта": "Dream", "Мультик": "Cartoon", "Комикс": "Comic",
    "Пиксель-арт": "Pixel art", "Ретро-телевизор": "Retro TV", "Нуар": "Noir", "Зима": "Winter",
    "Бледные цвета становятся живее, яркие не пересвечиваются.": "Dull colours come alive; bright ones don't clip.",
    "Тёплые света, бирюзовые тени, виньетка и плёночное зерно.": "Warm highlights, teal shadows, vignette and film grain.",
    "Мягкое свечение вокруг ярких мест, пастельные цвета.": "Soft glow around bright spots, pastel colours.",
    "Плоские цвета и чёрные контуры, как в мультфильме.": "Flat colours and black outlines, like a cartoon.",
    "Точечный растр в тенях и контуры, как в напечатанном комиксе.": "Halftone dots in shadows and outlines, like a printed comic.",
    "Крупные пиксели и мало цветов — Roblox как игра с NES.": "Big pixels and few colours — Roblox as an NES game.",
    "Строки развёртки, маска кинескопа, разъезд цветов.": "Scanlines, CRT mask and colour fringing.",
    "Чёрно-белое кино с жёстким контрастом.": "Black-and-white film with hard contrast.",
    "Холодные оттенки и иней по краям экрана.": "Cold tones and frost around the screen edges.",
    "Оранжевые света, фиолетовые тени, тёмные края.": "Orange highlights, purple shadows, dark edges.",
    "Сила": "Strength", "Ступени цвета": "Colour steps", "Контуры": "Outlines", "Размер пикселя": "Pixel size",
    "Цветов на канал": "Colours per channel", "Настройка": "Settings", "Чёткость": "Sharpness",
    "Резкость (AMD CAS)": "Sharpening (AMD CAS)",
    "Работает с любым фильтром и без него: картинка чётче, особенно при сглаживании.":
        "Works with any filter or on its own: a crisper image, especially with anti-aliasing.",
    "Фильтры рисуются поверх готового кадра (vkBasalt, как ReShade на Windows). Другие игроки их не видят, "
    "игра не меняется. Меняются после перезапуска Roblox.":
        "Filters are drawn over the finished frame (vkBasalt, like ReShade on Windows). Other players don't see them "
        "and the game itself is unchanged. They change after restarting Roblox.",
    "Для фильтров нужно расширение vkBasalt для Flatpak (см. README: scripts/build-vkbasalt-ext.sh).":
        "Filters need the vkBasalt Flatpak extension (see README: scripts/build-vkbasalt-ext.sh).",
    # графика
    "Качество": "Quality", "Режим Sober": "Sober mode", "Как на компьютере": "Desktop-like",
    "Сбалансированно (как на телефоне)": "Balanced (phone-like)", "Максимум FPS": "Max FPS",
    "Дальность и детали": "Distance and detail", "авто": "auto", "Сглаживание": "Anti-aliasing",
    "Как решит игра": "Let the game decide", "Выкл": "Off", "Текстуры": "Textures", "Низкие": "Low",
    "Средние": "Medium", "Высокие": "High", "Максимальные": "Maximum", "Прочее": "Other", "Трава": "Grass",
    "Серое небо (меньше отвлекает)": "Gray sky (less distracting)", "Счётчик FPS": "FPS counter",
    "Показывать": "Show", "Где": "Where", "Выключен": "Off", "Только FPS": "FPS only",
    "FPS, загрузка и температура": "FPS, load and temperature", "Подробно (с графиком кадров)": "Detailed (frame graph)",
    "Слева сверху": "Top left", "Справа сверху": "Top right", "Слева снизу": "Bottom left", "Справа снизу": "Bottom right",
    "MangoHud. В игре прячется и показывается клавишами правый Shift + F12.":
        "MangoHud. Hide or show it in game with right Shift + F12.",
    "Нужен MangoHud: flatpak install flathub runtime/org.freedesktop.Platform.VulkanLayer.MangoHud/x86_64/26.08":
        "Needs MangoHud: flatpak install flathub runtime/org.freedesktop.Platform.VulkanLayer.MangoHud/x86_64/26.08",
    "Показывать игру в статусе Discord": "Show the game in Discord status",
    "Кнопка «Присоединиться» в Discord для друзей": "“Join” button in Discord for friends",
    "Показывать, в какой стране сервер": "Show which country the server is in",
    "Закрывать Roblox при выходе из игры": "Close Roblox when leaving a game",
    "GameMode (система отдаёт игре больше ресурсов)": "GameMode (the system gives the game more resources)",
    "Используются только флаги из официального списка, который Roblox разрешил с сентября 2025. "
    "Настройки качества в самой игре тоже работают — эти просто сильнее.":
        "Only flags from the official allow-list (since September 2025) are used. The in-game quality settings "
        "still work — these just go further.",
    # история
    "Играть снова": "Play again", "На тот же сервер": "Same server", "Страница игры": "Game page",
    "Берётся из логов Sober. Названия и иконки игр подгружаются с сайта Roblox. "
    "«На тот же сервер» сработает, только если сервер ещё жив.":
        "Read from Sober's logs. Game names and icons are loaded from the Roblox website. "
        "“Same server” works only while that server is still running.",
    "Пока пусто — поиграй, и здесь появятся игры.": "Nothing yet — play something and it will show up here.",
    "Игра {place}": "Game {place}", "{h} ч {m} мин": "{h} h {m} min", "{m} мин": "{m} min",
    # о программе и сообщения
    "<b>{app}</b> — косметические моды для Roblox через Sober.": "<b>{app}</b> — cosmetic mods for Roblox via Sober.",
    "Только внешний вид и удобство: курсоры, шрифты, графика. Никаких преимуществ в игре — SoberStrap меняет "
    "файлы у тебя на компьютере, другие игроки ничего не видят. Всё снимается кнопкой ниже.":
        "Only looks and comfort: cursors, fonts, graphics. No in-game advantage — SoberStrap changes files on your "
        "computer and other players see nothing. Everything is undone with the button below.",
    "Вернуть всё как было": "Restore everything", "Моды: {overlay}\nНастройки Sober: {config}":
        "Mods: {overlay}\nSober settings: {config}",
    "Применяю…": "Applying…", "Готово: файлов модов — {n}. Запусти Roblox.": "Done: {n} mod files. Start Roblox.",
    "Не получилось применить:\n{e}": "Couldn't apply:\n{e}",
    "Roblox (Sober) сейчас запущен. Закрой его — изменения подхватятся только при следующем запуске.":
        "Roblox (Sober) is running. Close it — changes are picked up on the next launch.",
    "Сначала закрой Roblox (Sober).": "Close Roblox (Sober) first.",
    "Всё вернул как было. Окно закроется.": "Everything is restored. The window will close.",
}


def _(text):
    return text if RUSSIAN else EN.get(text, text)


def localize(root: QWidget):
    """Переводит тексты уже собранных виджетов (вкладки, кнопки, подписи, списки, рамки, подписи форм)."""
    if RUSSIAN:
        return
    for w in [root, *root.findChildren(QWidget)]:
        if isinstance(w, QTabWidget):
            for i in range(w.count()):
                w.setTabText(i, _(w.tabText(i)))
        elif isinstance(w, QComboBox):
            for i in range(w.count()):
                w.setItemText(i, _(w.itemText(i)))
        elif isinstance(w, QGroupBox):
            w.setTitle(_(w.title()))
        elif isinstance(w, (QLabel, QAbstractButton)):
            t = w.text()
            if t in EN:
                w.setText(EN[t])
            elif "  ·  моды для Sober" in t:
                w.setText(t.replace("  ·  моды для Sober", EN["  ·  моды для Sober"]))
        if w.toolTip():
            w.setToolTip(_(w.toolTip()))
