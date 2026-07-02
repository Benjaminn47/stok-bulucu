import streamlit as st
from google import genai
from google.genai import types
from tavily import TavilyClient
from PIL import Image
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
        st.error("❌ Gemini API Anahtarı yükli değil veya hatalı!")
    else:
        st.success("✓ Gemini API Anahtarı Okundu!")
        
    if not TAVILY_API_KEY:
        st.error("❌ Tavily API Anahtarı yükli değil veya hatalı!")
    else:
        st.success("✓ Tavily API Anahtarı Okundu!")

# İstemcileri başlat
client = None
tavily_client = None

if GEMINI_API_KEY:
    try:
        # Yeni nesil google-genai istemcisi başlatılıyor
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        st.error(f"Gemini istemcisi başlatılamadı: {e}")

if TAVILY_API_KEY:
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as e:
        st.error(f"Tavily istemcisi başlatılamadı: {e}")

# Kullanıcı Girdi Alanları
yuklenen_fotograf = st.file_uploader("Ürünün Fotoğrafını Yükleyin 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ekstra Detay (Örn: 45 Numara, Siyah renk)", placeholder="İstediğiniz bedeni veya detayı yazın...")

if st.button("Görseli Analiz Et ve Aramayı Başlat", use_container_width=True):
    if yuklenen_fotograf is not None:
        if not GEMINI_API_KEY or not TAVILY_API_KEY:
            st.error("Lütfen önce sağ alt kısımdan 'Sırlar (Secrets)' ayarlarına giderek API anahtarlarınızı girin.")
        elif client is None:
            st.error("Gemini API istemcisi düzgün başlatılamadı. Lütfen anahtarınızı kontrol edin.")
        else:
            with st.spinner("Yapay zeka görseli analiz ediyor ve canlı stok taraması yapıyor..."):
                try:
                    # 1. Aşama: Gemini AI ile Görsel Analizi
                    image = Image.open(yuklenen_fotograf)
                    st.image(image, caption="Analiz Edilen Ürün", use_column_width=True)
                    
                    prompt = "Bu görseldeki ürünün tam markasını, model numarasını ve rengini kısa bir metin olarak yaz."
                    
                    # Yeni google-genai kütüphanesi formatında generate_content çağrısı
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt, image]
                    )
                    tespit_edilen_urun = response.text.strip()
                    
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
