import streamlit as st
import pandas as pd
import gdown
import zipfile
import os
import glob
from pathlib import Path

# ════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN  ← ÚNICO LUGAR QUE DEBES EDITAR
# ════════════════════════════════════════════════════════════════════════════
# 1. Sube un ZIP con tus Excel a Google Drive (compartido "cualquiera con el enlace")
# 2. Copia el FILE_ID de ese ZIP y pégalo aquí:

ZIP_FILE_ID   = "1-buA01ayUVId3zs5sbM-O_FJDPplsumq"   # ← único cambio necesario
ZIP_LOCAL     = "listas_embarcaciones.zip"
CARPETA_DATOS = "listas_embarcaciones"

# Mapeo: nombre del recurso → nombre exacto del archivo Excel dentro del ZIP
RECURSOS = {
    "🐟 BONITO": {
        "nombre": "Bonito (Sarda chiliensis chiliensis)",
        "archivo": "Bonito.xlsx",
    },
    "🐠 MERLUZA": {
        "nombre": "Merluza (Merluccius gayi peruanus)",
        "archivo": "Merluza.xlsx",
    },
    "🦑 POTA": {
        "nombre": "Pota / Calamar gigante (Dosidicus gigas)",
        "archivo": "Pota.xlsx",
    },
    # Agrega más recursos cuando tengas las listas:
    # "🐟 JUREL": {
    #     "nombre": "Jurel (Trachurus murphyi)",
    #     "archivo": "Jurel.xlsx",
    # },
    # "🐟 CABALLA": {
    #     "nombre": "Caballa (Scomber japonicus)",
    #     "archivo": "Caballa.xlsx",
    # },
}
# ════════════════════════════════════════════════════════════════════════════


# ─── CSS ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Verificador de Embarcaciones",
    page_icon="🐟",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

  .stApp {
    background: linear-gradient(160deg, #0a1628 0%, #0d2240 60%, #0a3d2e 100%);
    min-height: 100vh;
  }

  /* Header */
  .header-block { text-align: center; padding: 2rem 1rem 0.5rem; }
  .header-block h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.45rem; color: #00d4aa;
    letter-spacing: 2px; text-transform: uppercase; margin: 0;
  }
  .header-block p {
    color: #7ab8c8; font-size: 0.82rem;
    margin: 0.4rem 0 0; letter-spacing: 1px;
  }

  /* Resultados */
  .result-ok {
    background: linear-gradient(135deg, rgba(0,200,100,0.15), rgba(0,212,170,0.1));
    border: 2px solid #00c864; border-radius: 12px;
    padding: 1.2rem 1.5rem; margin: 1rem 0;
  }
  .result-ok .status {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem; font-weight: 700;
    color: #00c864; letter-spacing: 2px;
  }
  .result-ok .vessel-name {
    font-size: 1.1rem; font-weight: 700;
    color: #e0f8f0; margin-top: 0.3rem;
  }
  .result-ok .detail {
    font-size: 0.78rem; color: #7ab8c8;
    margin-top: 0.5rem; font-family: 'IBM Plex Mono', monospace;
    line-height: 1.8;
  }
  .result-fail {
    background: linear-gradient(135deg, rgba(220,50,50,0.15), rgba(180,30,30,0.1));
    border: 2px solid #dc3232; border-radius: 12px;
    padding: 1.2rem 1.5rem; margin: 1rem 0;
  }
  .result-fail .status {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem; font-weight: 700;
    color: #ff5555; letter-spacing: 2px;
  }
  .result-fail .detail {
    font-size: 0.85rem; color: #ffaaaa;
    margin-top: 0.3rem; line-height: 1.6;
  }

  /* Strip de alerta */
  .info-strip {
    background: rgba(255,200,0,0.08);
    border-left: 3px solid #ffc800;
    padding: 0.7rem 1rem; border-radius: 0 8px 8px 0;
    margin: 0.8rem 0; font-size: 0.8rem; color: #ffe066;
  }

  /* Footer */
  .footer {
    text-align: center; font-size: 0.68rem; color: #3a6080;
    margin-top: 2rem; font-family: 'IBM Plex Mono', monospace; letter-spacing: 1px;
  }

  /* Widgets Streamlit */
  .stSelectbox > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(0,212,170,0.3) !important;
    color: #e0f0ff !important; border-radius: 8px !important;
  }
  .stTextInput > div > div > input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(0,212,170,0.3) !important;
    color: #e0f0ff !important; border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.05rem !important; letter-spacing: 2px !important;
    text-transform: uppercase !important;
  }
  .stTextInput > div > div > input::placeholder { color: #3a6080 !important; }
  div[data-testid="stSelectbox"] label,
  div[data-testid="stTextInput"] label {
    color: #7ab8c8 !important; font-size: 0.75rem !important;
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
  }
  .stButton > button {
    background: linear-gradient(135deg, #00d4aa, #0099cc) !important;
    color: #0a1628 !important; border: none !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important; letter-spacing: 2px !important;
    text-transform: uppercase !important; width: 100% !important;
    padding: 0.6rem !important; font-size: 0.9rem !important;
  }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1rem !important; max-width: 520px !important; }
</style>
""", unsafe_allow_html=True)


# ─── Descarga y extracción del ZIP (una sola vez por sesión) ─────────────────

def _descargar_con_requests(file_id: str, destino: str) -> bool:
    """
    Descarga un archivo público de Google Drive usando requests.
    Maneja automáticamente la confirmación para archivos grandes.
    """
    import requests

    session = requests.Session()

    # URL nueva (drive.usercontent.google.com) — más confiable para archivos públicos
    urls_a_intentar = [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0&confirm=t",
        f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t",
        f"https://drive.google.com/uc?id={file_id}",
    ]

    for url in urls_a_intentar:
        try:
            r = session.get(url, stream=True, timeout=60)
            if r.status_code != 200:
                continue

            content_type = r.headers.get("Content-Type", "")

            # Si Google devuelve una página HTML de confirmación (archivos >100MB)
            if "text/html" in content_type:
                # Extraer token de confirmación
                import re
                token_match = re.search(r'confirm=([0-9A-Za-z_-]+)', r.text)
                if token_match:
                    confirm = token_match.group(1)
                    url2 = f"https://drive.google.com/uc?export=download&confirm={confirm}&id={file_id}"
                    r = session.get(url2, stream=True, timeout=60)
                    if r.status_code != 200:
                        continue

            # Guardar el archivo
            with open(destino, "wb") as f:
                for chunk in r.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)

            # Verificar que es un ZIP válido
            if zipfile.is_zipfile(destino):
                return True
            else:
                os.remove(destino)

        except Exception:
            continue

    return False


@st.cache_resource(show_spinner=False)
def descargar_y_extraer_zip() -> bool:
    """
    Descarga el ZIP desde Google Drive y lo extrae.
    Intenta con gdown primero, luego con requests como respaldo.
    Se ejecuta una sola vez por sesión gracias a cache_resource.
    """
    if ZIP_FILE_ID == "PENDIENTE_CONFIGURAR":
        return False

    # Si ya existe la carpeta con archivos, no volver a descargar
    if os.path.exists(CARPETA_DATOS):
        archivos = glob.glob(f"{CARPETA_DATOS}/*.xlsx") + glob.glob(f"{CARPETA_DATOS}/*.csv")
        if archivos:
            return True

    os.makedirs(CARPETA_DATOS, exist_ok=True)

    # --- Método 1: gdown ---
    descargado = False
    try:
        url = f"https://drive.google.com/uc?id={ZIP_FILE_ID}"
        gdown.download(url, output=ZIP_LOCAL, quiet=True)
        if os.path.exists(ZIP_LOCAL) and zipfile.is_zipfile(ZIP_LOCAL):
            descargado = True
    except Exception:
        pass

    # --- Método 2: requests directo (respaldo) ---
    if not descargado:
        descargado = _descargar_con_requests(ZIP_FILE_ID, ZIP_LOCAL)

    if not descargado:
        st.error("No se pudo descargar la lista de embarcaciones desde Google Drive. "
                 "Verifica que el ZIP esté compartido como 'Cualquier persona con el enlace'.")
        return False

    # Extraer ZIP
    try:
        with zipfile.ZipFile(ZIP_LOCAL, "r") as zf:
            # Extraer solo a la raíz de CARPETA_DATOS (sin subcarpetas del ZIP)
            for member in zf.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue
                source = zf.open(member)
                target_path = os.path.join(CARPETA_DATOS, filename)
                with open(target_path, "wb") as target:
                    target.write(source.read())
        return True
    except Exception as e:
        st.error(f"Error al descomprimir el archivo: {e}")
        return False


@st.cache_data(ttl=1800, show_spinner=False)
def cargar_excel(archivo: str) -> pd.DataFrame | None:
    """Carga un Excel de la carpeta extraída."""
    ruta = os.path.join(CARPETA_DATOS, archivo)
    if not os.path.exists(ruta):
        # Buscar sin distinguir mayúsculas/minúsculas
        archivos_disponibles = glob.glob(f"{CARPETA_DATOS}/*")
        for f in archivos_disponibles:
            if os.path.basename(f).lower() == archivo.lower():
                ruta = f
                break
        else:
            return None
    try:
        return pd.read_excel(ruta, engine="openpyxl")
    except Exception:
        try:
            return pd.read_csv(ruta, encoding="utf-8", on_bad_lines="skip")
        except Exception:
            return pd.read_csv(ruta, encoding="latin-1", on_bad_lines="skip")


# ─── Funciones de búsqueda ───────────────────────────────────────────────────

def normalizar_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def detectar_col_matricula(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        cu = col.upper()
        if any(p in cu for p in ["MATRICUL", "MATRÍCUL", "MATRIC"]):
            return col
    return df.columns[0] if len(df.columns) else None


def detectar_col_nombre(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        cu = col.upper()
        if any(p in cu for p in ["NOMBRE", "EMBARCAC", "NAVE", "VESSEL"]):
            return col
    return None


def buscar_matricula(df: pd.DataFrame, matricula: str, col: str) -> pd.Series | None:
    # Normaliza para búsqueda: sin guiones, sin espacios, mayúsculas
    def limpiar(s: str) -> str:
        return s.strip().upper().replace(" ", "").replace("-", "")

    mat = limpiar(matricula)
    vals = df[col].astype(str).apply(limpiar)
    mask = vals == mat
    return df[mask].iloc[0] if mask.any() else None


# ─── HEADER ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-block">
  <h1>⚓ VERIFICADOR<br>DE EMBARCACIONES</h1>
  <p>DIREPRO TUMBES · PRODUCE</p>
</div>
""", unsafe_allow_html=True)

# ─── Descarga silenciosa al inicio ──────────────────────────────────────────

listas_ok = descargar_y_extraer_zip()

if not listas_ok and ZIP_FILE_ID == "PENDIENTE_CONFIGURAR":
    st.markdown("""
    <div class="info-strip">
      ⚙️ <b>Configuración pendiente:</b><br>
      Edita <code>app.py</code> → reemplaza <code>ZIP_FILE_ID</code>
      con el FILE_ID de tu ZIP en Google Drive.<br>
      Ver instrucciones en README.md
    </div>
    """, unsafe_allow_html=True)

# ─── CONTROLES ───────────────────────────────────────────────────────────────

recurso_key = st.selectbox("RECURSO A VERIFICAR", options=list(RECURSOS.keys()))
recurso_info = RECURSOS[recurso_key]

st.markdown(f"""
<div style="font-size:0.75rem; color:#7ab8c8; font-family:'IBM Plex Mono',monospace;
margin: 0.2rem 0 0.8rem;">▸ {recurso_info['nombre']}</div>
""", unsafe_allow_html=True)

matricula_input = st.text_input(
    "MATRÍCULA DE LA EMBARCACIÓN",
    placeholder="Ej: ZS-21330-BM",
    max_chars=25,
    key="mat",
)

buscar_btn = st.button("🔍  VERIFICAR EMBARCACIÓN")

# ─── LÓGICA DE BÚSQUEDA ──────────────────────────────────────────────────────

activar = buscar_btn or (matricula_input and len(matricula_input.strip()) >= 4)

if activar:
    mat = matricula_input.strip()

    if len(mat) < 4:
        st.markdown('<div class="info-strip">⚠️ Ingresa una matrícula válida.</div>',
                    unsafe_allow_html=True)

    elif not listas_ok:
        st.markdown("""
        <div class="info-strip">
          ⚠️ Las listas no están disponibles todavía. Verifica el FILE_ID del ZIP.
        </div>
        """, unsafe_allow_html=True)

    else:
        with st.spinner("Consultando lista oficial..."):
            df_raw = cargar_excel(recurso_info["archivo"])

        if df_raw is None:
            st.markdown(f"""
            <div class="info-strip">
              ⚙️ No se encontró <b>{recurso_info['archivo']}</b> dentro del ZIP.<br>
              Verifica que el archivo esté en la raíz del ZIP con ese nombre exacto.
            </div>
            """, unsafe_allow_html=True)

            # Mostrar qué archivos sí están disponibles
            disponibles = glob.glob(f"{CARPETA_DATOS}/*.*")
            if disponibles:
                nombres = [os.path.basename(f) for f in disponibles]
                st.markdown(f"**Archivos en el ZIP:** `{'`, `'.join(nombres)}`")

        else:
            df = normalizar_df(df_raw.copy())
            col_mat = detectar_col_matricula(df)
            col_nom = detectar_col_nombre(df)

            if col_mat is None:
                st.error("No se encontró columna de matrícula en el archivo.")
            else:
                fila = buscar_matricula(df, mat, col_mat)
                mat_disp = mat.upper()

                if fila is not None:
                    nombre_emb = str(fila[col_nom]).strip() if col_nom else "—"

                    # Columnas extra (distintas a matrícula y nombre)
                    excluir = {col_mat} | ({col_nom} if col_nom else set())
                    detalles = ""
                    for col in fila.index:
                        if col not in excluir:
                            val = str(fila[col]).strip()
                            if val and val.lower() not in ["nan", "none", ""]:
                                detalles += f"<div>{col}: <b>{val}</b></div>"

                    st.markdown(f"""
                    <div class="result-ok">
                      <div class="status">✅ AUTORIZADA</div>
                      <div class="vessel-name">{nombre_emb}</div>
                      <div class="detail">
                        <div>MATRÍCULA: {mat_disp}</div>
                        <div>RECURSO: {recurso_info['nombre']}</div>
                        {detalles}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.markdown(f"""
                    <div class="result-fail">
                      <div class="status">❌ NO AUTORIZADA</div>
                      <div class="detail">
                        <b>{mat_disp}</b> no figura en la lista oficial
                        para <b>{recurso_info['nombre']}</b>.
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("""
                    <div class="info-strip">
                      ⚠️ <b>Acción del fiscalizador:</b> Documentar en acta.
                      Verificar permiso de pesca vigente y tipificar conforme
                      DS 017-2017-PRODUCE y modificatorias vigentes.
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="font-size:0.7rem; color:#3a6080; text-align:right;
                font-family:'IBM Plex Mono',monospace; margin-top:0.5rem;">
                  {len(df):,} registros · {recurso_info['archivo']}
                </div>
                """, unsafe_allow_html=True)

# ─── EXPANDERS ───────────────────────────────────────────────────────────────

with st.expander("📋 ¿Cómo usar esta herramienta?"):
    st.markdown("""
    1. Selecciona el **recurso** que está siendo extraído.
    2. Ingresa la **matrícula** de la embarcación (ej: `ZS-21330-BM`).
    3. Presiona **VERIFICAR** — la búsqueda también es automática al escribir.

    - ✅ **AUTORIZADA** → figura en lista oficial vigente de PRODUCE.
    - ❌ **NO AUTORIZADA** → no figura → documentar en acta.

    **La búsqueda ignora guiones, espacios y mayúsculas.**
    `ZS21330BM`, `zs-21330-bm` y `ZS 21330 BM` son equivalentes.
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
  DIREPRO TUMBES · PRODUCE · USO OFICIAL EN CAMPO<br>
  Datos según lista PRODUCE vigente
</div>
""", unsafe_allow_html=True)
