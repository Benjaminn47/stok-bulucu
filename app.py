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

with st.expander("🔑 Durum"):
    st.write("Gemini:", "✅" if GEMINI_API_KEY else "❌")
    st.write("Tavily:", "✅" if TAVILY_API_KEY else "❌")

yuklenen_fotograf = st.file_uploader("Ürün Fotoğrafı 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ek Detay (renk, numara vb.)", "")

if st.button("Analiz Et ve Ara", use_container_width=True):
    if not yuklenen_fotograf:
        st.warning("Fotoğraf yükleyin.")
    elif not GEMINI_API_KEY:
        st.error("Gemini API anahtarınızı ekleyin.")
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
                            {"text": "Bu görseldeki ürünün markasını, modelini ve rengini kısa yaz."},
                            {"inline_data": {"mime_type": mime_type, "data": img_str}}
                        ]
                    }]
                }

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                response_json = response.json()

                if response.status_code == 200:
                    text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    tespit = text.strip()
                    st.success(f"**Tespit Edilen Ürün:** {tespit}")

                    # Tavily Kısmı - Hata korumalı
                    if TAVILY_API_KEY:
                        try:
                            tavily = TavilyClient(api_key=TAVILY_API_KEY)
                            with st.spinner("Web'de stok ve indirim aranıyor..."):
                                query = f"{tespit} {ek_detay} Türkiye stok fiyat indirim"
                                results = tavily.search(query, search_depth="basic", max_results=5)  # advanced yerine basic
                                
                                st.markdown("### 🛒 Bulunan Sonuçlar")
                                for item in results.get("results", []):
                                    st.markdown(f"""
                                    **[{item.get('title', 'Ürün')}]({item.get('url', '#')})**
                                    > {item.get('content', '')[:250]}...
                                    """)
                        except Exception as tavily_err:
                            st.warning("Tavily arama sırasında hata oluştu. Sadece Gemini tespiti gösteriliyor.")
                            st.code(str(tavily_err))
                    else:
                        st.info("Tavily API anahtarı eklenmedi.")
                else:
                    st.error(f"Gemini Hatası: {response.status_code}")
                    st.json(response_json)

            except Exception as e:
                st.error("Genel Hata")
                st.code(traceback.format_exc())
