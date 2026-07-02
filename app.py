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
st.write("Fotoğraf yükle, yapay zeka analiz etsin.")

with st.expander("🔑 Durum"):
    st.write("Gemini:", "✅" if GEMINI_API_KEY else "❌")

yuklenen_fotograf = st.file_uploader("Ürün Fotoğrafı 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ek Detay (renk, numara vb.)", "")

if st.button("Analiz Et ve Ara", use_container_width=True):
    if not yuklenen_fotograf:
        st.warning("Fotoğraf yükleyin.")
    elif not GEMINI_API_KEY:
        st.error("API anahtarınızı secrets.toml'a ekleyin.")
    else:
        with st.spinner("Gemini analiz yapıyor..."):
            try:
                image = Image.open(yuklenen_fotograf)
                st.image(image, caption="Yüklenen Fotoğraf", use_column_width=True)

                buffered = io.BytesIO()
                img_format = image.format or "JPEG"
                image.save(buffered, format=img_format)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

                mime_type = f"image/{img_format.lower()}"
                if mime_type == "image/jpg":
                    mime_type = "image/jpeg"

                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Bu görseldeki ürünün markasını, modelini ve rengini kısa ve net yaz."},
                            {"inline_data": {"mime_type": mime_type, "data": img_str}}
                        ]
                    }]
                }

                # En stabil model (listeden gelen)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                response_json = response.json()

                if response.status_code == 200:
                    text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    st.success(f"**Tespit Edilen Ürün:** {text.strip()}")

                    if TAVILY_API_KEY:
                        tavily = TavilyClient(api_key=TAVILY_API_KEY)
                        with st.spinner("Stok ve indirim aranıyor..."):
                            query = f"{text} {ek_detay} Türkiye stok fiyat indirim kodu"
                            results = tavily.search(query, search_depth="advanced", max_results=6)
                            
                            st.markdown("### 🛒 Bulunan Sonuçlar")
                            for item in results.get("results", []):
                                st.markdown(f"""
                                **[{item.get('title', 'Ürün')}]({item.get('url', '#')})**
                                > {item.get('content', '')[:300]}
                                """)
                else:
                    st.error(f"API Hatası: {response.status_code}")
                    st.json(response_json)

            except Exception as e:
                st.error("Bir hata oluştu")
                st.code(traceback.format_exc())
