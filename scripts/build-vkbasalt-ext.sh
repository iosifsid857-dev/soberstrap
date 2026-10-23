#!/bin/bash
# Собирает vkBasalt и ставит его как расширение Flatpak (org.freedesktop.Platform.VulkanLayer.vkBasalt//26.08).
# Sober загружает Vulkan-слои только из расширений Flatpak, а на Flathub vkBasalt для 26.08 пока нет.
# Нужно: git, meson, ninja, g++, glslang, vulkan-headers, libX11-devel.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC=${VKBASALT_SRC:-$ROOT/vkbasalt-ext/src}
OUT=$ROOT/vkbasalt-ext
BRANCH=${FLATPAK_BRANCH:-26.08}

[ -d "$SRC/.git" ] || git clone --depth 1 https://github.com/DadSchoorse/vkBasalt.git "$SRC"
meson setup "$SRC/build" "$SRC" --buildtype=release --wipe >/dev/null
ninja -C "$SRC/build"

rm -rf "$OUT/build" "$OUT/repo"
mkdir -p "$OUT/build/files/lib/x86_64-linux-gnu" "$OUT/build/files/share/vulkan/implicit_layer.d" \
         "$OUT/build/files/share/licenses/vkBasalt"
cp "$SRC/build/src/libvkbasalt.so" "$OUT/build/files/lib/x86_64-linux-gnu/"
cp "$SRC"/LICENSE* "$OUT/build/files/share/licenses/vkBasalt/" 2>/dev/null || true
sed 's|"library_path": *"[^"]*"|"library_path": "/usr/lib/extensions/vulkan/vkBasalt/lib/x86_64-linux-gnu/libvkbasalt.so"|' \
    "$SRC/build/config/vkBasalt.json" > "$OUT/build/files/share/vulkan/implicit_layer.d/vkBasalt.x86_64.json"
cat > "$OUT/build/metadata" <<META
[Runtime]
name=org.freedesktop.Platform.VulkanLayer.vkBasalt
runtime=org.freedesktop.Platform/x86_64/$BRANCH
sdk=org.freedesktop.Sdk/x86_64/$BRANCH

[ExtensionOf]
ref=runtime/org.freedesktop.Platform/x86_64/$BRANCH
runtime=org.freedesktop.Platform/x86_64/$BRANCH
META

# пустой репозиторий с маленьким порогом свободного места (по умолчанию ostree требует 3% диска)
flatpak build-export --runtime --arch=x86_64 "$OUT/repo" "$OUT/build" "$BRANCH" >/dev/null 2>&1 || true
grep -q min-free-space "$OUT/repo/config" || sed -i '/^\[core\]/a min-free-space-size=50MB' "$OUT/repo/config"
flatpak build-export --runtime --arch=x86_64 "$OUT/repo" "$OUT/build" "$BRANCH"

flatpak --user remote-delete soberstrap-local 2>/dev/null || true
flatpak --user remote-add --no-gpg-verify soberstrap-local "$OUT/repo"
flatpak --user install -y --reinstall soberstrap-local "runtime/org.freedesktop.Platform.VulkanLayer.vkBasalt/x86_64/$BRANCH"
echo "vkBasalt для Sober установлен"
