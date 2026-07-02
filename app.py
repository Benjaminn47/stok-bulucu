import streamlit as st
import requests
import base64
from tavily import TavilyClient
from PIL import Image
import io
import traceback

# Sayfa Ayarları
st.set_page_config(page_title="Akıllı Stok & İndirim Bulucu", page_icon="👟", layout="centered")

# Secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

st.title("📱 Akıllı Stok ve İndirim Bulucu")
st.write("Bilgisayara ihtiyaç duymadan telefonunuzdan kullanın. Ürün fotoğrafı yükleyin, yapay zeka markayı tanısın, canlı stok ve indirim kodlarını bulsun.")

# Hata Ayıklama
with st.expander("🛠️ Bağlantı ve Anahtar Kontrolü"):
    if not GEMINI_API_KEY:
        st.error("❌ Gemini API Anahtarı yüklü değil!")
    else:
        st.success(f"✓ Gemini API: {GEMINI_API_KEY[:8]}... mevcut")
    if not TAVILY_API_KEY:
        st.error("❌ Tavily API Anahtarı yüklü değil!")
    else:
        st.success("✓ Tavily API Anahtarı Okundu!")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

yuklenen_fotograf = st.file_uploader("Ürünün Fotoğrafını Yükleyin 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ekstra Detay (Örn: 45 Numara, Siyah renk)", placeholder="İstediğiniz detayı yazın...")

if st.button("Görseli Analiz Et ve Aramayı Başlat", use_container_width=True):
    if yuklenen_fotograf is None:
        st.warning("Lütfen bir ürün fotoğrafı yükleyin.")
    elif not GEMINI_API_KEY or not TAVILY_API_KEY:
        st.error("API anahtarlarınızı Streamlit Secrets'a ekleyin.")
    else:
        with st.spinner("Gemini analiz yapıyor..."):
            try:
                image = Image.open(yuklenen_fotograf)
                st.image(image, caption="Yüklenen Ürün", use_column_width=True)

                # Base64 çevir
                buffered = io.BytesIO()
                img_format = image.format or "JPEG"
                image.save(buffered, format=img_format)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

                mime_type = f"image/{img_format.lower()}"
                if mime_type == "image/jpg":
                    mime_type = "image/jpeg"

                # Gemini API Call
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": "Bu görseldeki ürünün markasını, modelini ve rengini kısa yaz.",
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": img_str
                            }
                        }]
                    }]
                }

                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                response_json = response.json()

                tespit_edilen_urun = "Ürün tespit edilemedi."

                if response.status_code == 200:
                    try:
                        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                        tespit_edilen_urun = text.strip()
                        st.success(f"**Tespit Edilen Ürün:** {tespit_edilen_urun}")
                    except:
                        st.warning("Gemini yanıtını okuyamadı.")
                        st.json(response_json)
                else:
                    st.error(f"Gemini API Hatası: {response.status_code}")
                    st.json(response_json)

                # Tavily Araması
                if tavily_client and tespit_edilen_urun != "Ürün tespit edilemedi.":
                    with st.spinner("Web'de stok ve indirim aranıyor..."):
                        stok_sonuclari = tavily_client.search(
                            f"{tespit_edilen_urun} {ek_detay} satın al Türkiye", 
                            search_depth="advanced", 
                            max_results=5
                        )
                        kupon_sonuclari = tavily_client.search(
                            f"{tespit_edilen_urun} indirim kodu kupon 2026", 
                            search_depth="basic", 
                            max_results=3
                        )

                        st.markdown("### 🛒 Bulunan Ürünler")
                        for item in stok_sonuclari.get('results', []):
                            st.markdown(f"**[{item.get('title')}]({item.get('url')})**\n> {item.get('content', '')}")

                        st.markdown("### 🎟️ İndirim Kodları")
                        for kupon in kupon_sonuclari.get('results', []):
                            st.markdown(f"**[{kupon.get('title')}]({kupon.get('url')})**\n> {kupon.get('content', '')}")
                else:
                    st.info("Arama için yeterli bilgi bulunamadı.")

            except Exception as e:
                st.error("Beklenmeyen hata oluştu:")
                st.code(traceback.format_exc())
