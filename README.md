# SafetyGuard

🇬🇧 [English](#english) · 🇪🇸 [Español](#español)

---

<a name="english"></a>
## 🇬🇧 English

Screen-lock and virtual-mouse tool for machines supervised through a browser on a Windows PC **with no physical mouse or keyboard**.

A full-screen lock asks for a username. Once unlocked, SafetyGuard automatically clicks the **Start** button on screen. If the screen shows no changes for 5 minutes (the operator is away), it clicks **Stop** and locks again.

### How it works

1. On launch, a full-screen lock window asks for a **username only** (no password). For now, any non-empty username is accepted.
2. After unlocking, the window disappears and, 1 second later, the virtual mouse clicks the button matching `start.jpg`.
3. A few seconds later, SafetyGuard takes a baseline screenshot and compares the screen every 2 seconds.
4. If there are no visual changes for 5 minutes, it clicks the button matching `stop.jpg` and, 1 second later, shows the lock screen again.
5. If a button image is not found on screen, the logic simply continues.

### Requirements

- Windows
- Python 3.8+

```bash
pip install -r requirements.txt
```

`requirements.txt`:
```
pyautogui
pillow
opencv-python
numpy
```

### Usage

1. Put `start.jpg` and `stop.jpg` in the same folder as `SafetyGuard.py`. They must be **exact screenshot crops** of the buttons, taken on the target machine at the same resolution and display scaling.
2. Run:
   ```bash
   python SafetyGuard.py
   ```

### Configuration

Edit the constants at the top of `SafetyGuard.py`:

| Constant | Default | Description |
|---|---|---|
| `ESPERA_CLICK_MS` | `1000` | Delay (ms) before clicking Start / before showing the lock after Stop |
| `TIEMPO_INACTIVIDAD` | `300` | Seconds without screen changes before locking |
| `INTERVALO_REVISION_MS` | `2000` | How often the screen is compared (ms) |
| `ESPERA_BASE_MS` | `3000` | Wait after clicking Start before taking the baseline image (ms) |
| `CONFIANZA_BOTON` | `0.8` | Image match tolerance, 0–1 |
| `REGION_MONITOREO` | `None` | `(x, y, width, height)` area to watch. `None` = full screen |
| `UMBRAL_PIXEL` | `25` | Brightness difference (0–255) for a pixel to count as changed |
| `UMBRAL_CAMBIO` | `0.0005` | Fraction of pixels that must change to count as activity |

### Build an executable

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name SafetyGuard SafetyGuard.py
```

Copy `start.jpg` and `stop.jpg` next to `dist\SafetyGuard.exe`:

```
dist\
 ├── SafetyGuard.exe
 ├── start.jpg
 └── stop.jpg
```

To start with Windows, press `Win + R`, type `shell:startup` and drop a shortcut to the `.exe` there.

> Build without `--noconsole` if you need to see log messages (clicks, "button not found").

### Notes and limitations

- **Constant on-screen changes** (Windows clock, live charts) prevent inactivity detection. Use `REGION_MONITOREO` to watch only the indicators area.
- **Sensitivity:** if it locks while there's still activity, lower `UMBRAL_PIXEL` / `UMBRAL_CAMBIO`. If it never locks due to screen noise, raise them.
- **No keyboard:** you need some way to enter the username (on-screen keyboard, badge reader, etc.).
- **Security:** this is a Python window, **not** an OS-level lock. Alt+Tab, Ctrl+Alt+Del or an attached keyboard can bypass it. For serious use, combine it with Windows kiosk mode.
- Antivirus software may flag PyInstaller executables that control the mouse; add an exception if needed.

---

<a name="español"></a>
## 🇪🇸 Español

Herramienta de bloqueo de pantalla y mouse virtual para máquinas supervisadas desde el navegador de una PC con Windows **sin mouse ni teclado físicos**.

Un bloqueo a pantalla completa pide un usuario. Al desbloquear, SafetyGuard hace click automáticamente en el botón **Start** de la pantalla. Si la pantalla no muestra cambios durante 5 minutos (el operador se ausentó), hace click en **Stop** y vuelve a bloquear.

### Cómo funciona

1. Al ejecutarlo, aparece una ventana de bloqueo a pantalla completa que pide **solo usuario** (sin contraseña). Por ahora se acepta cualquier usuario no vacío.
2. Al desbloquear, la ventana desaparece y, 1 segundo después, el mouse virtual hace click en el botón que coincide con `start.jpg`.
3. Unos segundos más tarde toma una captura base y compara la pantalla cada 2 segundos.
4. Si no hay cambios visuales durante 5 minutos, hace click en el botón de `stop.jpg` y, 1 segundo después, vuelve a mostrar el bloqueo.
5. Si no encuentra la imagen de un botón en pantalla, la lógica sigue normalmente.

### Requisitos

- Windows
- Python 3.8+

```bash
pip install -r requirements.txt
```

`requirements.txt`:
```
pyautogui
pillow
opencv-python
numpy
```

### Uso

1. Colocá `start.jpg` y `stop.jpg` en la misma carpeta que `SafetyGuard.py`. Deben ser **recortes exactos** de los botones, tomados en la máquina de destino, con la misma resolución y escalado de pantalla.
2. Ejecutá:
   ```bash
   python SafetyGuard.py
   ```

### Configuración

Editá las constantes al inicio de `SafetyGuard.py`:

| Constante | Valor por defecto | Descripción |
|---|---|---|
| `ESPERA_CLICK_MS` | `1000` | Demora (ms) antes de clickear Start / antes de mostrar el bloqueo tras Stop |
| `TIEMPO_INACTIVIDAD` | `300` | Segundos sin cambios en pantalla antes de bloquear |
| `INTERVALO_REVISION_MS` | `2000` | Cada cuánto se compara la pantalla (ms) |
| `ESPERA_BASE_MS` | `3000` | Espera tras clickear Start antes de tomar la imagen base (ms) |
| `CONFIANZA_BOTON` | `0.8` | Tolerancia de coincidencia de imagen, de 0 a 1 |
| `REGION_MONITOREO` | `None` | Área a vigilar `(x, y, ancho, alto)`. `None` = pantalla completa |
| `UMBRAL_PIXEL` | `25` | Diferencia de brillo (0–255) para considerar que un píxel cambió |
| `UMBRAL_CAMBIO` | `0.0005` | Fracción de píxeles que deben cambiar para contar como actividad |

### Generar un ejecutable

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name SafetyGuard SafetyGuard.py
```

Copiá `start.jpg` y `stop.jpg` junto a `dist\SafetyGuard.exe`:

```
dist\
 ├── SafetyGuard.exe
 ├── start.jpg
 └── stop.jpg
```

Para que arranque con Windows, apretá `Win + R`, escribí `shell:startup` y pegá ahí un acceso directo al `.exe`.

> Compilá sin `--noconsole` si necesitás ver los mensajes (clicks, "botón no encontrado").

### Notas y limitaciones

- **Cambios constantes en pantalla** (reloj de Windows, gráficos en vivo) impiden detectar la inactividad. Usá `REGION_MONITOREO` para vigilar solo el área de los indicadores.
- **Sensibilidad:** si bloquea cuando todavía hay actividad, bajá `UMBRAL_PIXEL` / `UMBRAL_CAMBIO`. Si nunca bloquea por ruido de pantalla, subilos.
- **Sin teclado:** necesitás algún medio para ingresar el usuario (teclado en pantalla, lector de credencial, etc.).
- **Seguridad:** es una ventana de Python, **no** un bloqueo a nivel del sistema operativo. Alt+Tab, Ctrl+Alt+Supr o un teclado conectado pueden saltearlo. Para uso serio, combinalo con el modo quiosco de Windows.
- Algunos antivirus pueden marcar los ejecutables de PyInstaller que controlan el mouse; agregá una excepción si hace falta.
