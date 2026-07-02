import streamlit as st
import requests
import base64
from tavily import TavilyClient
from PIL import Image
import io
import traceback
import json

st.set_page_config(page_title="Ultra Stok Uzmanı", page_icon="🔍", layout="wide")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

st.title("🔍 Ultra Stok & İndirim Uzmanı")
st.caption("Görsel analizi + Derin web araştırması + Akıllı karar motoru")

yuklenen_fotograf = st.file_uploader("Ürün Fotoğrafı Yükleyin 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ekstra İstek / Detay", placeholder="45.5 numara, orijinal kutulu, en ucuz orijinal satıcı")

if st.button("🚀 Ultra Derin Analiz Başlat", use_container_width=True, type="primary"):
    if not yuklenen_fotograf or not GEMINI_API_KEY or not TAVILY_API_KEY:
        st.error("Fotoğraf ve her iki API anahtarı gereklidir.")
    else:
        with st.spinner("Görsel analiz + 3 katmanlı derin araştırma + Akıllı rapor hazırlanıyor..."):
            try:
                # Görsel hazırlık
                image = Image.open(yuklenen_fotograf)
                st.image(image, caption="Analiz Edilen Ürün", use_column_width=True)

                buffered = io.BytesIO()
                img_format = image.format or "JPEG"
                image.save(buffered, format=img_format)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                mime_type = f"image/{img_format.lower()}"

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

                # 1. Ürün Tespiti
                urun_prompt = "Bu görseldeki ürünü profesyonelce analiz et: marka, tam model, renk, özellikler, tahmini kategori. Çok detaylı ol."
                payload = {"contents": [{"parts": [{"text": urun_prompt}, {"inline_data": {"mime_type": mime_type, "data": img_str}}]}]}
                urun_resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                urun_bilgisi = urun_resp.json()["candidates"][0]["content"]["parts"][0]["text"]

                st.success("✅ Ürün Tespiti Tamamlandı")

                # 2. Tavily Derin Aramalar (3 Katman)
                tavily = TavilyClient(api_key=TAVILY_API_KEY)
                aramalar = [
                    f"{urun_bilgisi} {ek_detay} Türkiye en ucuz orijinal stok",
                    f"{urun_bilgisi} {ek_detay} güncel indirim kodu kupon 2026",
                    f"{urun_bilgisi} {ek_detay} vs rakip modeller fiyat karşılaştırma"
                ]

                tum_veriler = []
                for i, sorgu in enumerate(aramalar, 1):
                    with st.spinner(f"Derin arama katmanı {i}/3..."):
                        sonuc = tavily.search(sorgu, search_depth="advanced", max_results=5)
                        tum_veriler.extend(sonuc.get("results", []))

                # 3. Gemini ile Uzman Rapor (Ajan Modu)
                rapor_prompt = f"""
Sen Türkiye'nin en iyi alışveriş danışmanısın. Aşırı detaycı ve matematikselsin.

**Ürün Bilgisi:**
{urun_bilgisi}

**Kullanıcı İsteği:**
{ek_detay}

**Web'den Çekilen Ham Veriler:**
{json.dumps([{'title': r.get('title'), 'url': r.get('url'), 'content': r.get('content')[:500]} for r in tum_veriler], ensure_ascii=False, indent=2)}

Bu verilere göre **ultra profesyonel bir rapor** hazırla. Şu bölümleri mutlaka içersin:

1. **Ürün Kimlik Özeti** (Marka, Model, Özellikler)
2. **Güncel Fiyat Haritası** (En ucuzdan pahalıya tablo)
3. **Kupon & İndirim Analizi** (Hangi kodlar çalışıyor olabilir)
4. **Matematiksel Sepet Simülasyonu** (Farklı senaryolarla toplam maliyet)
5. **Risk & Tavsiye Matrisi** (Al / Bekle / Alternatif)
6. **Final Karar + Puan** (100 üzerinden)

Raporu çok düzenli, emoji ve markdown ile zenginleştir.
"""

                with st.spinner("Akıllı rapor oluşturuluyor..."):
                    rapor_payload = {"contents": [{"parts": [{"text": rapor_prompt}]}]}
                    rapor_resp = requests.post(url, json=rapor_payload, headers={"Content-Type": "application/json"})
                    final_rapor = rapor_resp.json()["candidates"][0]["content"]["parts"][0]["text"]

                    st.markdown("## 📊 Ultra Uzman Raporu")
                    st.markdown(final_rapor)

            except Exception as e:
                st.error("Sistem hatası")
                st.code(traceback.format_exc())
