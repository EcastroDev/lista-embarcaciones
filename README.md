# ⚓ Verificador de Embarcaciones Pesqueras
### DIREPRO Tumbes · PRODUCE · Fiscalización

---

## ¿Cómo funciona?

La app descarga un ZIP desde tu Google Drive que contiene los Excel
con las listas de embarcaciones autorizadas (Bonito, Merluza, Pota, etc.).
Solo necesitas configurar un único FILE_ID en `app.py`.

---

## 🚀 Configuración y despliegue (paso a paso)

### Paso 1 — Preparar el ZIP en Google Drive

1. En tu PC, crea una carpeta y mete los 3 Excel:
   ```
   Bonito.xlsx
   Merluza.xlsx
   Pota.xlsx
   ```
   > ⚠️ Los nombres deben ser exactamente esos (respeta mayúsculas)

2. Comprime esa carpeta en un **ZIP** (clic derecho → Comprimir / Send to ZIP)

3. Sube el ZIP a **Google Drive**

4. Clic derecho en el ZIP → **Compartir** → cambia a  
   **"Cualquier persona con el enlace"** puede **Ver**

5. Clic en el ZIP para abrirlo → copia la URL, que tiene esta forma:
   ```
   https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view
   ```
   El FILE_ID es la parte entre `/d/` y `/view`:
   ```
   1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```

### Paso 2 — Pegar el FILE_ID en app.py

Abre `app.py` y busca la línea (~línea 13):

```python
ZIP_FILE_ID = "REEMPLAZA_CON_EL_FILE_ID_DE_TU_ZIP"
```

Reemplaza con tu ID real:

```python
ZIP_FILE_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz"
```

**Eso es todo lo que hay que editar.**

### Paso 3 — Subir a GitHub

Estructura del repositorio (sin carpeta `data/`, ya no se necesita):

```
tu_repo/
├── app.py              ← con tu FILE_ID configurado
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── config.toml
```

Desde GitHub web:
- **Add file → Upload files** → sube los 5 archivos → Commit

### Paso 4 — Desplegar en Streamlit Cloud

1. [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Conecta GitHub → selecciona repo → branch `main` → archivo `app.py`
3. **Deploy** → URL lista en ~3 minutos

---

## 🔄 Actualizar las listas

Cuando PRODUCE emita nuevas listas:
1. Actualiza los Excel en tu PC
2. Crea un nuevo ZIP con los Excel actualizados
3. **Reemplaza** el ZIP en Google Drive (misma ubicación, mismo nombre)
   - O sube uno nuevo y actualiza el `ZIP_FILE_ID` en `app.py`
4. En Streamlit Cloud → **Reboot app** (o espera 30 min para que expire el caché)

---

## ➕ Agregar nuevo recurso (Jurel, Caballa...)

1. Agrega `Jurel.xlsx` al ZIP y vuelve a subir a Drive
2. En `app.py`, descomenta las líneas de JUREL en el bloque `RECURSOS`:

```python
"🐟 JUREL": {
    "nombre": "Jurel (Trachurus murphyi)",
    "archivo": "Jurel.xlsx",
},
```

3. Commit → Streamlit actualiza solo

---

## 📱 App en pantalla de inicio (móvil)

- **Android Chrome**: Menú ⋮ → *Agregar a pantalla de inicio*
- **iPhone Safari**: Compartir → *Agregar a pantalla de inicio*

---

## Base legal
- DS 017-2017-PRODUCE y modificatorias (DS 009-2025, DS 006-2025)
- DS 020-2011-PRODUCE – ROP Tumbes
- RM N° 00070-2026-PRODUCE – Bonito artesanal 2026
