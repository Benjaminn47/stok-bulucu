import streamlit as st
import requests

st.title("Gemini Mevcut Modeller")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    st.error("API anahtarı bulunamadı!")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        models = response.json()
        st.success("Mevcut Modeller:")
        for model in models.get("models", []):
            name = model.get("name", "")
            display_name = model.get("displayName", "")
            st.write(f"• **{display_name}** → `{name}`")
    else:
        st.error(f"Hata: {response.status_code}")
        st.json(response.json())
