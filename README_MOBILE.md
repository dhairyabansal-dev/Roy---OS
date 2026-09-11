# Roy OS — Mobile Access

Roy OS can be hosted as a Streamlit web app and opened from Android like an app.

## Important

The default AI backend is Ollama on `localhost:11434`. A cloud deployment cannot access Ollama running on your laptop. For a fully online mobile version, configure the hosted LLM fallback through the environment variables already supported by `config.py`.

## Deploy

Use a Streamlit-compatible host or container platform. The included `Procfile`, `Dockerfile`, and `.streamlit/config.toml` are deployment helpers.

## Android

1. Open the deployed Roy OS URL in Chrome.
2. Open the browser menu.
3. Choose **Add to Home screen** / **Install app**.
4. Launch Roy OS from the new home-screen icon.

The mobile UI is still the same Streamlit application, so no separate Android APK is required.
