import streamlit as st
import gdown
import zipfile
import json
import os
import numpy as np
from PIL import Image
import io
import re
import pickle
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
FOLDER_ID  = "1p-_YzXDyZHhIEXCFAz8DeOhBYhDpsjMr"
DATA_DIR   = Path("data")
CACHE_FILE = DATA_DIR / "features_cache.pkl"

# Nombres de archivos tal como están en tu Google Drive
CATALOG_FILES = {
    "CATÁLOGO DE PECES TUMBES-1-18.pdf":    {"start": 1,   "end": 18},
    "CATÁLOGO DE PECES TUMBES-19-45.pdf":   {"start": 19,  "end": 45},
    "CATÁLOGO DE PECES TUMBES-46-96.pdf":   {"start": 46,  "end": 96},
    "CATÁLOGO DE PECES TUMBES-97-167.pdf":  {"start": 97,  "end": 167},
    "CATÁLOGO DE PECES TUMBES-168-219.pdf": {"start": 168, "end": 219},
    "CATÁLOGO DE PECES TUMBES-220-246.pdf": {"start": 220, "end": 246},
}

SPECIES_RE = re.compile(
    r'([A-Z][a-záéíóúñü]+\s+[a-záéíóúñü]+(?:\s+(?:[A-Z][a-záéíóúñü]+,?\s*\d{4}|\([^)]+\)))?)'
    r'[\r\n]+\u201c([^\u201d]+)\u201d',
    re.MULTILINE
)

# ─────────────────────────────────────────────
# UTILIDADES DE DESCARGA
# ─────────────────────────────────────────────

def is_valid_zip(path: Path) -> bool:
    """Verifica magic bytes PK de un ZIP."""
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"PK"
    except Exception:
        return False


def normalize(name: str) -> str:
    """Normaliza nombre para comparación flexible."""
    return (name.lower()
            .replace("á","a").replace("é","e").replace("í","i")
            .replace("ó","o").replace("ú","u").replace("ñ","n")
            .replace(" ", "").replace("-", ""))


def find_catalog_files(base_dir: Path) -> dict:
    """Busca recursivamente los archivos ZIP del catálogo."""
    found = {}
    norm_map = {normalize(k): k for k in CATALOG_FILES}

    for root, dirs, files in os.walk(base_dir):
        for fname in files:
            if not fname.lower().endswith(".pdf"):
                continue
            full_path = Path(root) / fname
            if not is_valid_zip(full_path):
                continue
            norm_fname = normalize(fname)
            for norm_key, orig_key in norm_map.items():
                if norm_key in norm_fname or norm_fname in norm_key:
                    found[orig_key] = full_path
                    break
    return found


def download_catalogs(data_dir: Path) -> dict:
    """Descarga los catálogos desde Google Drive."""
    data_dir.mkdir(parents=True, exist_ok=True)
    progress = st.progress(0, text="📥 Conectando con Google Drive...")

    try:
        gdown.download_folder(
            id=FOLDER_ID,
            output=str(data_dir),
            quiet=True,
            use_cookies=False,
        )
    except Exception as e:
        st.warning(f"Advertencia en descarga: {e}")

    progress.progress(70, text="🔍 Buscando archivos descargados...")
    found = find_catalog_files(data_dir)
    progress.progress(100, text=f"✅ {len(found)}/6 archivos encontrados")

    if len(found) < 6:
        st.warning(
            f"Solo se encontraron {len(found)} de 6 archivos válidos. "
            "La app funcionará con los disponibles."
        )
    return found


# ─────────────────────────────────────────────
# CARACTERÍSTICAS DE IMAGEN
# ─────────────────────────────────────────────

def color_histogram(img: Image.Image, bins: int = 16) -> np.ndarray:
    """Histograma HSV normalizado como vector de características."""
    arr = np.array(img.convert("RGB").resize((128, 128)), dtype=np.float32) / 255.0
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin + 1e-8

    h = np.zeros_like(r)
    h[cmax == r] = ((g[cmax == r] - b[cmax == r]) / delta[cmax == r]) % 6
    h[cmax == g] = (b[cmax == g] - r[cmax == g]) / delta[cmax == g] + 2
    h[cmax == b] = (r[cmax == b] - g[cmax == b]) / delta[cmax == b] + 4
    h /= 6.0
    s = np.where(cmax > 0, delta / (cmax + 1e-8), 0)

    h_hist, _ = np.histogram(h.flatten(), bins=bins, range=(0, 1))
    s_hist, _ = np.histogram(s.flatten(), bins=bins//2, range=(0, 1))
    v_hist, _ = np.histogram(cmax.flatten(), bins=bins//2, range=(0, 1))
    feat = np.concatenate([h_hist, s_hist, v_hist]).astype(np.float32)
    return feat / (np.linalg.norm(feat) + 1e-8)


# ─────────────────────────────────────────────
# EXTRACCIÓN DE ESPECIES
# ─────────────────────────────────────────────

def extract_all_species(catalog_paths: dict) -> list:
    """Extrae especies e imágenes de los ZIPs del catálogo."""
    db = []
    total = len(catalog_paths)
    prog = st.progress(0, text="🔬 Extrayendo especies del catálogo...")

    for idx, (cat_name, zip_path) in enumerate(catalog_paths.items()):
        prog.progress(int(idx / total * 100), text=f"Procesando {cat_name[:40]}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                pages_meta = {p["page_number"]: p for p in manifest["pages"]}

                for i in range(1, manifest["num_pages"] + 1):
                    try:
                        txt = zf.read(f"{i}.txt").decode("utf-8", errors="ignore")
                    except KeyError:
                        continue

                    ph = re.search(r'^\s*(\d+)\s+(\d+)', txt)
                    printed_page = int(ph.group(1)) if ph else 0

                    for sci, common in SPECIES_RE.findall(txt):
                        sci = sci.strip().replace('\n', ' ')
                        common = common.strip()
                        words = sci.split()
                        if len(words) < 2 or not words[1][0].islower():
                            continue

                        img_bytes, feat = None, None
                        pg = pages_meta.get(i, {})
                        img_name = pg.get("image", {}).get("path", f"{i}.jpeg")
                        try:
                            raw = zf.read(img_name)
                            feat = color_histogram(Image.open(io.BytesIO(raw)))
                            img_bytes = raw
                        except Exception:
                            pass

                        db.append({
                            "scientific": sci,
                            "common": common,
                            "printed_page": printed_page,
                            "catalog_file": cat_name,
                            "file_page": i,
                            "img_bytes": img_bytes,
                            "features": feat,
                        })
        except zipfile.BadZipFile:
            st.warning(f"⚠️ No se pudo leer: {cat_name}")

    prog.progress(100, text="✅ Catálogo procesado")
    return db


# ─────────────────────────────────────────────
# CARGA PRINCIPAL (CACHEADA)
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_database():
    DATA_DIR.mkdir(exist_ok=True)

    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception:
            CACHE_FILE.unlink(missing_ok=True)

    catalog_paths = download_catalogs(DATA_DIR)
    if not catalog_paths:
        return []

    db = extract_all_species(catalog_paths)
    if db:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(db, f)
    return db


def find_similar(query: Image.Image, db: list, top_k: int = 5) -> list:
    q = color_histogram(query)
    scored = [
        (float(np.dot(q, sp["features"])), i)
        for i, sp in enumerate(db) if sp["features"] is not None
    ]
    scored.sort(reverse=True)
    return [(db[i], s) for s, i in scored[:top_k]]


# ─────────────────────────────────────────────
# INTERFAZ
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Identificador de Peces – Tumbes",
    page_icon="🐟",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background: linear-gradient(160deg,#0c4a6e,#075985 40%,#0369a1); }
.block-container { padding-top:1rem; }
h1,h2,h3 { color:white !important; }
p,li,label { color:rgba(255,255,255,.9) !important; }
.result-card {
    background:rgba(255,255,255,.1);
    border:1px solid rgba(255,255,255,.2);
    border-radius:12px; padding:14px; margin-bottom:10px;
}
.sp-title { font-size:1.05rem; font-weight:bold; color:white; }
.sp-sci   { font-style:italic; color:#bae6fd; font-size:.85rem; }
.sp-page  {
    background:rgba(37,99,235,.4); border-radius:6px;
    padding:2px 10px; font-size:.8rem; color:#bfdbfe; display:inline-block;
}
.bar-wrap { background:rgba(255,255,255,.15); border-radius:4px; height:6px; margin-top:5px; }
.bar      { background:#38bdf8; border-radius:4px; height:6px; }
</style>
""", unsafe_allow_html=True)

# Encabezado
c1, c2 = st.columns([1, 8])
with c1:
    st.markdown("## 🐟")
with c2:
    st.markdown("# IDENTIFICADOR DE PECES — TUMBES")
    st.markdown(
        "<p style='font-size:.75rem;letter-spacing:2px;color:rgba(186,230,253,.8)'>"
        "CATÁLOGO IMARPE 2022 · APOYO A FISCALIZACIÓN PESQUERA</p>",
        unsafe_allow_html=True,
    )

st.divider()

db = load_database()
if not db:
    st.error("No se pudo cargar la base de datos.")
    st.stop()

total_sp = len(set(s["scientific"] for s in db))
st.success(f"✅ Base de datos lista: **{total_sp} especies** del Catálogo Ilustrado IMARPE 2022")
st.markdown("---")

st.markdown("### 📷 Sube la foto del pez a identificar")
uploaded = st.file_uploader(
    "JPG, PNG o WEBP · Foto clara · Pez completo · Buena iluminación",
    type=["jpg", "jpeg", "png", "webp"],
)

if uploaded:
    ci, cr = st.columns([1, 1])
    with ci:
        st.markdown("**Imagen cargada:**")
        query = Image.open(uploaded).convert("RGB")
        st.image(query, use_container_width=True)

    with cr:
        st.markdown("**🔍 Especies más similares:**")
        with st.spinner("Analizando imagen..."):
            results = find_similar(query, db, top_k=5)

        for rank, (sp, sim) in enumerate(results, 1):
            pct = int(sim * 100)
            st.markdown(f"""
            <div class='result-card'>
                <div class='sp-title'>#{rank} {sp['common']}</div>
                <div class='sp-sci'>{sp['scientific']}</div>
                <span class='sp-page'>📖 p.{sp['printed_page']}</span>
                <div class='bar-wrap'><div class='bar' style='width:{pct}%'></div></div>
                <small style='color:rgba(186,230,253,.7)'>Similitud: {pct}%</small>
            </div>""", unsafe_allow_html=True)

            if sp.get("img_bytes"):
                with st.expander(f"📄 Ver página del catálogo — {sp['common']}"):
                    st.image(Image.open(io.BytesIO(sp["img_bytes"])),
                             caption=f"{sp['scientific']} · p.{sp['printed_page']}",
                             use_container_width=True)

    st.info("💡 Verifica siempre el resultado consultando la página indicada en el catálogo físico IMARPE 2022.")

else:
    st.markdown(
        "<div style='text-align:center;padding:40px;color:rgba(186,230,253,.5);font-size:1.1rem'>"
        "👆 Sube una foto para iniciar la identificación</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    "<p style='text-align:center;font-size:.7rem;color:rgba(186,230,253,.35);"
    "letter-spacing:1px;margin-top:20px'>"
    "CATÁLOGO ILUSTRADO DE LA ICTIOFAUNA DE LA REGIÓN TUMBES · IMARPE 2022</p>",
    unsafe_allow_html=True,
)
