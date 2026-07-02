import streamlit as st
import requests
import base64
from tavily import TavilyClient
from PIL import Image
import io
import traceback

# Sayfa ayarları
st.set_page_config(page_title="Akıllı Stok & İndirim Bulucu", page_icon="👟", layout="centered")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

st.title("📱 Akıllı Stok ve İndirim Bulucu")
st.write("Ürün fotoğrafı yükleyin, yapay zeka analiz etsin ve stok/indirim bulsun.")

# API Kontrol
with st.expander("🔑 API Durumu"):
    st.write("Gemini:", "✅" if GEMINI_API_KEY else "❌")
    st.write("Tavily:", "✅" if TAVILY_API_KEY else "❌")

# Girdiler
yuklenen_fotograf = st.file_uploader("Ürün Fotoğrafı Yükleyin 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ekstra Detay (örnek: 45 numara, siyah)", "")

if st.button("🔍 Analiz Et ve Ara", use_container_width=True):
    if not yuklenen_fotograf:
        st.warning("Lütfen bir fotoğraf yükleyin.")
    elif not GEMINI_API_KEY:
        st.error("Gemini API anahtarınızı secrets.toml dosyasına ekleyin.")
    else:
        with st.spinner("Gemini görseli analiz ediyor..."):
            try:
                # Fotoğrafı göster
                image = Image.open(yuklenen_fotograf)
                st.image(image, caption="Yüklenen Fotoğraf", use_column_width=True)

                # Base64 çevir
                buffered = io.BytesIO()
                img_format = image.format or "JPEG"
                image.save(buffered, format=img_format)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

                mime_type = f"image/{img_format.lower()}"
                if mime_type == "image/jpg":
                    mime_type = "image/jpeg"

                # DOĞRU PAYLOAD YAPISI
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Bu görseldeki ürünün markasını, modelini ve rengini tespit et. Sadece kısa cevap ver."},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": img_str
                                }
                            }
                        ]
                    }]
                }

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                response_json = response.json()

                if response.status_code == 200:
                    try:
                        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                        tespit = text.strip()
                        st.success(f"**Yapay Zeka Tespiti:** {tespit}")

                        # Tavily Arama
                        if TAVILY_API_KEY:
                            tavily = TavilyClient(api_key=TAVILY_API_KEY)
                            with st.spinner("Stok ve indirim aranıyor..."):
                                results = tavily.search(f"{tespit} {ek_detay} Türkiye satın al stok indirim", 
                                                      search_depth="advanced", max_results=6)
                                
                                st.markdown("### 🛒 Sonuçlar")
                                for item in results.get("results", []):
                                    st.markdown(f"""
                                    **[{item.get('title', 'Ürün')}]({item.get('url', '#')})**
                                    > {item.get('content', '')}
                                    """)
                    except Exception as parse_err:
                        st.error("Yanıt işlenemedi.")
                        st.json(response_json)
                else:
                    st.error(f"API Hatası: {response.status_code}")
                    st.json(response_json)

            except Exception as e:
                st.error("Genel Hata")
                st.code(traceback.format_exc())
