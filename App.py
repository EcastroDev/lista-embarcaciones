import streamlit as st
import pandas as pd
import gdown
import zipfile
import os
import glob

ZIP_FILE_ID   = "1-buA01ayUVId3zs5sbM-O_FJDPplsumq"
ZIP_LOCAL     = "listas_embarcaciones.zip"
CARPETA_DATOS = "listas_embarcaciones"

RECURSOS = {
    "🐟 BONITO": {"nombre": "Bonito (Sarda chiliensis chiliensis)", "archivo": "Bonito.xlsx"},
    "🐠 MERLUZA": {"nombre": "Merluza (Merluccius gayi peruanus)", "archivo": "Merluza.xlsx"},
    "🦑 POTA": {"nombre": "Pota / Calamar gigante (Dosidicus gigas)", "archivo": "Pota.xlsx"},
}

st.set_page_config(page_title="Verificador de Embarcaciones", page_icon="🐟",
                   layout="centered", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:linear-gradient(160deg,#0a1628 0%,#0d2240 60%,#0a3d2e 100%);min-height:100vh;}
.header-block{text-align:center;padding:2rem 1rem 0.5rem;}
.header-block h1{font-family:'IBM Plex Mono',monospace;font-size:1.45rem;color:#00d4aa;letter-spacing:2px;text-transform:uppercase;margin:0;}
.header-block p{color:#7ab8c8;font-size:0.82rem;margin:0.4rem 0 0;letter-spacing:1px;}
.result-ok{background:linear-gradient(135deg,rgba(0,200,100,.15),rgba(0,212,170,.1));border:2px solid #00c864;border-radius:12px;padding:1.2rem 1.5rem;margin:1rem 0;}
.result-ok .status{font-family:'IBM Plex Mono',monospace;font-size:1.3rem;font-weight:700;color:#00c864;letter-spacing:2px;}
.result-ok .vessel-name{font-size:1.1rem;font-weight:700;color:#e0f8f0;margin-top:.3rem;}
.result-ok .detail{font-size:.82rem;color:#a0d8ef;margin-top:.6rem;font-family:'IBM Plex Mono',monospace;line-height:2;}
.result-fail{background:linear-gradient(135deg,rgba(220,50,50,.15),rgba(180,30,30,.1));border:2px solid #dc3232;border-radius:12px;padding:1.2rem 1.5rem;margin:1rem 0;}
.result-fail .status{font-family:'IBM Plex Mono',monospace;font-size:1.3rem;font-weight:700;color:#ff5555;letter-spacing:2px;}
.result-fail .detail{font-size:.85rem;color:#ffaaaa;margin-top:.3rem;line-height:1.6;}
.info-strip{background:rgba(255,200,0,.08);border-left:3px solid #ffc800;padding:.7rem 1rem;border-radius:0 8px 8px 0;margin:.8rem 0;font-size:.8rem;color:#ffe066;}
.footer{text-align:center;font-size:.68rem;color:#3a6080;margin-top:2rem;font-family:'IBM Plex Mono',monospace;letter-spacing:1px;}
.stSelectbox>div>div{background:rgba(255,255,255,.07)!important;border:1px solid rgba(0,212,170,.3)!important;color:#e0f0ff!important;border-radius:8px!important;}
.stTextInput>div>div>input{background:rgba(255,255,255,.07)!important;border:1px solid rgba(0,212,170,.3)!important;color:#e0f0ff!important;border-radius:8px!important;font-family:'IBM Plex Mono',monospace!important;font-size:1.05rem!important;letter-spacing:2px!important;text-transform:uppercase!important;}
.stTextInput>div>div>input::placeholder{color:#3a6080!important;}
div[data-testid="stSelectbox"] label,div[data-testid="stTextInput"] label{color:#7ab8c8!important;font-size:.75rem!important;font-family:'IBM Plex Mono',monospace!important;letter-spacing:1.5px!important;text-transform:uppercase!important;}
.stButton>button{background:linear-gradient(135deg,#00d4aa,#0099cc)!important;color:#0a1628!important;border:none!important;border-radius:8px!important;font-family:'IBM Plex Mono',monospace!important;font-weight:700!important;letter-spacing:2px!important;text-transform:uppercase!important;width:100%!important;padding:.6rem!important;font-size:.9rem!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem!important;max-width:540px!important;}
</style>""", unsafe_allow_html=True)


# ── DESCARGA ─────────────────────────────────────────────────────────────────

def _descargar_con_requests(file_id, destino):
    import requests, re
    session = requests.Session()
    urls = [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t",
        f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
        f"https://drive.google.com/uc?id={file_id}",
    ]
    for url in urls:
        try:
            r = session.get(url, stream=True, timeout=60)
            if r.status_code != 200:
                continue
            if "text/html" in r.headers.get("Content-Type", ""):
                m = re.search(r'confirm=([0-9A-Za-z_-]+)', r.text)
                if m:
                    r = session.get(
                        f"https://drive.google.com/uc?export=download&confirm={m.group(1)}&id={file_id}",
                        stream=True, timeout=60)
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
            if zipfile.is_zipfile(destino):
                return True
            if os.path.exists(destino):
                os.remove(destino)
        except Exception:
            continue
    return False


@st.cache_resource(show_spinner=False)
def descargar_y_extraer_zip():
    if ZIP_FILE_ID == "PENDIENTE_CONFIGURAR":
        return False
    if os.path.exists(CARPETA_DATOS):
        if glob.glob(f"{CARPETA_DATOS}/*.xlsx") + glob.glob(f"{CARPETA_DATOS}/*.csv"):
            return True
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    descargado = False
    try:
        gdown.download(f"https://drive.google.com/uc?id={ZIP_FILE_ID}",
                       output=ZIP_LOCAL, quiet=True)
        if os.path.exists(ZIP_LOCAL) and zipfile.is_zipfile(ZIP_LOCAL):
            descargado = True
    except Exception:
        pass
    if not descargado:
        descargado = _descargar_con_requests(ZIP_FILE_ID, ZIP_LOCAL)
    if not descargado:
        st.error("No se pudo descargar la lista. Verifica permisos del ZIP en Drive.")
        return False
    try:
        with zipfile.ZipFile(ZIP_LOCAL, "r") as zf:
            for member in zf.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue
                with zf.open(member) as src, \
                     open(os.path.join(CARPETA_DATOS, filename), "wb") as dst:
                    dst.write(src.read())
        return True
    except Exception as e:
        st.error(f"Error al descomprimir: {e}")
        return False


@st.cache_data(ttl=1800, show_spinner=False)
def cargar_excel(archivo):
    ruta = os.path.join(CARPETA_DATOS, archivo)
    if not os.path.exists(ruta):
        for f in glob.glob(f"{CARPETA_DATOS}/*"):
            if os.path.basename(f).lower() == archivo.lower():
                ruta = f
                break
        else:
            return None
    try:
        # header=0 garantiza que la primera fila sea el encabezado
        df = pd.read_excel(ruta, engine="openpyxl", header=0, dtype=str)
        return df
    except Exception:
        try:
            return pd.read_csv(ruta, encoding="utf-8", dtype=str)
        except Exception:
            return pd.read_csv(ruta, encoding="latin-1", dtype=str)


# ── PROCESAMIENTO ─────────────────────────────────────────────────────────────

def limpiar(s):
    """Normaliza: mayúsculas, sin espacios ni guiones."""
    return str(s).strip().upper().replace(" ", "").replace("-", "")


def normalizar_df(df):
    """Limpia encabezados y convierte todo a str."""
    df = df.copy()
    # Limpiar nombres de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    # Eliminar columnas sin nombre (Unnamed)
    df = df.loc[:, ~df.columns.str.startswith("UNNAMED")]
    # Eliminar filas completamente vacías
    df = df.dropna(how="all")
    # Convertir todo a string limpio
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
    return df


def detectar_col_matricula(df):
    """Detecta la columna de matrícula con múltiples criterios."""
    candidatos_exactos = [
        "MATRÍCULA", "MATRICULA", "N° MATRÍCULA", "N° MATRICULA",
        "Nº MATRÍCULA", "Nº MATRICULA", "NRO MATRICULA", "NRO. MATRICULA",
        "MATRICULA DE LA EMBARCACIÓN", "MATRICULA NAVE", "MAT"
    ]
    # 1. Coincidencia exacta
    for candidato in candidatos_exactos:
        if candidato.upper() in df.columns:
            return candidato.upper()
    # 2. Columna que contiene "MATRICUL"
    for col in df.columns:
        if "MATRICUL" in col or "MATRÍCUL" in col:
            return col
    # 3. Columna que contiene "MAT" (abreviatura)
    for col in df.columns:
        if col.strip() in ["MAT", "MAT.", "MATR"]:
            return col
    # 4. Primera columna como último recurso
    return df.columns[0] if len(df.columns) > 0 else None


def detectar_col_nombre(df):
    """Detecta la columna del nombre de la embarcación."""
    candidatos_exactos = [
        "NOMBRE DE LA EMBARCACIÓN", "NOMBRE DE LA EMBARCACION",
        "NOMBRE EMBARCACIÓN", "NOMBRE EMBARCACION",
        "NOMBRE DE EMBARCACIÓN", "NOMBRE", "NAVE", "EMBARCACIÓN", "EMBARCACION"
    ]
    for candidato in candidatos_exactos:
        if candidato.upper() in df.columns:
            return candidato.upper()
    for col in df.columns:
        if "NOMBRE" in col or "EMBARCAC" in col or "NAVE" in col:
            return col
    return None


def buscar(df, termino_raw, col_mat, col_nom=None):
    """
    Búsqueda en 3 niveles:
    1. Exacta normalizada (PS-56224-BM == PS56224BM)
    2. Contiene el término en matrícula (56224 → PS-56224-BM)
    3. Contiene el término en nombre de embarcación
    """
    termino = limpiar(termino_raw)
    if not termino:
        return None

    vals_mat = df[col_mat].apply(limpiar)

    # Nivel 1: exacta
    mask = vals_mat == termino
    if mask.any():
        return df[mask].copy()

    # Nivel 2: parcial en matrícula
    mask = vals_mat.str.contains(termino, na=False, regex=False)
    if mask.any():
        return df[mask].copy()

    # Nivel 3: en nombre
    if col_nom:
        vals_nom = df[col_nom].apply(limpiar)
        mask = vals_nom.str.contains(termino, na=False, regex=False)
        if mask.any():
            return df[mask].copy()

    return None


def ficha_embarcacion(fila, col_mat, col_nom, recurso_nombre):
    """Genera el HTML de la ficha completa de la embarcación."""
    nombre_emb  = str(fila.get(col_nom, "—")).strip() if col_nom else "—"
    matricula_emb = str(fila.get(col_mat, "—")).strip().upper()

    # Todas las columnas restantes como detalles
    excluir = {col_mat} | ({col_nom} if col_nom else set())
    filas_detalle = ""
    for col in fila.index:
        if col in excluir:
            continue
        val = str(fila[col]).strip()
        if val and val.lower() not in ["nan", "none", ""]:
            filas_detalle += (
                f'<div style="display:flex;justify-content:space-between;'
                f'border-bottom:1px solid rgba(0,212,170,.1);padding:.25rem 0;">'
                f'<span style="color:#5aa0b8;">{col}</span>'
                f'<span style="color:#e0f8f0;font-weight:600;">{val}</span>'
                f'</div>'
            )

    html = (
        f'<div class="result-ok">'
        f'<div class="status">✅ AUTORIZADA</div>'
        f'<div class="vessel-name">{nombre_emb}</div>'
        f'<div class="detail">'
        f'<div style="display:flex;justify-content:space-between;'
        f'border-bottom:1px solid rgba(0,212,170,.1);padding:.25rem 0;">'
        f'<span style="color:#5aa0b8;">MATRÍCULA</span>'
        f'<span style="color:#e0f8f0;font-weight:600;">{matricula_emb}</span>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;'
        f'border-bottom:1px solid rgba(0,212,170,.1);padding:.25rem 0;">'
        f'<span style="color:#5aa0b8;">RECURSO</span>'
        f'<span style="color:#e0f8f0;font-weight:600;">{recurso_nombre}</span>'
        f'</div>'
        f'{filas_detalle}'
        f'</div></div>'
    )
    return html


# ── HEADER ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-block">
  <h1>⚓ VERIFICADOR<br>DE EMBARCACIONES</h1>
  <p>MINISTERIO DE LA PRODUCCIÓN</p>
</div>
""", unsafe_allow_html=True)

listas_ok = descargar_y_extraer_zip()

# ── CONTROLES ────────────────────────────────────────────────────────────────

recurso_key = st.selectbox("RECURSO A VERIFICAR", options=list(RECURSOS.keys()))
recurso_info = RECURSOS[recurso_key]

st.markdown(
    f'<div style="font-size:.75rem;color:#7ab8c8;font-family:IBM Plex Mono,monospace;'
    f'margin:.2rem 0 .8rem;">▸ {recurso_info["nombre"]}</div>',
    unsafe_allow_html=True
)

matricula_input = st.text_input(
    "MATRÍCULA, NÚMERO O NOMBRE DE EMBARCACIÓN",
    placeholder="Ej: PS-56224-BM  ó  56224  ó  nombre del barco",
    max_chars=60,
    key="mat",
)

buscar_btn = st.button("🔍  VERIFICAR EMBARCACIÓN")

# ── BÚSQUEDA ─────────────────────────────────────────────────────────────────

if buscar_btn or (matricula_input and len(matricula_input.strip()) >= 3):
    mat = matricula_input.strip()

    if not listas_ok:
        st.markdown(
            '<div class="info-strip">⚠️ Listas no disponibles. '
            'Verifica el FILE_ID del ZIP.</div>',
            unsafe_allow_html=True
        )
    else:
        with st.spinner("Consultando lista oficial..."):
            df_raw = cargar_excel(recurso_info["archivo"])

        if df_raw is None:
            disponibles = [os.path.basename(f) for f in glob.glob(f"{CARPETA_DATOS}/*.*")]
            st.markdown(
                f'<div class="info-strip">⚙️ No se encontró '
                f'<b>{recurso_info["archivo"]}</b>.<br>'
                f'Archivos en ZIP: {", ".join(disponibles) if disponibles else "ninguno"}'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            df = normalizar_df(df_raw)
            col_mat = detectar_col_matricula(df)
            col_nom = detectar_col_nombre(df)

            # ── DEBUG (oculto en expander) ────────────────────────────────
            with st.expander("🔧 Diagnóstico de datos (para soporte técnico)"):
                st.markdown(f"**Columnas detectadas:** `{list(df.columns)}`")
                st.markdown(f"**Columna matrícula:** `{col_mat}`")
                st.markdown(f"**Columna nombre:** `{col_nom}`")
                st.markdown(f"**Total filas:** {len(df)}")
                st.markdown("**Primeras 5 filas:**")
                st.dataframe(df.head(5), use_container_width=True)
                if col_mat:
                    st.markdown(f"**Ejemplos de matrícula en lista:** "
                                f"`{list(df[col_mat].dropna().head(5).values)}`")

            if col_mat is None:
                st.error("No se encontró columna de matrícula. Ver diagnóstico arriba.")
            else:
                resultados = buscar(df, mat, col_mat, col_nom)

                if resultados is not None and len(resultados) > 0:
                    if len(resultados) > 1:
                        st.markdown(
                            f'<div style="font-size:.8rem;color:#00d4aa;'
                            f'font-family:IBM Plex Mono,monospace;margin-bottom:.5rem;">'
                            f'Se encontraron {len(resultados)} coincidencias:</div>',
                            unsafe_allow_html=True
                        )
                    for _, fila in resultados.iterrows():
                        st.markdown(
                            ficha_embarcacion(fila, col_mat, col_nom,
                                              recurso_info["nombre"]),
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        f'<div class="result-fail">'
                        f'<div class="status">❌ NO AUTORIZADA</div>'
                        f'<div class="detail"><b>{mat.upper()}</b> no figura en la lista '
                        f'oficial para <b>{recurso_info["nombre"]}</b>.</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        '<div class="info-strip">'
                        '⚠️ <b>Acción del fiscalizador:</b> Documentar en acta. '
                        'Verificar permiso de pesca vigente y tipificar conforme '
                        'DS 017-2017-PRODUCE y modificatorias vigentes.'
                        '</div>',
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f'<div style="font-size:.7rem;color:#3a6080;text-align:right;'
                    f'font-family:IBM Plex Mono,monospace;margin-top:.5rem;">'
                    f'{len(df):,} registros · {recurso_info["archivo"]}</div>',
                    unsafe_allow_html=True
                )

# ── EXPANDERS ────────────────────────────────────────────────────────────────

with st.expander("📋 ¿Cómo usar esta herramienta?"):
    st.markdown("""
    1. Selecciona el **recurso** que está siendo extraído.
    2. Ingresa la **matrícula completa**, solo el **número** o el **nombre** del barco.
    3. Presiona **VERIFICAR** — o espera la búsqueda automática (desde 3 caracteres).

    **Ejemplos válidos:**
    - `PS-56224-BM` → matrícula completa
    - `56224` → solo el número
    - `SEÑOR DE SIPAN` → parte del nombre

    ✅ **AUTORIZADA** → figura en lista oficial de PRODUCE con ficha completa.
    ❌ **NO AUTORIZADA** → no figura → documentar en acta.
    """)

with st.expander("⚖️ Base legal"):
    st.markdown("""
    - Decreto Ley N° 25977 – Ley General de Pesca
    - DS 012-2001-PE – Reglamento de la LGP
    - DS 017-2017-PRODUCE – Reglamento de Fiscalización y Sanción
    - DS 009-2025-PRODUCE / DS 006-2025-PRODUCE – Modificatorias
    - DS 020-2011-PRODUCE – ROP Tumbes
    - RM N° 00070-2026-PRODUCE – Bonito artesanal 2026
    """)

st.markdown("""
<div class="footer">
   · PRODUCE · USO  EN CAMPO<br>
  Datos según lista PRODUCE vigente
</div>
""", unsafe_allow_html=True)
