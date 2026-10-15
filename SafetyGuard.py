import os
import sys
import time
import ctypes
import tkinter as tk

import numpy as np
import pyautogui

# ------------------------------------------------------------
# Windows: evita que el escalado de pantalla (DPI) desfase los clicks
# ------------------------------------------------------------
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

pyautogui.FAILSAFE = False  # la máquina no tiene mouse físico, no hace falta

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
CARPETA = os.path.dirname(os.path.abspath(sys.argv[0]))
IMG_START = os.path.join(CARPETA, "start.jpg")
IMG_STOP = os.path.join(CARPETA, "stop.jpg")

ESPERA_CLICK_MS = 1000          # 1 segundo antes de clickear start / antes de volver a pedir usuario
TIEMPO_INACTIVIDAD = 5 #* 60     # 5 minutos sin cambios en pantalla (segundos)
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
# Estado
# ------------------------------------------------------------
estado = {
    "monitoreando": False,
    "frame_anterior": None,
    "ultimo_cambio": time.time(),
}


# ------------------------------------------------------------
# Mouse virtual
# ------------------------------------------------------------
def clickear_boton(ruta_imagen):
    """Busca la imagen en pantalla y hace click. Devuelve True si lo encontró."""
    if not os.path.exists(ruta_imagen):
        print(f"[AVISO] No existe el archivo: {ruta_imagen}")
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
        print(f"[INFO] Botón no encontrado: {os.path.basename(ruta_imagen)}")
        return False

    pyautogui.click(pos.x, pos.y)
    print(f"[OK] Click en {os.path.basename(ruta_imagen)} ({pos.x}, {pos.y})")
    return True


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
            estado["ultimo_cambio"] = time.time()
        estado["frame_anterior"] = frame
    except Exception as e:
        print(f"[ERROR] Captura de pantalla: {e}")

    if time.time() - estado["ultimo_cambio"] >= TIEMPO_INACTIVIDAD:
        iniciar_bloqueo()
    else:
        root.after(INTERVALO_REVISION_MS, revisar_pantalla)


def iniciar_monitoreo():
    estado["frame_anterior"] = None
    estado["ultimo_cambio"] = time.time()
    estado["monitoreando"] = True
    root.after(INTERVALO_REVISION_MS, revisar_pantalla)


# ------------------------------------------------------------
# Flujo de bloqueo / desbloqueo
# ------------------------------------------------------------
def iniciar_bloqueo():
    """Inactividad detectada: click en STOP y, 1 s después, pedir usuario."""
    estado["monitoreando"] = False
    clickear_boton(IMG_STOP)
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

    print(f"[LOGIN] Usuario: {usuario}")
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

entry_usuario.focus_set()
root.mainloop()