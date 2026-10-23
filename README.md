# SoberStrap

Cosmetic mods and graphics settings for [Sober](https://sober.vinegarhq.org/) (Roblox on Linux) — a small
Bloxstrap-like manager. Only things you see yourself: cursors, UI font, graphics quality. No gameplay changes.

* **Cursors** — built-in styles (clean arrow, dot, crosshair) or your own picture.
* **UI font** — any installed font (with Cyrillic), or a font file.
* **Graphics** — Sober's quality mode plus Roblox's allow-listed FFlags (quality level, MSAA, textures, grass, gray sky).
* **Folder mods** — drop a folder with Roblox's `content/...` structure into `~/.local/share/soberstrap/mods/`.
* **Reset** — one button removes every file it placed and restores the config.

Files go to Sober's `asset_overlay`; changes apply on the next Sober launch.

```
python3 soberstrap.py      # needs PySide6 and fontconfig
```

MIT license. Not affiliated with Roblox or VinegarHQ.
