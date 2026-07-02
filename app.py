import streamlit as st
import requests
import base64
from tavily import TavilyClient
from PIL import Image
import io
import traceback

# Sayfa Ayarları (Mobil uyumlu görünüm için)
st.set_page_config(page_title="Akıllı Stok & İndirim Bulucu", page_icon="👟", layout="centered")

# Secrets kontrolü ve çekilmesi
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

st.title("📱 Akıllı Stok ve İndirim Bulucu")
st.write("Bilgisayara ihtiyaç duymadan telefonunuzdan kullanın. Ürün fotoğrafı yükleyin, yapay zeka markayı tanısın, canlı stok ve indirim kodlarını bulsun.")

# Hata Ayıklama Paneli (Şifrelerin okunup okunmadığını kontrol eder)
with st.expander("🛠️ Bağlantı ve Anahtar Kontrolü (Hata Ayıklama)"):
    if not GEMINI_API_KEY:
        st.error("❌ Gemini API Anahtarı yüklü değil!")
    else:
        st.success(f"✓ Gemini API Anahtarı Okundu: {GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-5:]}")
        
    if not TAVILY_API_KEY:
        st.error("❌ Tavily API Anahtarı yüklü değil!")
    else:
        st.success(f"✓ Tavily API Anahtarı Okundu!")

# İstemcileri başlat
tavily_client = None
if TAVILY_API_KEY:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Kullanıcı Girdi Alanları
yuklenen_fotograf = st.file_uploader("Ürünün Fotoğrafını Yükleyin 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ekstra Detay (Örn: 45 Numara, Siyah renk)", placeholder="İstediğiniz bedeni veya detayı yazın...")

if st.button("Görseli Analiz Et ve Aramayı Başlat", use_container_width=True):
    if yuklenen_fotograf is not None:
        if not GEMINI_API_KEY or not TAVILY_API_KEY:
            st.error("Lütfen önce sağ alt kısımdan 'Sırlar (Secrets)' ayarlarına giderek API anahtarlarınızı girin.")
        else:
            with st.spinner("Yapay zeka görseli analiz ediyor ve canlı stok taraması yapıyor..."):
                try:
                    # 1. Aşama: Gemini AI ile Görsel Analizi (Direct HTTP API Call)
                    image = Image.open(yuklenen_fotograf)
                    st.image(image, caption="Analiz Edilen Ürün", use_column_width=True)
                    
                    # Görseli bytes olarak RAM'e kaydedip oradan base64'e dönüştürüyoruz
                    buffered = io.BytesIO()
                    img_format = image.format if image.format else "JPEG"
                    image.save(buffered, format=img_format)
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    mime_type = f"image/{img_format.lower()}"
                    if mime_type == "image/jpg":
                        mime_type = "image/jpeg"
                    
                    # Gemini API'sine doğrudan güvenli internet bağlantısı kuruyoruz
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    headers = {"Content-Type": "application/json"}
                    
                    prompt = "Bu görseldeki ürünün tam markasını, model numarasını ve rengini kısa bir metin olarak yaz."
                    
                    # Kusursuz şekilde yapılandırılmış veri paketi
                    payload = {
                        "contents":
                            }
                        ]
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    response_json = response.json()
                    
                    # Yanıtı kontrol et
                    if response.status_code!= 200:
                        st.error(f"Google Gemini API Hatası ({response.status_code}):")
                        st.json(response_json)
                    else:
                        # Yanıt içindeki listeleri doğru indislerle ayıklıyoruz
                        tespit_edilen_urun = response_json["candidates"]["content"]["parts"]["text"].strip()
                        st.success(f"**Yapay Zeka Tespiti:** {tespit_edilen_urun}")
                        
                        # 2. Aşama: Tavily API ile Derinlemesine Web ve İndirim Araması
                        arama_sorgusu = f"{tespit_edilen_urun} {ek_detay} satın al Türkiye fiyat stok"
                        indirim_sorgusu = f"{tespit_edilen_urun} güncel indirim kodu 2026 Türkiye"
                        
                        st.info("E-ticaret siteleri ve kupon platformları taranıyor...")
                        
                        # Canlı arama motoru tetikleniyor
                        stok_sonuclari = tavily_client.search(arama_sorgusu, search_depth="advanced", max_results=3)
                        kupon_sonuclari = tavily_client.search(indirim_sorgusu, search_depth="basic", max_results=2)
                        
                        # 3. Aşama: Sonuçları Listeleme
                        st.markdown("### 🛒 Bulunan Satış Noktaları ve Linkler")
                        for item in stok_sonuclari['results']:
                            st.markdown(f"""
                            * **[{item['title']}]({item['url']})**
                            > {item['content']}
                            """)
                        
                        st.markdown("### 🎟️ Bulunan Aktif İndirim Kodları")
                        for kupon in kupon_sonuclari['results']:
                            st.markdown(f"""
                            * **[Kupon Kaynağı: {kupon['title']}]({kupon['url']})**
                            > {kupon['content']}
                            """)

                except Exception as e:
                    st.error("Bir hata oluştu! Detaylı hata raporu aşağıdadır:")
                    st.code(traceback.format_exc())
    else:
        st.warning("Lütfen arama yapmak için bir ürün fotoğrafı yükleyin.")
