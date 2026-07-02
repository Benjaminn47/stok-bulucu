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

yuklenen_fotograf = st.file_uploader("Ürün Fotoğrafı Yükleyin 📸", type=["jpg", "jpeg", "png"])
ek_detay = st.text_input("Ekstra İstek / Detay", placeholder="45 numara, orijinal, en ucuz satıcı")

if st.button("🚀 Ultra Derin Analiz Başlat", use_container_width=True, type="primary"):
    if not yuklenen_fotograf or not GEMINI_API_KEY or not TAVILY_API_KEY:
        st.error("Fotoğraf ve API anahtarları gereklidir.")
    else:
        with st.spinner("Görsel analiz + Derin araştırmalar yapılıyor..."):
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
                urun_prompt = "Bu görseldeki ürünü detaylı analiz et: marka, tam model adı, renk, ana özellikler."
                payload = {"contents": [{"parts": [{"text": urun_prompt}, {"inline_data": {"mime_type": mime_type, "data": img_str}}]}]}
                
                urun_resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                urun_bilgisi = urun_resp.json()["candidates"][0]["content"]["parts"][0]["text"]

                st.success(f"✅ Ürün Tespit Edildi: {urun_bilgisi[:100]}...")

                # 2. Tavily Aramaları (Kısaltılmış Query)
                tavily = TavilyClient(api_key=TAVILY_API_KEY)
                
                aramalar = [
                    f"{urun_bilgisi[:80]} {ek_detay} Türkiye fiyat stok",
                    f"{urun_bilgisi[:80]} indirim kodu kupon",
                    f"{urun_bilgisi[:80]} en ucuz satıcı"
                ]

                tum_veriler = []
                for i, sorgu in enumerate(aramalar, 1):
                    with st.spinner(f"Arama katmanı {i}/3..."):
                        sonuc = tavily.search(sorgu, search_depth="advanced", max_results=5)
                        tum_veriler.extend(sonuc.get("results", []))

                # 3. Uzman Rapor (Gemini Ajan)
                rapor_prompt = f"""
Sen Türkiye'nin en iyi e-ticaret alışveriş danışmanısın.

**Ürün:** {urun_bilgisi}
**Kullanıcı Talebi:** {ek_detay}

**Web Arama Sonuçları:**
{json.dumps([{'title': r.get('title',''), 'url': r.get('url',''), 'content': r.get('content','')[:400]} for r in tum_veriler], ensure_ascii=False)}

Bu verilerden yola çıkarak **ultra profesyonel rapor** hazırla. Şu başlıkları mutlaka kullan:

1. **Ürün Kimliği ve Özellikleri**
2. **Fiyat Karşılaştırma Tablosu** (En iyi 4-5 seçenek)
3. **Kupon & Promosyon Analizi**
4. **Matematiksel Maliyet Simülasyonu** (farklı senaryolar)
5. **Risk Değerlendirmesi**
6. **Final Tavsiye + Puan (100 üzerinden)**

Raporu emoji, tablo ve net önerilerle zenginleştir.
"""

                with st.spinner("Uzman rapor hazırlanıyor..."):
                    rapor_payload = {"contents": [{"parts": [{"text": rapor_prompt}]}]}
                    rapor_resp = requests.post(url, json=rapor_payload, headers={"Content-Type": "application/json"})
                    final_rapor = rapor_resp.json()["candidates"][0]["content"]["parts"][0]["text"]

                    st.markdown("## 📊 Ultra Uzman Rapor")
                    st.markdown(final_rapor)

            except Exception as e:
                st.error("Hata oluştu")
                st.code(traceback.format_exc())
