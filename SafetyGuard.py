import os
import sys
import time
import ctypes
import logging
import logging.handlers
import tkinter as tk

import numpy as np
import pyautogui

# ------------------------------------------------------------
# Windows: evita que el escalado de pantalla (DPI) desfase los clicks.
# Debe ejecutarse ANTES de crear la ventana de Tk.
# ------------------------------------------------------------
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # Windows 8.1 o superior
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()    # Windows 7
    except Exception:
        pass

pyautogui.FAILSAFE = False  # la máquina no tiene mouse físico, no hace falta

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
# Carpeta del programa (funciona tanto con .py como con el .exe de PyInstaller)
if getattr(sys, "frozen", False):
    CARPETA = os.path.dirname(sys.executable)
else:
    CARPETA = os.path.dirname(os.path.abspath(__file__))

IMG_START = os.path.join(CARPETA, "start.jpg")
IMG_STOP = os.path.join(CARPETA, "stop.jpg")
ARCHIVO_LOG = os.path.join(CARPETA, "safetyguard.log")

ESPERA_CLICK_MS = 1000          # 1 segundo antes de clickear start / antes de volver a pedir usuario
TIEMPO_INACTIVIDAD = 5 * 60     # 5 minutos sin cambios en pantalla (segundos)
INTERVALO_REVISION_MS = 2000    # cada cuánto se compara la pantalla
ESPERA_BASE_MS = 3000           # tras clickear start, esperar antes de tomar la imagen base

CONFIANZA_BOTON = 0.8           # 0 a 1, qué tan parecida debe ser la imagen del botón

# Región de pantalla a vigilar: (x, y, ancho, alto). None = pantalla completa.
# Recomendado: acotarla al área de los indicadores para ignorar el reloj de Windows, etc.
REGION_MONITOREO = None

# Sensibilidad de detección de cambios
UMBRAL_PIXEL = 25               # diferencia de brillo (0-255) para considerar que un píxel cambió
UMBRAL_CAMBIO = 0.0005          # fracción de píxeles que deben cambiar (0.05%)


# ------------------------------------------------------------
# Log a archivo (con --noconsole no hay dónde ver los print)
# ------------------------------------------------------------
log = logging.getLogger("safetyguard")
log.setLevel(logging.INFO)
try:
    _handler = logging.handlers.RotatingFileHandler(
        ARCHIVO_LOG, maxBytes=200000, backupCount=2, encoding="utf-8"
    )
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(_handler)
except Exception:
    log.addHandler(logging.NullHandler())


# ------------------------------------------------------------
# Instancia única (evita dos ventanas de bloqueo a la vez)
# ------------------------------------------------------------
try:
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _mutex = _kernel32.CreateMutexW(None, False, "SafetyGuard_Mutex")
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        log.warning("Ya hay otra instancia en ejecución. Saliendo.")
        sys.exit(0)
except SystemExit:
    raise
except Exception:
    pass


# ------------------------------------------------------------
# Estado
# ------------------------------------------------------------
estado = {
    "monitoreando": False,
    "frame_anterior": None,
    "ultimo_cambio": time.monotonic(),
}


# ------------------------------------------------------------
# Mouse virtual
# ------------------------------------------------------------
def clickear_boton(ruta_imagen):
    """Busca la imagen en pantalla y hace click. Devuelve True si lo encontró."""
    nombre = os.path.basename(ruta_imagen)

    if not os.path.exists(ruta_imagen):
        log.warning("No existe el archivo: %s", ruta_imagen)
        return False

    try:
        try:
            pos = pyautogui.locateCenterOnScreen(ruta_imagen, confidence=CONFIANZA_BOTON)
        except NotImplementedError:
            # sin OpenCV no existe 'confidence'
            pos = pyautogui.locateCenterOnScreen(ruta_imagen)
    except Exception:
        # En versiones nuevas, "no encontrado" lanza ImageNotFoundException
        pos = None

    if pos is None:
        log.info("Botón no encontrado: %s", nombre)
        return False

    try:
        # Mover primero y esperar un instante: algunas páginas web
        # necesitan el "hover" antes de aceptar el click.
        pyautogui.moveTo(pos.x, pos.y, duration=0.3)
        time.sleep(0.2)
        pyautogui.click()
        log.info("Click en %s (%s, %s)", nombre, pos.x, pos.y)
        return True
    except Exception:
        log.exception("Error al hacer click en %s", nombre)
        return False


# ------------------------------------------------------------
# Detección de cambios en pantalla
# ------------------------------------------------------------
def capturar_frame():
    img = pyautogui.screenshot(region=REGION_MONITOREO).convert("L")
    # reducir para que sea rápido y menos sensible al ruido
    img = img.resize((max(1, img.width // 4), max(1, img.height // 4)))
    return np.asarray(img, dtype=np.int16)


def hay_cambio(frame_a, frame_b):
    if frame_a.shape != frame_b.shape:
        return True
    diff = np.abs(frame_a - frame_b) > UMBRAL_PIXEL
    return diff.mean() > UMBRAL_CAMBIO


def revisar_pantalla():
    if not estado["monitoreando"]:
        return

    try:
        frame = capturar_frame()
        if estado["frame_anterior"] is not None and hay_cambio(estado["frame_anterior"], frame):
            estado["ultimo_cambio"] = time.monotonic()
        estado["frame_anterior"] = frame
    except Exception:
        log.exception("Error al capturar la pantalla")

    if time.monotonic() - estado["ultimo_cambio"] >= TIEMPO_INACTIVIDAD:
        iniciar_bloqueo()
    else:
        root.after(INTERVALO_REVISION_MS, revisar_pantalla)


def iniciar_monitoreo():
    if estado["monitoreando"]:
        return  # evita arrancar dos ciclos de revisión
    estado["frame_anterior"] = None
    estado["ultimo_cambio"] = time.monotonic()
    estado["monitoreando"] = True
    log.info("Monitoreo de pantalla iniciado")
    root.after(INTERVALO_REVISION_MS, revisar_pantalla)


# ------------------------------------------------------------
# Flujo de bloqueo / desbloqueo
# ------------------------------------------------------------
def iniciar_bloqueo():
    """Inactividad detectada: click en STOP y, 1 s después, pedir usuario."""
    estado["monitoreando"] = False
    log.info("Inactividad detectada: bloqueando")
    try:
        clickear_boton(IMG_STOP)
    finally:
        # Pase lo que pase con el click, siempre se vuelve a bloquear
        root.after(ESPERA_CLICK_MS, mostrar_bloqueo)


def mostrar_bloqueo():
    entry_usuario.delete(0, tk.END)
    root.deiconify()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.lift()
    root.focus_force()
    entry_usuario.focus_set()


def validar():
    usuario = entry_usuario.get().strip()

    # Por ahora se acepta cualquier usuario (solo se exige que no esté vacío).
    # Si querés aceptar incluso vacío, borrá este if.
    if not usuario:
        return

    log.info("Login: %s", usuario)
    root.withdraw()
    root.after(ESPERA_CLICK_MS, despues_de_desbloquear)


def despues_de_desbloquear():
    clickear_boton(IMG_START)
    # Esperar a que la pantalla se estabilice y recién ahí tomar la imagen base
    root.after(ESPERA_BASE_MS, iniciar_monitoreo)


# ------------------------------------------------------------
# Ventana principal
# ------------------------------------------------------------
root = tk.Tk()
root.title("Login Locker")
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg="black")
root.protocol("WM_DELETE_WINDOW", lambda: None)


def _error_tk(exc, val, tb):
    log.error("Error no controlado", exc_info=(exc, val, tb))


root.report_callback_exception = _error_tk

frame = tk.Frame(root, bg="black")
frame.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(
    frame, text="MÁQUINA BLOQUEADA",
    font=("Arial", 32, "bold"), fg="white", bg="black"
).pack(pady=20)

tk.Label(
    frame, text="Usuario",
    font=("Arial", 14), fg="white", bg="black"
).pack()

entry_usuario = tk.Entry(frame, font=("Arial", 14), width=25)
entry_usuario.pack(pady=10)

tk.Button(
    frame, text="Desbloquear", command=validar,
    font=("Arial", 14), width=20
).pack(pady=20)

root.bind("<Return>", lambda event: validar())

log.info("SafetyGuard iniciado")
entry_usuario.focus_set()
root.mainloop()