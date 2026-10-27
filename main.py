import os
import sys
import shutil
import ctypes
import subprocess
import threading
import customtkinter as ctk
from PIL import Image

APP_NAME = "Nex Tools"
VERSION = "1.0.0"

# Couleurs (thème Nexora)
BG = "#0B0716"
CARD = "#130D24"
BORDER = "#2A1B4D"
ACCENT = "#7C3AED"
ACCENT_HOVER = "#6D28D9"
ACCENT_LIGHT = "#A78BFA"
TEXT = "#F3EEFF"
MUTED = "#8B80A8"
OK = "#34D399"
WARN = "#FBBF24"
ERR = "#F87171"


def res(path):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, path)


# Chemins dynamiques : s'adaptent au nom d'utilisateur de chaque PC
LOCAL = os.environ.get("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local"))
USER_TEMP = os.environ.get("TEMP", os.path.join(LOCAL, "Temp"))
WINDIR = os.environ.get("SystemRoot", r"C:\Windows")
FIVEM = os.path.join(LOCAL, "FiveM", "FiveM.app")

BASIC = [
    os.path.join(FIVEM, "logs"),
    os.path.join(FIVEM, "crashes"),
    os.path.join(FIVEM, "data", "cache"),
    os.path.join(FIVEM, "data", "nui-storage"),
    os.path.join(FIVEM, "data", "server-cache"),
    os.path.join(FIVEM, "data", "server-cache-priv"),
]
ADVANCED = BASIC + [
    os.path.join(FIVEM, "citizen"),
    USER_TEMP,
    os.path.join(WINDIR, "Temp"),
    os.path.join(WINDIR, "Prefetch"),
]
NETWORK = [
    ("Vider le cache DNS", ["ipconfig", "/flushdns"]),
    ("Réenregistrer le DNS", ["ipconfig", "/registerdns"]),
    ("Vider le cache NetBIOS", ["nbtstat", "-R"]),
    ("Réenregistrer les noms NetBIOS", ["nbtstat", "-RR"]),
    ("Vider le cache ARP", ["arp", "-d", "*"]),
]

NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def size_of(path):
    total = 0
    try:
        if os.path.isfile(path) or os.path.islink(path):
            return os.path.getsize(path)
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    except OSError:
        pass
    return total


def wipe_contents(folder):
    """Supprime le contenu d'un dossier (pas le dossier). Retourne (octets, supprimés, ignorés)."""
    freed = removed = skipped = 0
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return 0, 0, 0
    for e in entries:
        sz = size_of(e.path)
        try:
            if e.is_dir(follow_symlinks=False):
                shutil.rmtree(e.path, ignore_errors=True)
                if os.path.exists(e.path):
                    skipped += 1
                    continue
            else:
                os.remove(e.path)
            freed += sz
            removed += 1
        except OSError:
            skipped += 1
    return freed, removed, skipped


def fmt(n):
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024 or unit == "Go":
            return f"{n:.1f} {unit}" if unit != "o" else f"{int(n)} o"
        n /= 1024


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("620x700")
        self.minsize(560, 640)
        self.configure(fg_color=BG)
        try:
            self.iconbitmap(res("logo.ico"))
        except Exception:
            pass

        self.buttons = []
        self.busy = False
        self._build_ui()
        if not is_admin():
            self.log("Lancé sans droits administrateur : certains dossiers système seront ignorés.", WARN)

    # ---------- UI ----------
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(24, 8))
        try:
            img = ctk.CTkImage(Image.open(res("logo.png")), size=(96, 96))
            ctk.CTkLabel(header, image=img, text="").pack()
        except Exception:
            pass
        ctk.CTkLabel(header, text="NEX TOOLS", font=("Segoe UI", 28, "bold"), text_color=TEXT).pack(pady=(6, 0))
        ctk.CTkLabel(header, text="NEXORA COMMUNITY · Optimisation FiveM & Windows",
                     font=("Consolas", 11), text_color=ACCENT_LIGHT).pack()

        self._card("Clean Basic", "Logs, crashs, caches FiveM (cache, NUI, server-cache).",
                   "Lancer", lambda: self.run(self.clean_basic))
        self._card("Clean Advanced", "Basic + dossier citizen, Temp utilisateur, Windows\\Temp, Prefetch.\nFiveM retéléchargera certains fichiers au prochain lancement.",
                   "Lancer", lambda: self.run(self.clean_advanced))
        self._card("Network Clean", "Flush DNS, NetBIOS, ARP. Sans risque, sans redémarrage.",
                   "Lancer", lambda: self.run(self.network_clean))

        self.progress = ctk.CTkProgressBar(self, height=6, progress_color=ACCENT, fg_color=BORDER,
                                           mode="indeterminate")
        self.progress.pack(fill="x", padx=32, pady=(10, 6))
        self.progress.set(0)

        self.console = ctk.CTkTextbox(self, fg_color=CARD, border_color=BORDER, border_width=1,
                                      text_color=TEXT, font=("Consolas", 12), corner_radius=10)
        self.console.pack(fill="both", expand=True, padx=32, pady=(0, 20))
        for name, color in (("ok", OK), ("warn", WARN), ("err", ERR), ("muted", MUTED), ("accent", ACCENT_LIGHT)):
            self.console.tag_config(name, foreground=color)
        self.console.configure(state="disabled")

    def _card(self, title, desc, btn_text, cmd):
        card = ctk.CTkFrame(self, fg_color=CARD, border_color=BORDER, border_width=1, corner_radius=12)
        card.pack(fill="x", padx=32, pady=6)
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=16, pady=12)
        ctk.CTkLabel(left, text=title, font=("Segoe UI", 15, "bold"), text_color=TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(left, text=desc, font=("Segoe UI", 11), text_color=MUTED, anchor="w",
                     justify="left", wraplength=340).pack(fill="x")
        b = ctk.CTkButton(card, text=btn_text, width=100, height=36, corner_radius=8,
                          fg_color=ACCENT, hover_color=ACCENT_HOVER, font=("Segoe UI", 13, "bold"),
                          command=cmd)
        b.pack(side="right", padx=16)
        self.buttons.append(b)

    # ---------- Logs / threads ----------
    def log(self, msg, tag=None):
        def _w():
            self.console.configure(state="normal")
            self.console.insert("end", msg + "\n", tag)
            self.console.see("end")
            self.console.configure(state="disabled")
        self.after(0, _w)

    def run(self, fn):
        if self.busy:
            return
        self.busy = True
        for b in self.buttons:
            b.configure(state="disabled")
        self.progress.start()
        threading.Thread(target=self._worker, args=(fn,), daemon=True).start()

    def _worker(self, fn):
        try:
            fn()
        except Exception as ex:
            self.log(f"Erreur : {ex}", ERR)
        finally:
            self.after(0, self._done)

    def _done(self):
        self.progress.stop()
        self.progress.set(0)
        for b in self.buttons:
            b.configure(state="normal")
        self.busy = False

    # ---------- Actions ----------
    def clean_paths(self, paths):
        total = 0
        for p in paths:
            if not os.path.isdir(p):
                self.log(f"– Introuvable : {p}", "muted")
                continue
            freed, removed, skipped = wipe_contents(p)
            total += freed
            extra = f" ({skipped} ignorés, en cours d'utilisation)" if skipped else ""
            self.log(f"✓ {p}  →  {fmt(freed)}{extra}", "ok" if not skipped else "warn")
        self.log(f"Terminé : {fmt(total)} libérés.\n", "accent")

    def clean_basic(self):
        self.log("▶ Clean Basic", "accent")
        self.clean_paths(BASIC)

    def clean_advanced(self):
        self.log("▶ Clean Advanced", "accent")
        self.clean_paths(ADVANCED)

    def network_clean(self):
        self.log("▶ Network Clean", "accent")
        for label, cmd in NETWORK:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, creationflags=NO_WINDOW, timeout=30)
                ok = r.returncode == 0
                self.log(f"{'✓' if ok else '✗'} {label}", "ok" if ok else "err")
            except Exception:
                self.log(f"✗ {label}", "err")
        self.log("Terminé.\n", "accent")


if __name__ == "__main__":
    App().mainloop()
