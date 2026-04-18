# Deployment de CiteCrawl en Streamlit Cloud

Guía rápida para desplegar CiteCrawl en Streamlit Cloud de forma gratuita.

## Requisitos previos

1. Cuenta en GitHub (con acceso a este repositorio)
2. Cuenta en [Streamlit Cloud](https://streamlit.io/cloud)
3. API keys:
   - Firecrawl API key (obten en [firecrawl.dev](https://firecrawl.dev))
   - Google Gemini API key (obten en [ai.google.com](https://ai.google.com))

## Pasos para deployment

### 1. Conectar repositorio a Streamlit Cloud

1. Ve a [Streamlit Cloud](https://share.streamlit.io)
2. Haz clic en "Deploy an app"
3. Selecciona tu repositorio GitHub (`complexluise/citecrawl`)
4. Deja los defaults:
   - Repository: `complexluise/citecrawl`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

### 2. Configurar secrets (API keys)

1. Después de desplegar, ve a "Advanced settings"
2. Abre la sección "Secrets"
3. Agrega tus API keys en formato TOML:

```toml
FIRECRAWL_API_KEY = "your_firecrawl_api_key_here"
GEMINI_API_KEY = "your_gemini_api_key_here"
```

4. Haz clic en "Deploy"

### 3. Esperar deployment

- El primer deployment toma ~2-3 minutos
- Verás un URL como: `https://tu-app-name.streamlit.app`

### 4. Generar QR para la charla

```bash
pip install qrcode pillow
python -c "import qrcode; qrcode.make('https://your-app-url.streamlit.app').save('qr_code.png')"
```

Abre `qr_code.png` e inclúyelo en tus diapositivas de presentación.

## Troubleshooting

### "ModuleNotFoundError: No module named 'citecrawl'"

Streamlit Cloud leerá `requirements.txt` automáticamente. Verifica que:
- streamlit está en requirements.txt
- google-generativeai está incluido
- firecrawl-py está incluido

### API keys no funcionan

- Abre "App menu" (⋮) → "Settings"
- Verifica que los secrets están configurados correctamente
- El formato debe ser exacto: `FIRECRAWL_API_KEY` y `GEMINI_API_KEY`

### La app es lenta

- Streamlit Cloud tiene límites de recursos en el tier gratuito
- Para mejor performance, considera un upgrade a "Community Cloud"

## Links útiles

- [Documentación Streamlit Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [Referencia de secrets](https://docs.streamlit.io/deploy/streamlit-cloud/deploy-your-app/secrets-management)

## Después de deployment

Tu app estará disponible en:
```
https://your-app-name.streamlit.app
```

Comparte este URL en:
- Charla (con QR)
- LinkedIn (en el post)
- Documentación del proyecto

¡Listo! Ya tienes CiteCrawl funcionando en línea. 🚀
