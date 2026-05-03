"""
BizarroLand - Descargador de mods local
Lee el mods_manifest.json y descarga todos los mods a la carpeta /mods
"""

import json
import os
import sys
from pathlib import Path
import requests

MANIFEST_FILE = "mods_manifest.json"
MODS_DIR = Path("mods")

def download_mod(mod: dict) -> bool:
    url = mod.get("url", "")
    filename = mod.get("filename", "")

    if not url or url in ("NO_DISPONIBLE", "") or url.startswith("VERIFICAR"):
        print(f"  ⏭️  Saltando '{mod['name']}' — sin URL válida")
        return False

    dest = MODS_DIR / filename
    if dest.exists():
        print(f"  ✅ Ya existe: {filename}")
        return True

    print(f"  ⬇️  Descargando {mod['name']}...")
    print(f"      {url}")
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r      {pct:.1f}%", end="", flush=True)
        print(f"\r      ✅ Descargado ({downloaded/1024/1024:.1f} MB)    ")
        return True
    except Exception as e:
        print(f"\r      ❌ Error: {e}")
        if dest.exists():
            dest.unlink()
        return False


def main():
    if not Path(MANIFEST_FILE).exists():
        print(f"❌ No se encuentra '{MANIFEST_FILE}' en esta carpeta.")
        print(f"   Ejecuta este script en la misma carpeta que el manifest.")
        sys.exit(1)

    with open(MANIFEST_FILE, encoding="utf-8") as f:
        data = json.load(f)

    mods = data.get("mods", [])
    deps = data.get("dependencies_required", [])
    all_items = deps + mods

    MODS_DIR.mkdir(exist_ok=True)
    print(f"📁 Carpeta de mods: {MODS_DIR.resolve()}")
    print(f"📋 {len(mods)} mods + {len(deps)} dependencias\n")

    ok, skipped, failed = 0, 0, 0

    # Dependencias primero
    if deps:
        print("── DEPENDENCIAS ──────────────────────────")
        for dep in deps:
            result = download_mod(dep)
            if result:
                ok += 1
            elif dep.get("url", "").startswith("VERIFICAR") or not dep.get("url"):
                skipped += 1
            else:
                failed += 1

    # Mods
    print("\n── MODS ──────────────────────────────────")
    for mod in mods:
        result = download_mod(mod)
        if result:
            ok += 1
        elif mod.get("url", "NO_DISPONIBLE") in ("NO_DISPONIBLE", "") or \
             mod.get("url", "").startswith("VERIFICAR"):
            skipped += 1
        else:
            failed += 1

    print(f"\n{'─'*45}")
    print(f"✅ Descargados/existentes : {ok}")
    print(f"⏭️  Saltados (sin URL)     : {skipped}")
    print(f"❌ Errores                : {failed}")
    print(f"\n📁 Mods en carpeta: {len(list(MODS_DIR.glob('*.jar')))}")

    if failed:
        print(f"\n⚠️  {failed} mod(s) fallaron. Descárgalos manualmente desde Modrinth.")

if __name__ == "__main__":
    main()
