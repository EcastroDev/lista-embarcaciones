import streamlit as st
import pandas as pd
import gdown
import zipfile
import os
import glob

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN — estructura exacta de cada Excel verificada
# ═══════════════════════════════════════════════════════════════════════════════
ZIP_FILE_ID   = "1-buA01ayUVId3zs5sbM-O_FJDPplsumq"
ZIP_LOCAL     = "listas_embarcaciones.zip"
CARPETA_DATOS = "listas_embarcaciones"

RECURSOS = {
    "🐟 BONITO": {
        "nombre":      "Bonito (Sarda chiliensis chiliensis)",
        "archivo":     "Bonito.xlsx",
        "header_row":  4,           # filas 0-3 son título/vacío
        "col_mat":     "MATRICULA",
        "col_nom":     "EMBARCACIÓN",
        "etiquetas": {
            "NRO":          "N° en lista",
            "MATRICULA":    "Matrícula",
            "EMBARCACIÓN":  "Nombre EP",
            "NRO_FAENAS":   "N° de faenas",
            "DESCARGA (t)": "Descarga (t)",
        },
    },
    "🐠 MERLUZA": {
        "nombre":      "Merluza (Merluccius gayi peruanus)",
        "archivo":     "Merluza.xlsx",
        "header_row":  1,           # fila 0 es título fusionado
        "col_mat":     "MATRICULA",
        "col_nom":     "EMBARCACION",
        "etiquetas": {
            "N°":             "N° en lista",
            "EMBARCACION":    "Nombre EP",
            "MATRICULA":      "Matrícula",
            "PERMISO DE PESCA": "Permiso de pesca",
        },
    },
    "🦑 POTA": {
        "nombre":      "Pota / Calamar gigante (Dosidicus gigas)",
        "archivo":     "Pota.xlsx",
        "header_row":  0,           # encabezados desde fila 0
        "col_mat":     "Matricula de la Embarcación Pesquera (AA-#####-AA)",
        "col_nom":     "Nombre de la Embarcación Pesquera:",
        "etiquetas": {
            "Nombre de la Embarcación Pesquera:":                   "Nombre EP",
            "Matricula de la Embarcación Pesquera (AA-#####-AA)":   "Matrícula",
            "Capacidad de bodega":                                   "Capacidad de bodega",
            "Puerto actual de la EP":                               "Puerto base",
            "OBSERVACIONES":                                        "Observaciones",
            "Marca temporal":                                       "Fecha registro",
            "Puntuación":                                           None,  # ocultar
        },
    },
}
# ═══════════════════════════════════════════════════════════════════════════════

# ── CSS ───────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Verificador de Embarcaciones",
    page_icon="🐟", layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:linear-gradient(160deg,#0a1628 0%,#0d2240 60%,#0a3d2e 100%);min-height:100vh;}
.header-block{text-align:center;padding:1.8rem 1rem .4rem;}
.header-block h1{font-family:'IBM Plex Mono',monospace;font-size:1.4rem;color:#00d4aa;letter-spacing:2px;text-transform:uppercase;margin:0;}
.header-block p{color:#7ab8c8;font-size:.8rem;margin:.3rem 0 0;letter-spacing:1px;}
.result-ok{background:linear-gradient(135deg,rgba(0,200,100,.12),rgba(0,212,170,.08));border:2px solid #00c864;border-radius:14px;padding:1.2rem 1.4rem;margin:1rem 0;}
.badge-ok{font-family:'IBM Plex Mono',monospace;font-size:1.05rem;font-weight:700;color:#00c864;letter-spacing:2px;margin-bottom:.5rem;}
.vessel-name{font-size:1.15rem;font-weight:700;color:#e0f8f0;margin-bottom:.7rem;padding-bottom:.5rem;border-bottom:1px solid rgba(0,212,170,.2);}
.ficha-row{display:flex;justify-content:space-between;align-items:flex-start;padding:.35rem 0;border-bottom:1px solid rgba(255,255,255,.04);}
.ficha-lbl{font-size:.7rem;color:#5aa0b8;font-family:'IBM Plex Mono',monospace;text-transform:uppercase;letter-spacing:.5px;flex:1.2;padding-right:.5rem;line-height:1.4;}
.ficha-val{font-size:.83rem;color:#e0f8f0;font-weight:600;flex:1.5;text-align:right;line-height:1.4;}
.ficha-nr{font-size:.83rem;color:#2a4a5a;font-style:italic;font-weight:400;flex:1.5;text-align:right;}
.result-fail{background:rgba(200,40,40,.1);border:2px solid #dc3232;border-radius:14px;padding:1.2rem 1.4rem;margin:1rem 0;}
.badge-fail{font-family:'IBM Plex Mono',monospace;font-size:1.05rem;font-weight:700;color:#ff5555;letter-spacing:2px;}
.fail-detail{font-size:.85rem;color:#ffaaaa;margin-top:.4rem;line-height:1.6;}
.accion{background:rgba(255,180,0,.07);border-left:3px solid #ffc800;padding:.7rem 1rem;border-radius:0 8px 8px 0;margin:.8rem 0;font-size:.8rem;color:#ffe066;line-height:1.6;}
.footer{text-align:center;font-size:.65rem;color:#2a4860;margin-top:2rem;font-family:'IBM Plex Mono',monospace;}
.stSelectbox>div>div{background:rgba(255,255,255,.06)!important;border:1px solid rgba(0,212,170,.25)!important;color:#e0f0ff!important;border-radius:8px!important;}
.stTextInput>div>div>input{background:rgba(255,255,255,.06)!important;border:1px solid rgba(0,212,170,.25)!important;color:#e0f0ff!important;border-radius:8px!important;font-family:'IBM Plex Mono',monospace!important;font-size:1rem!important;letter-spacing:2px!important;text-transform:uppercase!important;}
.stTextInput>div>div>input::placeholder{color:#2a4860!important;}
div[data-testid="stSelectbox"] label,div[data-testid="stTextInput"] label{color:#7ab8c8!important;font-size:.72rem!important;font-family:'IBM Plex Mono',monospace!important;letter-spacing:1.5px!important;text-transform:uppercase!important;}
.stButton>button{background:linear-gradient(135deg,#00d4aa,#0099cc)!important;color:#0a1628!important;border:none!important;border-radius:8px!important;font-family:'IBM Plex Mono',monospace!important;font-weight:700!important;letter-spacing:2px!important;text-transform:uppercase!important;width:100%!important;padding:.6rem!important;font-size:.88rem!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:.8rem!important;max-width:520px!important;}
</style>
""", unsafe_allow_html=True)


# ── DESCARGA ──────────────────────────────────────────────────────────────────
def _req_download(file_id, destino):
    import requests, re
    s = requests.Session()
    for url in [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t",
        f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
    ]:
        try:
            r = s.get(url, stream=True, timeout=60)
            if r.status_code != 200: continue
            if "text/html" in r.headers.get("Content-Type",""):
                m = re.search(r'confirm=([0-9A-Za-z_-]+)', r.text)
                if m:
                    r = s.get(f"https://drive.google.com/uc?export=download&confirm={m.group(1)}&id={file_id}",
                              stream=True, timeout=60)
            with open(destino,"wb") as f:
                for chunk in r.iter_content(32768):
                    if chunk: f.write(chunk)
            if zipfile.is_zipfile(destino): return True
            if os.path.exists(destino): os.remove(destino)
        except Exception: continue
    return False


@st.cache_resource(show_spinner=False)
def init_datos():
    if os.path.exists(CARPETA_DATOS) and glob.glob(f"{CARPETA_DATOS}/*.xlsx"):
        return True
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    ok = False
    try:
        gdown.download(f"https://drive.google.com/uc?id={ZIP_FILE_ID}",
                       output=ZIP_LOCAL, quiet=True)
        ok = os.path.exists(ZIP_LOCAL) and zipfile.is_zipfile(ZIP_LOCAL)
    except Exception: pass
    if not ok:
        ok = _req_download(ZIP_FILE_ID, ZIP_LOCAL)
    if not ok: return False
    with zipfile.ZipFile(ZIP_LOCAL,"r") as zf:
        for m in zf.namelist():
            fn = os.path.basename(m)
            if not fn: continue
            with zf.open(m) as src, open(os.path.join(CARPETA_DATOS,fn),"wb") as dst:
                dst.write(src.read())
    return True


# ── CARGA DE EXCEL ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def cargar_excel(archivo, header_row):
    """Carga el Excel con la fila de encabezado correcta para cada archivo."""
    ruta = os.path.join(CARPETA_DATOS, archivo)
    if not os.path.exists(ruta):
        for f in glob.glob(f"{CARPETA_DATOS}/*"):
            if os.path.basename(f).lower() == archivo.lower():
                ruta = f; break
        else:
            return None

    df = pd.read_excel(ruta, engine="openpyxl", header=header_row, dtype=str)
    # Limpiar columnas
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.loc[:, df.columns != "nan"]
    df = df.dropna(how="all").reset_index(drop=True)
    # Limpiar valores
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
    return df


# ── BÚSQUEDA ──────────────────────────────────────────────────────────────────
def limpiar(s):
    return str(s).strip().upper().replace(" ","").replace("-","").replace(".","")

def buscar(df, termino_raw, col_mat, col_nom=None):
    termino = limpiar(termino_raw)
    if len(termino) < 2: return None

    vals_mat = df[col_mat].apply(limpiar)

    # 1. Exacta
    mask = vals_mat == termino
    if mask.any(): return df[mask].copy()

    # 2. Parcial en matrícula
    mask = vals_mat.str.contains(termino, na=False, regex=False)
    if mask.any(): return df[mask].copy()

    # 3. En nombre
    if col_nom and col_nom in df.columns:
        vals_nom = df[col_nom].apply(limpiar)
        mask = vals_nom.str.contains(termino, na=False, regex=False)
        if mask.any(): return df[mask].copy()

    return None


# ── FICHA FISCALIZADOR ────────────────────────────────────────────────────────
def render_ficha(fila, cfg):
    col_mat  = cfg["col_mat"]
    col_nom  = cfg["col_nom"]
    etiquetas = cfg["etiquetas"]
    recurso  = cfg["nombre"]

    nombre_emb    = str(fila.get(col_nom, "")).strip() or "No registra"
    matricula_emb = str(fila.get(col_mat, "")).strip().upper() or "—"

    # Construir filas de la ficha en el orden definido en etiquetas
    filas_html = f"""
    <div class="ficha-row">
      <span class="ficha-lbl">Recurso verificado</span>
      <span class="ficha-val" style="color:#00d4aa;">{recurso}</span>
    </div>"""

    cols_ya = set()

    def add(col):
        nonlocal filas_html
        if col in cols_ya or col not in fila.index: return
        cols_ya.add(col)
        label = etiquetas.get(col)
        if label is None: return          # columna oculta
        v = str(fila[col]).strip()
        ok = v and v.lower() not in ("nan","none","","0")
        if ok:
            filas_html += (f'<div class="ficha-row">'
                           f'<span class="ficha-lbl">{label}</span>'
                           f'<span class="ficha-val">{v}</span>'
                           f'</div>')
        else:
            filas_html += (f'<div class="ficha-row">'
                           f'<span class="ficha-lbl">{label}</span>'
                           f'<span class="ficha-nr">No registra</span>'
                           f'</div>')

    # Orden: primero columnas definidas en etiquetas, luego el resto
    for col in etiquetas:
        add(col)
    for col in fila.index:
        if col not in cols_ya:
            # Columnas extra no mapeadas: mostrar con nombre tal cual
            if col not in cols_ya:
                cols_ya.add(col)
                v = str(fila[col]).strip()
                if v and v.lower() not in ("nan","none","","0"):
                    filas_html += (f'<div class="ficha-row">'
                                   f'<span class="ficha-lbl">{col}</span>'
                                   f'<span class="ficha-val">{v}</span>'
                                   f'</div>')

    return f"""
<div class="result-ok">
  <div class="badge-ok">✅ AUTORIZADA</div>
  <div class="vessel-name">{nombre_emb}</div>
  {filas_html}
</div>"""


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-block">
  <h1>⚓ VERIFICADOR<br>DE EMBARCACIONES</h1>
  <p>DIREPRO TUMBES · PRODUCE</p>
</div>
""", unsafe_allow_html=True)

listas_ok = init_datos()
if not listas_ok:
    st.error("No se pudieron cargar las listas. Verifica permisos del ZIP en Google Drive.")
    st.stop()

recurso_key  = st.selectbox("RECURSO A VERIFICAR", options=list(RECURSOS.keys()))
cfg          = RECURSOS[recurso_key]

st.markdown(
    f'<div style="font-size:.72rem;color:#7ab8c8;font-family:IBM Plex Mono,monospace;'
    f'margin:.1rem 0 .7rem;">▸ {cfg["nombre"]}</div>',
    unsafe_allow_html=True
)

termino = st.text_input(
    "MATRÍCULA, NÚMERO O NOMBRE DE EMBARCACIÓN",
    placeholder="Ej: PS-56224-BM  ó  56224  ó  nombre",
    max_chars=60, key="busqueda",
)

buscar_btn = st.button("🔍  VERIFICAR EMBARCACIÓN")

# ── BÚSQUEDA ──────────────────────────────────────────────────────────────────
if buscar_btn or (termino and len(termino.strip()) >= 3):
    df = cargar_excel(cfg["archivo"], cfg["header_row"])

    if df is None:
        st.error(f"No se encontró {cfg['archivo']} en el ZIP.")
    else:
        col_mat = cfg["col_mat"]
        col_nom = cfg["col_nom"]

        # Verificar que las columnas existen
        if col_mat not in df.columns:
            st.error(f"Columna '{col_mat}' no encontrada. Columnas: {list(df.columns)}")
        else:
            resultados = buscar(df, termino.strip(), col_mat, col_nom)

            if resultados is not None and len(resultados) > 0:
                if len(resultados) > 1:
                    st.markdown(
                        f'<div style="font-size:.75rem;color:#00d4aa;font-family:'
                        f'IBM Plex Mono,monospace;margin:.3rem 0;">'
                        f'📋 {len(resultados)} coincidencias</div>',
                        unsafe_allow_html=True
                    )
                for _, fila in resultados.iterrows():
                    st.markdown(render_ficha(fila, cfg), unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div class="result-fail">
  <div class="badge-fail">❌ NO AUTORIZADA</div>
  <div class="fail-detail">
    <b>{termino.strip().upper()}</b> no figura en la lista oficial
    para <b>{cfg['nombre']}</b>.
  </div>
</div>""", unsafe_allow_html=True)
                st.markdown("""
<div class="accion">
  ⚠️ <b>Acción del fiscalizador:</b> Documentar en acta de fiscalización.
  Verificar permiso de pesca vigente y tipificar conforme
  DS 017-2017-PRODUCE y modificatorias vigentes.
</div>""", unsafe_allow_html=True)

            st.markdown(
                f'<div style="font-size:.65rem;color:#2a4860;text-align:right;'
                f'font-family:IBM Plex Mono,monospace;margin-top:.4rem;">'
                f'{len(df):,} embarcaciones · {cfg["archivo"]}</div>',
                unsafe_allow_html=True
            )

# ── EXPANDERS ─────────────────────────────────────────────────────────────────
with st.expander("📋 ¿Cómo usar?"):
    st.markdown("""
    1. Selecciona el **recurso** que está siendo extraído.
    2. Ingresa la **matrícula completa**, solo el **número** o el **nombre** del barco.
    3. Toca **VERIFICAR**.

    **Ejemplos:** `PS-56224-BM` · `56224` · `MI POPY`

    ✅ **AUTORIZADA** → ficha completa de la embarcación.
    ❌ **NO AUTORIZADA** → documentar en acta.
    """)

with st.expander("⚖️ Base legal"):
    st.markdown("""
    - DS 017-2017-PRODUCE – Reglamento de Fiscalización y Sanción
    - DS 009-2025-PRODUCE / DS 006-2025-PRODUCE – Modificatorias
    - DS 020-2011-PRODUCE – ROP Tumbes
    - RM N° 00070-2026-PRODUCE – Bonito artesanal 2026
    """)

st.markdown("""
<div class="footer">
  DIREPRO TUMBES · PRODUCE · USO OFICIAL EN CAMPO<br>
  Datos según lista PRODUCE vigente
</div>
""", unsafe_allow_html=True)
