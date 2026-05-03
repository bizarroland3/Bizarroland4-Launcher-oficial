# 🎮 BizarroLand Launcher

Launcher personalizado para el servidor de Minecraft **BizarroLand** (1.20.1 + Forge).

---

## Requisitos

- Python 3.11+
- Java 17+ instalado en el sistema
- Conexión a internet para la primera instalación

---

## Instalación

```bash
pip install -r requirements.txt
python launcher.py
```

---

## Estructura del proyecto

```
bizarroland_launcher/
├── launcher.py           # Launcher principal
├── mods_manifest.json    # Manifest de mods (sube esto a tu servidor/GitHub)
└── requirements.txt
```

El launcher guarda los archivos de Minecraft en:
- **Linux/Mac:** `~/.bizarroland/`
- **Windows:** `C:\Users\TU_USUARIO\.bizarroland\`

---

## Cómo gestionar los mods del servidor

### 1. Sube `mods_manifest.json` a un servidor o GitHub

El launcher descarga este JSON cada vez que arranca para detectar cambios.

**Ejemplo con GitHub:**  
Sube el archivo a un repositorio público y usa la URL raw:
```
https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/mods_manifest.json
```

Edita esta constante en `launcher.py`:
```python
MODS_MANIFEST_URL = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/mods_manifest.json"
```

### 2. Formato del manifest

```json
{
  "version": "1",
  "mods": [
    {
      "name": "Nombre del mod",
      "filename": "archivo.jar",
      "url": "https://enlace-directo-al-jar",
      "sha256": "hash-sha256-del-archivo"
    }
  ]
}
```

### 3. Para actualizar los mods

1. Sube los nuevos `.jar` a tu servidor/CDN
2. Actualiza las URLs y hashes en `mods_manifest.json`
3. Incrementa el campo `"version"`
4. La próxima vez que arranquen el launcher, se actualizan automáticamente

### Obtener el hash SHA256 de un .jar

```bash
# Linux/Mac
sha256sum archivo.jar

# Windows (PowerShell)
Get-FileHash archivo.jar -Algorithm SHA256
```

---

## Configuración avanzada

Edita las constantes al inicio de `launcher.py`:

| Constante | Descripción |
|-----------|-------------|
| `MC_VERSION` | Versión de Minecraft (ej: `"1.20.1"`) |
| `FORGE_VERSION` | Versión de Forge (ej: `"47.3.0"`) |
| `MODS_MANIFEST_URL` | URL de tu manifest de mods |
| `BIZARRO_DIR` | Directorio de instalación |

---

## Flujo de arranque

```
Launcher arranca
    ├── ¿Forge instalado?
    │       NO → instala Minecraft base + Forge automáticamente
    │       SÍ → continúa
    │
    ├── Descarga mods_manifest.json desde el servidor
    │       ├── ¿Algún mod falta o tiene hash distinto?
    │       │       SÍ → descarga los mods nuevos/actualizados
    │       │       NO → "todos los mods al día"
    │       └── Sin conexión → avisa y usa los mods locales ya instalados
    │
    └── Botón JUGAR habilitado
```

# Bizarroland4-Launcher-oficial
