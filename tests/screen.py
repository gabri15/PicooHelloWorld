import base64
import time
import requests
import json
import os
import re

# QR deps
try:
    import qrcode
except ImportError:
    raise SystemExit("Falta 'qrcode'. Instala: pip3 install qrcode[pil] pillow")

PIXOO_IP = "192.168.0.21"
URL = f"http://{PIXOO_IP}/post"
W, H = 64, 64

# =========================
# CONFIG QR
# =========================
QR_URL = "https://produccioncientifica.usal.es/investigadores/57921/detalle"
TITLE_QR = "CONTACTO"

# ==========================================================
# LECTURA DE all-results.json (estructura fija)
# ==========================================================
RESULTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "all-results.json")

def load_all_results(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _to_int(v, default=0):
    try:
        if v is None:
            return default
        return int(v)
    except:
        return default

def _sum_y(items) -> int:
    if not items:
        return 0
    total = 0
    for it in items:
        total += _to_int((it or {}).get("y", 0), 0)
    return total

def money_to_int(v) -> int:
    if v is None:
        return 0
    s = str(v).strip()
    s2 = re.sub(r"[^0-9,.\-]", "", s)

    # US: 2,695,566.00
    try:
        f = float(s2.replace(",", ""))
        return int(round(f))
    except:
        pass

    # ES: 2.695.566,00
    try:
        f = float(s2.replace(".", "").replace(",", "."))
        return int(round(f))
    except:
        pass

    digits = re.sub(r"[^0-9]", "", s2)
    return int(digits) if digits else 0

def format_thousands(n: int) -> str:
    s = str(max(0, int(n)))
    parts = []
    while s:
        parts.append(s[-3:])
        s = s[:-3]
    return ".".join(reversed(parts)) if parts else "0"

def load_quartiles_from_results(data: dict) -> dict:
    la = data.get("tests", {}).get("login-automatico", {})
    quartiles_list = la.get("publicationsByJIFQuartiles", []) or []

    q = {}
    for item in quartiles_list:
        k = (item.get("key") or item.get("name") or "").strip().upper()
        if k in ("Q1", "Q2", "Q3", "Q4"):
            q[k] = _to_int(item.get("y", 0), 0)

    for kk in ("Q1", "Q2", "Q3", "Q4"):
        q.setdefault(kk, 0)

    return q

def load_direcciones_from_results(data: dict) -> dict:
    tests = data.get("tests", {})
    la = tests.get("login-automatico", {})

    supervised = _to_int(la.get("supervisedTheses", 0), 0)
    tfm = _to_int(la.get("tfmSupervisadas", 0), 0)
    pract = _to_int(la.get("practicasSupervisadas", 0), 0)

    rec_tfg = tests.get("recuperacion-tfg", []) or []
    tfg_total = 0
    for item in rec_tfg:
        tfg_total += _to_int(item.get("count", 0), 0)

    return {"TFG": tfg_total, "TFM": tfm, "TESIS": supervised, "PRAC": pract}

def load_ip_proyectos_from_results(data: dict) -> dict:
    la = data.get("tests", {}).get("login-automatico", {})
    p = la.get("projectsByType", {}) or {}
    return {
        "NAC":  _to_int(p.get("ipNacionales", 0), 0),
        "REG":  _to_int(p.get("ipRegionales", 0), 0),
        "INDO": _to_int(p.get("ipInnovacionDocente", 0), 0),
        "OTRO": _to_int(p.get("otros", 0), 0),
    }

def load_curso_docente_from_results(data: dict) -> dict:
    la = data.get("tests", {}).get("login-automatico", {})
    return {
        "IMPARTIDOS": _to_int(la.get("cursosdocentesImpartidos", 0), 0),
        "RECIBIDOS":  _to_int(la.get("cursosdocentesRecibidos", 0), 0),
    }

def load_registros_from_results(data: dict) -> dict:
    la = data.get("tests", {}).get("login-automatico", {})
    return {
        "PATENTES":     _to_int(la.get("patentes", 0), 0),
        "PROPIEDADES":  _to_int(la.get("registrosDeUtilidad", 0), 0),
    }

def load_resumen_from_results(data: dict) -> dict:
    la = data.get("tests", {}).get("login-automatico", {})

    p = la.get("projectsByType", {}) or {}
    proyectos_total = (
        _to_int(p.get("ipNacionales", 0), 0) +
        _to_int(p.get("ipRegionales", 0), 0) +
        _to_int(p.get("ipInnovacionDocente", 0), 0) +
        _to_int(p.get("otros", 0), 0)
    )

    publication_types = la.get("publicationTypes", []) or []
    quartiles = la.get("publicationsByJIFQuartiles", []) or []
    publicaciones_total = _sum_y(publication_types) + _sum_y(quartiles)

    return {"PROYECTOS": proyectos_total, "PUBLICACIONES": publicaciones_total}

def load_pro_oficiales_from_results(data: dict) -> dict:
    la = data.get("tests", {}).get("login-automatico", {})
    funding = la.get("funding", {}) or {}
    total_projects = _to_int(funding.get("totalProjects", 0), 0)
    total_money_int = money_to_int(funding.get("totalMoney", "0"))
    return {"PROYECTOS": total_projects, "FINANCIACION": total_money_int}

# ==========================================================
# Pantallas (defaults -> se sobrescriben con JSON)
# ==========================================================
TITLE_1  = "PUBLICACIONES"
COUNTERS_1  = [("Q1", 20), ("Q2", 12), ("Q3", 5), ("Q4", 8)]

TITLE_1B = "DIRECCIONES"
COUNTERS_1B = [("TFG", 20), ("TFM", 12), ("TESIS", 5), ("PRAC", 8)]

TITLE_1C = "IP. PROYECTOS"
COUNTERS_1C = [("NAC", 20), ("REG", 12), ("INDO", 5), ("OTRO", 8)]

TITLE_1D = "CURSO DOCENTE"
COUNTERS_1D = [("IMPARTIDOS", 31), ("RECIBIDOS", 40)]

TITLE_1E = "REGISTROS"
COUNTERS_1E = [("PATENTES", 31), ("PROPIEDADES", 40)]

TITLE_1F = "RESUMEN"
COUNTERS_1F = [("PROYECTOS", 31), ("PUBLICACIONES", 40)]

TITLE_1G = "PRO. OFICIALES"
COUNTERS_1G = [("PROYECTOS", 0), ("FINANCIACION", 0)]

# ---- Sobrescribir desde JSON ----
try:
    results = load_all_results(RESULTS_JSON_PATH)

    qvals = load_quartiles_from_results(results)
    COUNTERS_1 = [("Q1", qvals["Q1"]), ("Q2", qvals["Q2"]), ("Q3", qvals["Q3"]), ("Q4", qvals["Q4"])]

    dvals = load_direcciones_from_results(results)
    COUNTERS_1B = [("TFG", dvals["TFG"]), ("TFM", dvals["TFM"]), ("TESIS", dvals["TESIS"]), ("PRAC", dvals["PRAC"])]

    ipvals = load_ip_proyectos_from_results(results)
    COUNTERS_1C = [("NAC", ipvals["NAC"]), ("REG", ipvals["REG"]), ("INDO", ipvals["INDO"]), ("OTRO", ipvals["OTRO"])]

    cvals = load_curso_docente_from_results(results)
    COUNTERS_1D = [("IMPARTIDOS", cvals["IMPARTIDOS"]), ("RECIBIDOS", cvals["RECIBIDOS"])]

    rvals = load_registros_from_results(results)
    COUNTERS_1E = [("PATENTES", rvals["PATENTES"]), ("PROPIEDADES", rvals["PROPIEDADES"])]

    svals = load_resumen_from_results(results)
    COUNTERS_1F = [("PROYECTOS", svals["PROYECTOS"]), ("PUBLICACIONES", svals["PUBLICACIONES"])]

    povals = load_pro_oficiales_from_results(results)
    COUNTERS_1G = [("PROYECTOS", povals["PROYECTOS"]), ("FINANCIACION", povals["FINANCIACION"])]

    print(f"✅ JSON cargado: {RESULTS_JSON_PATH}")
except Exception as e:
    print(f"⚠️ No pude leer {RESULTS_JSON_PATH}. Uso valores por defecto. Error: {e}")

# ==========================================================
# Estilo
# ==========================================================
BG = (6, 4, 20)
GRID = (10, 10, 30)
CYAN = (0, 220, 255)
CYAN_DIM = (0, 120, 150)
WHITE = (230, 235, 255)
CARD_BG = (8, 6, 26)
CARD_BG2 = (10, 8, 34)

GOLD = (240, 200, 90)
SILVER = (220, 220, 230)
BRONZE = (200, 140, 90)
GRAY = (140, 150, 160)

# Colores QR (alto contraste)
QR_BG = (240, 245, 255)
QR_FG = (10, 12, 20)

# ==========================================================
# TIMING (el que te funcionaba bien)
# ==========================================================
FRAME_MS = 1900
FRAMES_PER_SCREEN = 6

COUNTUP_FRAMES = 2
HOLD_FRAMES = 4
assert COUNTUP_FRAMES + HOLD_FRAMES == FRAMES_PER_SCREEN

EXTRA_FRAMES_2BOX = 0
SEND_SLEEP = 0.06

session = requests.Session()

def post(payload, retries=4):
    for _ in range(retries):
        try:
            r = session.post(URL, json=payload, timeout=6)
            r.raise_for_status()
            return
        except:
            time.sleep(0.2)
    raise RuntimeError("Error enviando datos al Pixoo")

def new_frame(rgb=BG):
    buf = bytearray(W * H * 3)
    for i in range(0, len(buf), 3):
        buf[i], buf[i+1], buf[i+2] = rgb
    return buf

def set_px(f, x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        i = (y*W + x)*3
        f[i], f[i+1], f[i+2] = rgb

def hline(f, x0, x1, y, rgb):
    for x in range(x0, x1+1):
        set_px(f, x, y, rgb)

def vline(f, x, y0, y1, rgb):
    for y in range(y0, y1+1):
        set_px(f, x, y, rgb)

def rect_outline(f, x0, y0, w, h, rgb):
    hline(f, x0, x0+w-1, y0, rgb)
    hline(f, x0, x0+w-1, y0+h-1, rgb)
    vline(f, x0, y0, y0+h-1, rgb)
    vline(f, x0+w-1, y0, y0+h-1, rgb)

def fill_rect(f, x0, y0, w, h, rgb):
    for yy in range(y0, y0+h):
        for xx in range(x0, x0+w):
            set_px(f, xx, yy, rgb)

def glow_box(f, x, y, w, h):
    rect_outline(f, x, y, w, h, CYAN)
    rect_outline(f, x-1, y-1, w+2, h+2, CYAN_DIM)

def draw_grid(f, phase=0):
    for y in range(H):
        if (y+phase) % 8 == 0:
            hline(f, 0, W-1, y, GRID)
    for x in range(W):
        if (x+phase) % 8 == 0:
            vline(f, x, 0, H-1, GRID)

# -------- FUENTES --------
FONT_MINI = {
    "A":["0110","1010","1110","1010","1010"],
    "B":["1100","1010","1100","1010","1100"],
    "C":["1110","1000","1000","1000","1110"],
    "D":["1100","1010","1010","1010","1100"],
    "E":["1110","1000","1100","1000","1110"],
    "F":["1110","1000","1100","1000","1000"],
    "G":["1110","1000","1010","1010","1110"],
    "I":["1110","0100","0100","0100","1110"],
    "L":["1000","1000","1000","1000","1110"],
    "M":["1010","1110","1110","1010","1010"],
    "N":["1010","1110","1110","1010","1010"],
    "O":["1110","1010","1010","1010","1110"],
    "P":["1110","1010","1110","1000","1000"],
    "Q":["1110","1010","1010","1110","0010"],
    "R":["1110","1010","1110","1010","1010"],
    "S":["1110","1000","1110","0010","1110"],
    "T":["1110","0100","0100","0100","0100"],
    "U":["1010","1010","1010","1010","1110"],
    "Y":["1010","1010","0100","0100","0100"],
    ".":["0000","0000","0000","0000","0100"],
    "0":["1110","1010","1010","1010","1110"],
    "1":["0100","1100","0100","0100","1110"],
    "2":["1110","0010","1110","1000","1110"],
    "3":["1110","0010","1110","0010","1110"],
    "4":["1010","1010","1110","0010","0010"],
    "5":["1110","1000","1110","0010","1110"],
    "6":["1110","1000","1110","1010","1110"],
    "7":["1110","0010","0100","0100","0100"],
    "8":["1110","1010","1110","1010","1110"],
    "9":["1110","1010","1110","0010","1110"],
    " ":["0000","0000","0000","0000","0000"],
}

def draw_char_mini(f, x, y, ch, col):
    g = FONT_MINI.get(ch.upper(), FONT_MINI[" "])
    for yy, row in enumerate(g):
        for xx, c in enumerate(row):
            if c == "1":
                set_px(f, x+xx, y+yy, col)

def draw_centered_text_mini(f, cx, y, s, col):
    w = len(s) * 4
    x = cx - w // 2
    for ch in s:
        draw_char_mini(f, x, y, ch, col)
        x += 4

FONT_TITLE = {
    "A":["1110","1010","1110","1010","1010"],
    "B":["1100","1010","1100","1010","1100"],
    "C":["1110","1000","1000","1000","1110"],
    "D":["1100","1010","1010","1010","1100"],
    "E":["1110","1000","1100","1000","1110"],
    "F":["1110","1000","1100","1000","1000"],
    "G":["1110","1000","1010","1010","1110"],
    "I":["1110","0100","0100","0100","1110"],
    "L":["1000","1000","1000","1000","1110"],
    "M":["1010","1110","1110","1010","1010"],
    "N":["1010","1110","1110","1010","1010"],
    "O":["1110","1010","1010","1010","1110"],
    "P":["1110","1010","1110","1000","1000"],
    "R":["1110","1010","1110","1010","1010"],
    "S":["1110","1000","1110","0010","1110"],
    "T":["1110","0100","0100","0100","0100"],
    "U":["1010","1010","1010","1010","1110"],
    "Y":["1010","1010","0100","0100","0100"],
    ".":["0000","0000","0000","0000","0100"],
    " ":["0000","0000","0000","0000","0000"],
}

def draw_char_title(f, x, y, ch, col):
    g = FONT_TITLE.get(ch.upper(), FONT_TITLE[" "])
    for yy, row in enumerate(g):
        for xx, c in enumerate(row):
            if c == "1":
                set_px(f, x+xx, y+yy, col)

def draw_centered_title(f, cx, y, s, col):
    w = len(s) * 4
    x = cx - w // 2
    for ch in s:
        draw_char_title(f, x, y, ch, col)
        x += 4

def draw_common_frame(f, phase, title):
    draw_grid(f, phase)
    rect_outline(f, 1, 1, 62, 62, CYAN)
    rect_outline(f, 3, 3, 58, 58, CYAN_DIM)
    draw_centered_title(f, 32, 8, title, WHITE)
    hline(f, 20, 44, 16, CYAN)

def draw_box_interior(f, x, y, w, h):
    for yy in range(y+1, y+h-1):
        for xx in range(x+1, x+w-1):
            set_px(f, xx, yy, CARD_BG if (xx+yy) % 2 == 0 else CARD_BG2)

def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)

def countup_value(final_val: int, frame: int) -> int:
    if frame >= COUNTUP_FRAMES - 1:
        return int(final_val)
    t = (frame + 1) / COUNTUP_FRAMES
    return max(1, int(int(final_val) * ease_out_quad(t)))

def format_value(label: str, value_int: int) -> str:
    if label.upper() == "FINANCIACION":
        return format_thousands(value_int)
    return str(value_int)

# =========================
# Builders pantallas
# =========================
def build_publicaciones(phase, frame):
    f = new_frame()
    draw_common_frame(f, phase, TITLE_1)
    boxes = [
        (12, 21, 18, 18, GOLD),
        (34, 21, 18, 18, SILVER),
        (12, 41, 18, 18, BRONZE),
        (34, 41, 18, 18, GRAY),
    ]
    for i, (x, y, w, h, col) in enumerate(boxes):
        draw_box_interior(f, x, y, w, h)
        glow_box(f, x, y, w, h)
        draw_centered_text_mini(f, x+w//2, y+3, COUNTERS_1[i][0], col)
        v = countup_value(_to_int(COUNTERS_1[i][1], 0), frame)
        draw_centered_text_mini(f, x+w//2, y+10, str(v), col)
    return f

def build_4boxes_wide(title, counters, phase, frame):
    f = new_frame()
    draw_common_frame(f, phase, title)
    boxes = [
        (6, 21, 24, 18, GOLD),
        (34, 21, 24, 18, SILVER),
        (6, 41, 24, 18, BRONZE),
        (34, 41, 24, 18, GRAY),
    ]
    for i, (x, y, w, h, col) in enumerate(boxes):
        draw_box_interior(f, x, y, w, h)
        glow_box(f, x, y, w, h)
        draw_centered_text_mini(f, x+w//2, y+3, counters[i][0], col)
        v = countup_value(_to_int(counters[i][1], 0), frame)
        draw_centered_text_mini(f, x+w//2, y+10, str(v), col)
    return f

def build_2boxes_custom(title, counters, phase, frame, y_top, y_bottom, color_top, color_bottom):
    f = new_frame()
    draw_common_frame(f, phase, title)
    boxes = [
        (6, y_top,    52, 18, color_top),
        (6, y_bottom, 52, 18, color_bottom),
    ]
    for i, (x, y, w, h, col) in enumerate(boxes):
        draw_box_interior(f, x, y, w, h)
        glow_box(f, x, y, w, h)
        label = counters[i][0]
        final_v = _to_int(counters[i][1], 0)
        v = countup_value(final_v, frame)
        draw_centered_text_mini(f, x+w//2, y+4, label, col)
        draw_centered_text_mini(f, x+w//2, y+11, format_value(label, v), col)
    return f

# =========================
# QR SCREEN (centrado total)
# =========================
def qr_matrix(data: str):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=2,  # quiet zone importante
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.get_matrix()

def draw_qr_centered_full(f, data: str):
    """
    QR centrado y grande ocupando prácticamente el centro de la pantalla,
    sin caja extra (para que sea lo más grande posible) pero manteniendo
    el marco exterior y el título como el resto.
    """
    m = qr_matrix(data)
    n = len(m)

    # Área útil bajo el título: y=18..61 (44 px)
    # y arriba del todo está el título y línea
    x0, y0, size = 8, 18, 48  # cuadrado grande centrado en pantalla
    # Fondo claro para escaneo
    fill_rect(f, x0, y0, size, size, QR_BG)

    # Escalado entero para encajar
    scale = max(1, size // n)
    draw_size = n * scale
    ox = x0 + (size - draw_size) // 2
    oy = y0 + (size - draw_size) // 2

    # dibujar módulos
    for yy in range(n):
        for xx in range(n):
            if m[yy][xx]:
                for sy in range(scale):
                    for sx in range(scale):
                        set_px(f, ox + xx*scale + sx, oy + yy*scale + sy, QR_FG)

    # Marco glow (estética igual)
    glow_box(f, x0, y0, size, size)

def build_qr_screen(phase, frame):
    f = new_frame()
    draw_common_frame(f, phase, TITLE_QR)
    draw_qr_centered_full(f, QR_URL)
    return f

# =========================
# Envío
# =========================
def send_http_gif(frames):
    post({"Command": "Channel/SetIndex", "SelectIndex": 3})
    post({"Command": "Draw/ClearHttpText"})
    post({"Command": "Draw/ResetHttpGifId"})
    for i, fr in enumerate(frames):
        post({
            "Command": "Draw/SendHttpGif",
            "PicNum": len(frames),
            "PicWidth": 64,
            "PicOffset": i,
            "PicID": 1,
            "PicSpeed": FRAME_MS,
            "PicData": base64.b64encode(bytes(fr)).decode()
        })
        time.sleep(SEND_SLEEP)

if __name__ == "__main__":
    frames = []

    # 1) PUBLICACIONES
    for i in range(FRAMES_PER_SCREEN):
        frames.append(build_publicaciones(i % 2, i))

    # 2) DIRECCIONES
    for i in range(FRAMES_PER_SCREEN):
        frames.append(build_4boxes_wide(TITLE_1B, COUNTERS_1B, i % 2, i))

    # 3) IP. PROYECTOS
    for i in range(FRAMES_PER_SCREEN):
        frames.append(build_4boxes_wide(TITLE_1C, COUNTERS_1C, i % 2, i))

    def add_2box_screen(title, counters, y_top, y_bottom, color_top, color_bottom):
        for i in range(FRAMES_PER_SCREEN + EXTRA_FRAMES_2BOX):
            fr = min(i, FRAMES_PER_SCREEN - 1)
            frames.append(build_2boxes_custom(title, counters, i % 2, fr, y_top, y_bottom, color_top, color_bottom))

    # 4) CURSO DOCENTE
    add_2box_screen(TITLE_1D, COUNTERS_1D, y_top=18, y_bottom=39, color_top=GOLD, color_bottom=SILVER)

    # 5) REGISTROS
    add_2box_screen(TITLE_1E, COUNTERS_1E, y_top=18, y_bottom=40, color_top=SILVER, color_bottom=BRONZE)

    # 6) RESUMEN
    add_2box_screen(TITLE_1F, COUNTERS_1F, y_top=18, y_bottom=39, color_top=GOLD, color_bottom=SILVER)

    # 7) PRO. OFICIALES
    add_2box_screen(TITLE_1G, COUNTERS_1G, y_top=18, y_bottom=39, color_top=GOLD, color_bottom=SILVER)

    # 8) CONTACTO (QR)
    for i in range(FRAMES_PER_SCREEN):
        frames.append(build_qr_screen(i % 2, i))

    print(f"Total frames enviados: {len(frames)}")
    send_http_gif(frames)
    print("OK: QR CONTACTO centrado a URL de Producción Científica.")
