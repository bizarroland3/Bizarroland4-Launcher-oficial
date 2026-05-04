import os
import sys
import json
import threading
import subprocess
import hashlib
import shutil
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox
import requests
import minecraft_launcher_lib

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DEL SERVIDOR
# ─────────────────────────────────────────────
LAUNCHER_VERSION = "1.0.2"
MC_VERSION = "1.20.1"
FORGE_VERSION = "47.4.0"

# ID que usa la API para DESCARGAR Forge
FORGE_DOWNLOAD_ID = f"{MC_VERSION}-{FORGE_VERSION}" 

# URL del JSON de mods (asegúrate de que sea pública)
MODS_MANIFEST_URL = "https://raw.githubusercontent.com/bizarroland3/Bizarroland4-Launcher-oficial/refs/heads/main/mods_manifest.json"

BIZARRO_DIR = Path.home() / ".bizarroland"
MODS_DIR = BIZARRO_DIR / "mods"
CONFIG_FILE = BIZARRO_DIR / "launcher_config.json"

# ─────────────────────────────────────────────
#  UTILIDADES
# ─────────────────────────────────────────────

def ensure_dirs():
    BIZARRO_DIR.mkdir(parents=True, exist_ok=True)
    MODS_DIR.mkdir(parents=True, exist_ok=True)
    (BIZARRO_DIR / "versions").mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {"username": "", "ram": "4"}

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch_mods_manifest() -> dict | None:
    try:
        r = requests.get(MODS_MANIFEST_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def check_mod_updates(manifest: dict) -> list[dict]:
    pending = []
    for mod in manifest.get("mods", []):
        local = MODS_DIR / mod["filename"]
        if not local.exists():
            pending.append({**mod, "reason": "no instalado"})
        elif mod.get("sha256") and not mod["sha256"].startswith("placeholder"):
            if sha256_file(local) != mod["sha256"]:
                pending.append({**mod, "reason": "actualización"})
    return pending

def download_mod(mod: dict, progress_cb=None) -> bool:
    dest = MODS_DIR / mod["filename"]
    try:
        r = requests.get(mod["url"], stream=True, timeout=20)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb and total:
                    progress_cb(downloaded / total)
        return True
    except Exception:
        if dest.exists(): dest.unlink()
        return False

def is_forge_installed() -> bool:
    installed = minecraft_launcher_lib.utils.get_installed_versions(str(BIZARRO_DIR))
    # Buscamos si existe alguna carpeta que contenga 'forge' y la versión '1.20.1'
    return any("forge" in v["id"].lower() and MC_VERSION in v["id"] for v in installed)

# ─────────────────────────────────────────────
#  LAUNCHER GUI
# ─────────────────────────────────────────────

ctk.set_appearance_mode("dark")
DARK_BG, PANEL_BG, ACCENT, ACCENT2 = "#0a0a0f", "#10101a", "#7c3aed", "#c026d3"
TEXT_MAIN, TEXT_DIM, SUCCESS, WARNING, ERROR_COL, BORDER = "#e2e8f0", "#64748b", "#22c55e", "#f59e0b", "#ef4444", "#1e1e2e"

class BizarroLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.cfg = load_config()
        self.title("BizarroLand Launcher")
        self.geometry("780x520")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self._build_ui()
        self._start_startup_checks()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, height=90)
        header.place(x=0, y=0, relwidth=1)
        ctk.CTkLabel(header, text="✦ BIZARROLAND ✦", font=("Georgia", 28, "bold"), text_color=TEXT_MAIN).place(relx=0.5, rely=0.4, anchor="center")
        ctk.CTkLabel(header, text=f"MC {MC_VERSION} | Forge {FORGE_VERSION}", font=("Arial", 10), text_color=ACCENT).place(relx=0.98, rely=0.8, anchor="e")

        # Main Panel
        main = ctk.CTkFrame(self, fg_color="transparent", height=390)
        main.place(x=0, y=90, relwidth=1)

        # Config Panel (Left)
        left = ctk.CTkFrame(main, fg_color=PANEL_BG, corner_radius=12, border_width=1, border_color=BORDER, width=240, height=365)
        left.place(x=20, y=10)
        
        ctk.CTkLabel(left, text="NICKNAME", font=("Arial", 10, "bold"), text_color=ACCENT).pack(pady=(20, 0))
        self.username_var = ctk.StringVar(value=self.cfg.get("username", ""))
        self.username_entry = ctk.CTkEntry(left, textvariable=self.username_var, fg_color="#1a1a2e", border_color=ACCENT, width=200)
        self.username_entry.pack(pady=10)

        ctk.CTkLabel(left, text="RAM (GB)", font=("Arial", 10, "bold"), text_color=ACCENT).pack(pady=(10, 0))
        self.ram_var = ctk.IntVar(value=int(self.cfg.get("ram", 4)))
        self.ram_slider = ctk.CTkSlider(left, from_=2, to=16, number_of_steps=14, variable=self.ram_var, button_color=ACCENT)
        self.ram_slider.pack(pady=10)
        self.ram_label = ctk.CTkLabel(left, text=f"{self.ram_var.get()} GB", text_color=TEXT_MAIN)
        self.ram_label.pack()
        self.ram_slider.configure(command=lambda v: self.ram_label.configure(text=f"{int(v)} GB"))

        self.forge_status_lbl = ctk.CTkLabel(left, text="🔍 Verificando Forge...", font=("Arial", 10), text_color=TEXT_DIM)
        self.forge_status_lbl.pack(pady=(20, 0))
        self.mods_status_lbl = ctk.CTkLabel(left, text="🔍 Verificando Mods...", font=("Arial", 10), text_color=TEXT_DIM)
        self.mods_status_lbl.pack()

        # Log Panel (Right)
        right = ctk.CTkFrame(main, fg_color=PANEL_BG, corner_radius=12, border_width=1, border_color=BORDER, width=472, height=365)
        right.place(x=278, y=10)
        self.log_box = ctk.CTkTextbox(right, fg_color="#0d0d1a", text_color=TEXT_MAIN, font=("Courier New", 11), width=450, height=280)
        self.log_box.pack(pady=10, padx=10)
        self.log_box.configure(state="disabled")

        self.progress_bar = ctk.CTkProgressBar(right, progress_color=ACCENT, width=440)
        self.progress_bar.pack(pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(right, text="", font=("Arial", 10), text_color=TEXT_DIM)
        self.progress_label.pack()

        # Footer / Play Button
        bar = ctk.CTkFrame(self, fg_color=PANEL_BG, height=40)
        bar.place(x=0, y=480, relwidth=1)
        self.play_btn = ctk.CTkButton(bar, text="⚡ JUGAR", font=("Arial", 14, "bold"), fg_color=ACCENT, hover_color=ACCENT2, width=160, command=self._on_play)
        self.play_btn.place(relx=0.5, rely=0.5, anchor="center")
        self.play_btn.configure(state="disabled")

    def _log(self, msg):
        self.after(0, lambda: (self.log_box.configure(state="normal"), self.log_box.insert("end", msg + "\n"), self.log_box.see("end"), self.log_box.configure(state="disabled")))

    def _set_progress(self, val, txt):
        self.after(0, lambda: (self.progress_bar.set(val), self.progress_label.configure(text=txt)))

    def _on_play(self):
        user = self.username_var.get().strip()
        if not user: return messagebox.showwarning("Error", "Escribe tu nombre.")
        save_config({"username": user, "ram": str(self.ram_var.get())})
        self.play_btn.configure(state="disabled", text="Lanzando...")
        threading.Thread(target=self._launch_game, daemon=True).start()

    def _start_startup_checks(self):
        threading.Thread(target=self._startup_sequence, daemon=True).start()

    def _startup_sequence(self):
        self._log("🚀 Iniciando BizarroLand Launcher...")
        
        # 1. Forge
        if not is_forge_installed():
            self._log("📦 Forge no detectado. Instalando...")
            self._install_forge()
        else:
            self._log("✅ Forge detectado correctamente.")
            self.after(0, lambda: self.forge_status_lbl.configure(text="✅ Forge OK", text_color=SUCCESS))

        # 2. Mods
        self._check_and_update_mods()

        self._log("✅ Listo para jugar.")
        self.after(0, lambda: (self.play_btn.configure(state="normal"), self.play_btn.configure(text="⚡ JUGAR")))

    def _install_forge(self):
        mc_dir = str(BIZARRO_DIR)
        cb = {"setStatus": lambda s: self._log(f"  {s}"), "setProgress": lambda p: self._set_progress(p, "Descargando..."), "setMax": lambda _: None}
        
        try:
            self._log("📦 Instalando versión base de Minecraft...")
            minecraft_launcher_lib.install.install_minecraft_version(MC_VERSION, mc_dir, callback=cb)
            
            self._log(f"🛠️ Instalando Forge (versión {FORGE_DOWNLOAD_ID})...")
            # Usa el método compatible para instalar Forge
            if minecraft_launcher_lib.forge.supports_automatic_install(FORGE_DOWNLOAD_ID):
                minecraft_launcher_lib.forge.install_forge_version(FORGE_DOWNLOAD_ID, mc_dir, callback=cb)
                self.after(0, lambda: self.forge_status_lbl.configure(text="✅ Forge Instalado", text_color=SUCCESS))
                self._log("✅ Instalación de Forge completada.")
            else:
                self._log("⚠️ Esta versión requiere instalación manual.")
                minecraft_launcher_lib.forge.run_forge_installer(FORGE_DOWNLOAD_ID)
                self._log("✅ Completa el instalador que apareció en pantalla.")
                
        except Exception as e:
            self._log(f"❌ Error instalando Forge: {e}")
            self.after(0, lambda: self.forge_status_lbl.configure(text="❌ Error de Forge", text_color=ERROR_COL))

    def _check_and_update_mods(self):
        manifest = fetch_mods_manifest()
        if not manifest:
            self._log("⚠️ No se pudo conectar al servidor de mods. Saltando...")
            self.after(0, lambda: self.mods_status_lbl.configure(text="⚠️ Modo Offline", text_color=WARNING))
            return

        pending = check_mod_updates(manifest)
        if not pending:
            self._log("✅ Mods actualizados.")
            self.after(0, lambda: self.mods_status_lbl.configure(text=f"✅ {len(manifest.get('mods',[]))} Mods OK", text_color=SUCCESS))
            return

        for mod in pending:
            self._log(f"⬇️ Descargando {mod['name']}...")
            download_mod(mod, progress_cb=lambda p: self._set_progress(p, f"Descargando {mod['name']}"))
        
        self._set_progress(0, "")
        self.after(0, lambda: self.mods_status_lbl.configure(text="✅ Mods Sincronizados", text_color=SUCCESS))

    def _launch_game(self):
        mc_dir = str(BIZARRO_DIR)
        
        # Búsqueda dinámica de la carpeta de Forge
        installed = minecraft_launcher_lib.utils.get_installed_versions(mc_dir)
        target_version = None
        for v in installed:
            if "forge" in v["id"].lower() and MC_VERSION in v["id"]:
                target_version = v["id"]
                break
                
        if not target_version:
            self._log("❌ No se encontró la instalación de Forge. Reinicia el launcher.")
            self.after(0, lambda: self.play_btn.configure(state="normal", text="⚡ REINTENTAR"))
            return

        self._log(f"🎮 Ejecutando: {target_version}...")

        try:
            options = {
                "username": self.username_var.get(),
                "uuid": str(__import__("uuid").uuid4()),
                "token": "0",
                "jvmArguments": [f"-Xmx{self.ram_var.get()}G", "-XX:+UseG1GC"]
            }
            cmd = minecraft_launcher_lib.command.get_minecraft_command(target_version, mc_dir, options)
            subprocess.Popen(cmd)
            self.after(2000, self.destroy)
        except Exception as e:
            self._log(f"❌ Error al lanzar: {e}")
            self.after(0, lambda: self.play_btn.configure(state="normal", text="⚡ REINTENTAR"))

if __name__ == "__main__":
    app = BizarroLauncher()
    app.mainloop()