import streamlit as st
import requests
import base64
from PIL import Image
import io
import traceback

# Sayfa Ayarları (Mobil uyumlu görünüm için)
st.set_page_config(page_title="Akıllı Stok & İndirim Bulucu", page_icon="👟", layout="centered")

# Secrets kontrolü ve çekilmesi
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

st.title("📱 Akıllı Stok ve İndirim Bulucu")
st.write("Yüklediğiniz fotoğrafı yapay zeka ile tanır, Türkiye pazarında (NB, FLO, SuperStep, Boyner, Hepsiburada) canlı stok tespiti yapar, kuponları bulur ve sepet simülasyonlu uzman araştırma raporu üretir.")

# Hata Ayıklama Paneli (Şifrelerin okunup okunmadığını kontrol eder)
with st.expander("🔑 Bağlantı ve Şifre Durumu"):
    st.write("Gemini API Durumu:", "✅ Okundu" if GEMINI_API_KEY else "❌ Eksik")
    st.write("Tavily API Durumu:", "✅ Okundu" if TAVILY_API_KEY else "❌ Eksik")

# Tavily Arama Yardımcı Fonksiyonu
def search_tavily(query, api_key):
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": 5
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json().get("results", [])
    except Exception as e:
        st.warning(f"Arama hatası: {e}")
    return []

# Kullanıcı Girdi Alanları
yuklenen_fotograf = st.file_uploader("Ürünün Fotoğrafını Yükleyin 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ekstra Detay (Örn: 45 Numara, kahverengi gri vb.)", placeholder="İstediğiniz bedeni veya detayı yazın...")

if st.button("Görseli Analiz Et ve Derin Araştırmayı Başlat", use_container_width=True):
    if yuklenen_fotograf is not None:
        if not GEMINI_API_KEY or not TAVILY_API_KEY:
            st.error("Lütfen önce sağ alt kısımdan 'Sırlar (Secrets)' ayarlarına giderek her iki API anahtarınızı da girin.")
        else:
            # 1. AŞAMA: ÜRÜN TANIMLAMA (Gemini Vision)
            with st.spinner("Yapay zeka görseldeki ayakkabıyı tanımlıyor..."):
                try:
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
                    
                    # Google API Bağlantı Adresi ve Başlık Ayarı (401 Önleyici)
                    headers = {"Content-Type": "application/json"}
                    if GEMINI_API_KEY.startswith("AQ."):
                        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                        headers["Authorization"] = f"Bearer {GEMINI_API_KEY}"
                    else:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    
                    # DÜZELTİLMİŞ PAYLOAD
                    payload = {
                        "contents": [{
                            "parts": [{
                                "text": "Bu görseldeki ürünün tam markasını, model numarasını ve rengini kısa bir metin olarak yaz.",
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": img_str
                                }
                            }]
                        }]
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    response_json = response.json()
                    
                    if response.status_code != 200:
                        st.error(f"Google Gemini Görsel Analiz Hatası ({response.status_code}):")
                        st.json(response_json)
                    else:
                        tespit_edilen_urun = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                        st.success(f"🔍 **Yapay Zeka Tespiti:** {tespit_edilen_urun}")
                        
                        # 2. AŞAMA: DERİN İNTERNET ARAŞTIRMASI (Tavily Multi-Query Search)
                        with st.spinner("Türkiye e-ticaret pazarı, stoklar ve aktif indirim kuponları taranıyor..."):
                            # Arama 1: Canlı Fiyat ve Stok
                            q1 = f"{tespit_edilen_urun} {ek_detay} satın al Türkiye fiyat stok durumunu sorgula (New Balance, FLO, SuperStep, Hepsiburada, Boyner, FashFed)"
                            stok_data = search_tavily(q1, TAVILY_API_KEY)
                            
                            # Arama 2: Orijinallik ve Güvenlik Parametreleri
                            q2 = f"{tespit_edilen_urun} orijinal ürün kontrolü sahtecilik analizi nelere dikkat edilmeli satıcı güvenilirliği"
                            güvenlik_data = search_tavily(q2, TAVILY_API_KEY)
                            
                            # Arama 3: Kuponlar ve Kampanyalar
                            q3 = f"Boyner, SuperStep, FLO, New Balance Türkiye aktif indirim kodları kuponları kampanyaları 2026 Donanımhaber Kuponla"
                            kupon_data = search_tavily(q3, TAVILY_API_KEY)
                            
                            # Ham Arama Sonuçlarını Metne Dönüştürme
                            stok_txt = "\n".join([f"- {item['title']}: {item['content']} ({item['url']})" for item in stok_data])
                            güvenlik_txt = "\n".join([f"- {item['title']}: {item['content']}" for item in güvenlik_data])
                            kupon_txt = "\n".join([f"- {item['title']}: {item['content']} ({item['url']})" for item in kupon_data])
                            
                        # 3. AŞAMA: DERİN UZMAN RAPORU SENTEZİ (Gemini Synthesis)
                        with st.spinner("Elde edilen tüm pazar verileri analiz ediliyor ve uzman raporunuz yazılıyor..."):
                            synthesis_prompt = f"""
                            Sen Türkiye'nin en seçkin e-ticaret analisti, spor giyim pazarı uzmanı ve veri araştırmacısısın.
                            Kullanıcı bir ayakkabı yükledi: {tespit_edilen_urun}
                            Kullanıcının ek detayları (beden/numara, renk vb.): {ek_detay}
                            
                            Arka planda yaptığımız internet araştırmaları sonucu elde ettiğimiz ham veriler aşağıdadır:
                            
                            STOK VE FİYAT VERİLERİ:
                            {stok_txt}
                            
                            ORİJİNAL ÜRÜN VE GÜVENLİK ANALİZİ:
                            {güvenlik_txt}
                            
                            İNDİRİM KODLARI VE KAMPANYALAR:
                            {kupon_txt}
                            
                            Lütfen bu ham verileri derinlemesine analiz et ve kullanıcıya son derece kapsamlı ve profesyonel bir TÜRKÇE RAPOR hazırlat. 
                            Rapor kesinlikle şu 4 ana başlığı içermeli ve başlıkların altını son derece dolu, detaylı, analiz ve tablolarla doldurmalısın:
                            
                            # Türkiye Spor Giyim ve E-Ticaret Pazarı Araştırma Raporu: {tespit_edilen_urun} Analizi
                            
                            ## 1. Ürün Anatomisi, Malzeme Mühendisliği ve Orijinallik Değerlendirmesi
                            - Ürünün (veya benzer NB / spor silüetlerinin) anatomik yapısını (Poliüretan/polyester oranları, C-CAP orta taban veya ilgili yastıklama teknolojilerini) detaylıca anlat.
                            - Orijinal ürün satın alırken Trendyol/Hepsiburada satıcılarının güvenilirliğine, sahtecilik risklerine karşı nelere dikkat edilmesi gerektiğini detaylandır.
                            
                            ## 2. Türkiye E-Ticaret Pazarı Stok, Beden ve Fiyat Haritası
                            - Hangi platformda stok var? (FLO, SuperStep, Boyner, New Balance, Hepsiburada vb.)
                            - Özellikle kullanıcının istediği {ek_detay} ebatları/varyantı var mı?
                            - Kargo, iade (30 gün iade vb.), taksit avantajları, lojistik süreçlerini içeren mükemmel bir karşılaştırma tablosu oluştur. Tabloda tek boşluklu sade Markdown formatı kullan. Bulunan site linklerini tabloya yerleştir.
                            
                            ## 3. Aktif Kupon Kodları ve Sepet Simülasyonları
                            - Donanımhaber, Kuponla veya Picodi gibi sitelerden gelen tüm indirim kodlarını (%20 ilk alışveriş, 250 TL mobil indirim, %30 resmi site kodu gibi) listele.
                            - Fiyatları ve kuponları eşleştirerek sepet simülasyonları yap. "Senaryo 1, Senaryo 2" gibi matematiksel hesaplamaları tek tek göster. En yüksek indirim oranını veren kazanan senaryoyu ilan et.
                            
                            ## 4. Alışveriş Karar Matrisi ve Nihai Aksiyon Planı
                            - Kullanıcının en güvenli ve en ucuz şekilde bu ayakkabıyı alabilmesi için izlemesi gereken adım adım stratejik yol haritasını yaz.
                            
                            Üslubu profesyonel tut. "Sistemimiz", "arama sonuçları", "veri tabanı" gibi teknik terimlerden bahsetme; doğrudan kendin araştırmış ve nihai sonucu analiz etmiş gibi konuş. Satış platformlarının adlarını ve linklerini mutlaka doğru şekilde entegre et.
                            """
                            
                            synthesis_payload = {
                                "contents": [{"parts": [{"text": synthesis_prompt}]}]
                            }
                            
                            synthesis_response = requests.post(url, json=synthesis_payload, headers=headers)
                            synthesis_json = synthesis_response.json()
                            
                            if synthesis_response.status_code != 200:
                                st.error(f"Sentezleme Hatası ({synthesis_response.status_code}):")
                                st.json(synthesis_json)
                            else:
                                final_report = synthesis_json["candidates"][0]["content"]["parts"][0]["text"]
                                st.markdown("---")
                                st.markdown(final_report)
                                st.balloons()
                                
                except Exception as e:
                    st.error("Bir hata oluştu! Detaylı hata raporu aşağıdadır:")
                    st.code(traceback.format_exc())
    else:
        st.warning("Lütfen arama yapmak için bir ürün fotoğrafı yükleyin.")
