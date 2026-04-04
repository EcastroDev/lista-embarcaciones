import streamlit as st
import numpy as np
from PIL import Image
import io
import pickle
from pathlib import Path

# ─────────────────────────────────────────────
# CARGA DE BASE DE DATOS (incluida en el repo)
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_db():
    db_path = Path(__file__).parent / "species_db.pkl"
    with open(db_path, "rb") as f:
        return pickle.load(f)


# ─────────────────────────────────────────────
# CARACTERÍSTICAS E IMAGEN
# ─────────────────────────────────────────────

def color_histogram(img: Image.Image, bins: int = 16) -> np.ndarray:
    arr = np.array(img.convert("RGB").resize((128, 128)), dtype=np.float32) / 255.0
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    cmax  = np.maximum(np.maximum(r, g), b)
    delta = cmax - np.minimum(np.minimum(r, g), b) + 1e-8
    h = np.zeros_like(r)
    h[cmax==r] = ((g[cmax==r]-b[cmax==r])/delta[cmax==r]) % 6
    h[cmax==g] = (b[cmax==g]-r[cmax==g])/delta[cmax==g] + 2
    h[cmax==b] = (r[cmax==b]-g[cmax==b])/delta[cmax==b] + 4
    h /= 6.0
    s = np.where(cmax > 0, delta/(cmax+1e-8), 0)
    hh, _ = np.histogram(h.flatten(),    bins=bins,   range=(0,1))
    sh, _ = np.histogram(s.flatten(),    bins=bins//2, range=(0,1))
    vh, _ = np.histogram(cmax.flatten(), bins=bins//2, range=(0,1))
    feat  = np.concatenate([hh, sh, vh]).astype(np.float32)
    return feat / (np.linalg.norm(feat) + 1e-8)


def find_similar(query: Image.Image, db: list, top_k: int = 5) -> list:
    q = color_histogram(query)
    scored = [
        (float(np.dot(q, sp["feat"])), i)
        for i, sp in enumerate(db) if sp["feat"] is not None
    ]
    scored.sort(reverse=True)
    return [(db[i], round(s * 100)) for s, i in scored[:top_k]]


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
/* Fondo degradado marino */
.stApp { background: linear-gradient(160deg,#0c4a6e 0%,#075985 40%,#0369a1 100%); }
.block-container { padding-top: .8rem; max-width: 1000px; }

/* Textos */
h1,h2,h3 { color: white !important; }
p, li, label, .stMarkdown p { color: rgba(255,255,255,.9) !important; }

/* Tarjeta resultado */
.rcard {
    background: rgba(255,255,255,.10);
    border: 1px solid rgba(255,255,255,.18);
    border-radius: 14px; padding: 13px 15px; margin-bottom: 9px;
    transition: background .2s;
}
.rcard:hover { background: rgba(255,255,255,.16); }
.sp-name  { font-size:1.05rem; font-weight:700; color:#fff; }
.sp-sci   { font-style:italic; color:#bae6fd; font-size:.83rem; }
.sp-page  {
    background: rgba(37,99,235,.45); border-radius:6px;
    padding:2px 10px; font-size:.78rem; color:#bfdbfe;
    display:inline-block; margin-top:4px;
}
.bar-bg { background:rgba(255,255,255,.15); border-radius:4px; height:5px; margin-top:6px; }
.bar-fg { background:#38bdf8; border-radius:4px; height:5px; }

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: rgba(186,230,253,.8) !important;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: white !important;
    border-bottom: 2px solid #38bdf8;
}
/* Ocultar barra roja de Streamlit */
[data-testid="stStatusWidget"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ── Encabezado ──────────────────────────────
c1, c2 = st.columns([1, 9])
with c1:
    st.markdown("<div style='font-size:2.5rem;margin-top:5px'>🐟</div>",
                unsafe_allow_html=True)
with c2:
    st.markdown("## IDENTIFICADOR DE PECES — TUMBES")
    st.markdown(
        "<p style='font-size:.72rem;letter-spacing:2px;color:rgba(186,230,253,.75);margin-top:-8px'>"
        "CATÁLOGO IMARPE 2022 · APOYO A FISCALIZACIÓN PESQUERA</p>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Carga BD ─────────────────────────────────
with st.spinner("Cargando base de datos..."):
    db = load_db()

total_sp = len(set(s["scientific"] for s in db))
st.success(f"✅ **{total_sp} especies** del Catálogo Ilustrado IMARPE 2022 listas")

st.markdown("---")
st.markdown("### 📷 Captura o sube la foto del pez")

# ── Tabs: Cámara | Archivo ───────────────────
tab_cam, tab_file = st.tabs(["📸  Tomar foto con cámara", "📂  Subir imagen"])

img_input = None

with tab_cam:
    cam = st.camera_input(
        "Apunta la cámara al pez y toca el botón",
        label_visibility="visible",
    )
    if cam:
        img_input = Image.open(cam).convert("RGB")

with tab_file:
    upl = st.file_uploader(
        "Arrastra o selecciona una imagen (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="visible",
    )
    if upl:
        img_input = Image.open(upl).convert("RGB")

# ── Resultados ───────────────────────────────
if img_input:
    st.markdown("---")
    col_img, col_res = st.columns([1, 1])

    with col_img:
        st.markdown("**Imagen analizada:**")
        st.image(img_input, use_container_width=True)

    with col_res:
        st.markdown("**🔍 Top 5 — especies más similares:**")
        with st.spinner("Analizando..."):
            results = find_similar(img_input, db, top_k=5)

        for rank, (sp, pct) in enumerate(results, 1):
            st.markdown(f"""
            <div class='rcard'>
                <div class='sp-name'>#{rank} &nbsp; {sp['common']}</div>
                <div class='sp-sci'>{sp['scientific']}</div>
                <span class='sp-page'>📖 p.{sp['printed_page']}</span>
                <div class='bar-bg'>
                    <div class='bar-fg' style='width:{pct}%'></div>
                </div>
                <small style='color:rgba(186,230,253,.65)'>Similitud: {pct}%</small>
            </div>""", unsafe_allow_html=True)

            if sp.get("thumb"):
                with st.expander(f"Ver página del catálogo — {sp['common']}"):
                    st.image(
                        Image.open(io.BytesIO(sp["thumb"])),
                        caption=f"{sp['scientific']} · p.{sp['printed_page']} · {sp['catalog']}",
                        use_container_width=True,
                    )

    st.info(
        "💡 **Tip campo:** Mejor resultado con foto bien iluminada, "
        "fondo neutro y pez completo. Confirma siempre en la página "
        "indicada del catálogo físico IMARPE 2022."
    )

else:
    st.markdown(
        "<div style='text-align:center;padding:35px 20px;"
        "color:rgba(186,230,253,.45);font-size:1rem'>"
        "👆 Usa la cámara o sube una foto para identificar el pez"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Pie ──────────────────────────────────────
st.markdown(
    "<p style='text-align:center;font-size:.65rem;"
    "color:rgba(186,230,253,.3);letter-spacing:1px;margin-top:18px'>"
    "CATÁLOGO ILUSTRADO DE LA ICTIOFAUNA DE LA REGIÓN TUMBES · IMARPE 2022 · "
    "LABORATORIO COSTERO DE TUMBES</p>",
    unsafe_allow_html=True,
)
