# SoberStrap

A Bloxstrap-like manager for [Sober](https://sober.vinegarhq.org/), the Roblox client for Linux: cosmetic mods,
graphics filters and settings. Everything changes only what **you** see on your own screen. There are no gameplay
changes, cheats or injected scripts.

> The interface is in English and Russian (picked from your system language; force it with `SOBERSTRAP_LANG=en` or `ru`). Russian README: [README.ru.md](README.ru.md).

## Features

* **Filters**: ten post-processing looks applied to the finished frame. They are vivid, cinema, dream, cartoon,
  comic, pixel art, retro TV, noir, winter and Halloween, each with sliders. AMD CAS sharpening can be used with any
  of them or on its own. On Windows, Roblox's anti-cheat blocks ReShade. Here the same idea works through
  [vkBasalt](https://github.com/DadSchoorse/vkBasalt).
* **Themes**: New Year and Halloween. Each changes the cursor, sun and moon, loading spinner, pause-menu glow and
  sparkles. It also adds snow or embers in a click-through overlay above the game. A theme can be switched
  automatically by date.
* **Cursors**: a clean arrow, a dot, a crosshair, or your own picture.
* **UI font**: any installed font that has Cyrillic, or a font file.
* **Graphics**: Sober's quality mode plus the FFlags that Roblox allows since September 2025. These cover quality
  level, MSAA, textures, grass and gray sky.
* **FPS counter**: [MangoHud](https://github.com/flightlessmango/MangoHud) presets.
* **Game history**: what you played and for how long, read from Sober's logs. It has "play again" and
  "same server" buttons.
* **Effect colours**: explosion and force-field colours recoloured from Roblox's own textures.
* **Folder mods**: put a folder with Roblox's `content/...` structure into `~/.local/share/soberstrap/mods/`.
* **Reset**: one button removes every file SoberStrap placed and restores Sober's config.

Mods go to Sober's `asset_overlay` directory. Filters and the FPS counter are environment variables set with
`flatpak override --user`. Changes apply on the next Sober launch.

## Install

Requirements:

* Sober (`flatpak install flathub org.vinegarhq.Sober`), launched at least once;
* Python 3 with `PySide6`, `numpy` and `Pillow`, plus fontconfig.

Run these commands:

```
git clone https://github.com/iosifsid857-dev/soberstrap && cd soberstrap
python3 soberstrap.py
```

### FPS counter

Install MangoHud for Flatpak. The branch must match Sober's runtime, which is currently 26.08:

```
flatpak install flathub runtime/org.freedesktop.Platform.VulkanLayer.MangoHud/x86_64/26.08
```

### Filters

Sober only loads Vulkan layers that come from Flatpak extensions, and Flathub has no vkBasalt for 26.08 yet. The
script below builds vkBasalt and installs it as a local Flatpak extension.

It needs these build tools:

* `git`, `meson`, `ninja`, `g++`
* `glslang`, `vulkan-headers`, `libX11-devel`

```
scripts/build-vkbasalt-ext.sh
```

## Notes

* Snow, embers and the FPS counter can be hidden at any time. Press right Shift + F12 to toggle the FPS counter.
* Your own skies and fonts work only where the game itself doesn't override them.
* SoberStrap is not affiliated with Roblox, VinegarHQ or Bloxstrap.

## Support

If you find SoberStrap useful, you can support the author: [Monobank jar](https://send.monobank.ua/jar/ABkwFDAY2V).

## Credits

SoberStrap is MIT licensed. Filters run on vkBasalt (zlib) and the FPS counter on MangoHud (MIT). Neither is bundled:
both are installed separately. Developed together with Claude (Anthropic) as a coding assistant.
