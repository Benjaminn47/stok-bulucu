import streamlit as st
import requests
import base64
from tavily import TavilyClient
from PIL import Image
import io
import traceback

st.set_page_config(page_title="Akıllı Stok & İndirim Bulucu", page_icon="👟", layout="centered")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

st.title("📱 Akıllı Stok ve İndirim Bulucu")

with st.expander("🔑 API Durumu"):
    st.write(f"Gemini Key: {'✅ Var' if GEMINI_API_KEY else '❌ Yok'}")
    st.write(f"Tavily Key: {'✅ Var' if TAVILY_API_KEY else '❌ Yok'}")

yuklenen_fotograf = st.file_uploader("Ürün Fotoğrafı Yükle 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ek Detay (renk, numara vb.)", "")

if st.button("Analiz Et ve Ara", use_container_width=True):
    if not yuklenen_fotograf:
        st.warning("Fotoğraf yükleyin.")
    elif not GEMINI_API_KEY:
        st.error("Gemini API anahtarını secrets.toml dosyasına ekleyin.")
    else:
        with st.spinner("Gemini analiz ediyor..."):
            try:
                image = Image.open(yuklenen_fotograf)
                st.image(image, caption="Yüklenen Fotoğraf")

                # Base64
                buffered = io.BytesIO()
                image.save(buffered, format=image.format or "JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                payload = {
                    "contents": [{
                        "parts": [{
                            "text": "Bu görseldeki ayakkabı veya ürünün markasını ve modelini kısa yaz.",
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_str
                            }
                        }]
                    }]
                }

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                
                if response.status_code == 200:
                    data = response.json()
                    try:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        st.success(f"**Tespit:** {text}")
                    except:
                        st.error("Yanıt okunamadı.")
                        st.json(data)
                else:
                    st.error(f"API Hatası: {response.status_code}")
                    st.json(response.json())

            except Exception as e:
                st.error("Hata oluştu")
                st.code(traceback.format_exc())
