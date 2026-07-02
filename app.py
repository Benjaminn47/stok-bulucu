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
ek_detay = st.text_input("Ekstra İstek / Detay", placeholder="45 numara, orijinal kutulu")

if st.button("🚀 Ultra Derin Analiz Başlat", use_container_width=True, type="primary"):
    if not yuklenen_fotograf or not GEMINI_API_KEY or not TAVILY_API_KEY:
        st.error("Fotoğraf ve API anahtarları gereklidir.")
    else:
        with st.spinner("Analiz + Araştırma + Rapor hazırlanıyor..."):
            try:
                image = Image.open(yuklenen_fotograf)
                st.image(image, caption="Analiz Edilen Ürün", use_column_width=True)

                buffered = io.BytesIO()
                img_format = image.format or "JPEG"
                image.save(buffered, format=img_format)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                mime_type = f"image/{img_format.lower()}"

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

                # Ürün tespiti
                urun_prompt = "Bu görseldeki ürünü detaylı analiz et: marka, model, renk, özellikler."
                payload = {"contents": [{"parts": [{"text": urun_prompt}, {"inline_data": {"mime_type": mime_type, "data": img_str}}]}]}
                urun_resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
                urun_bilgisi = urun_resp.json()["candidates"][0]["content"]["parts"][0]["text"]

                st.success("✅ Ürün Tespit Edildi")

                # Tavily Aramaları
                tavily = TavilyClient(api_key=TAVILY_API_KEY)
                aramalar = [
                    f"{urun_bilgisi[:70]} {ek_detay} Türkiye fiyat stok",
                    f"{urun_bilgisi[:70]} indirim kodu kupon",
                    f"{urun_bilgisi[:70]} en ucuz"
                ]

                tum_veriler = []
                for sorgu in aramalar:
                    sonuc = tavily.search(sorgu, search_depth="advanced", max_results=6)
                    tum_veriler.extend(sonuc.get("results", []))

                # Linkleri net şekilde veren rapor promptu
                rapor_prompt = f"""
Sen profesyonel bir alışveriş uzmanısın.

**Ürün:** {urun_bilgisi}
**Kullanıcı Talebi:** {ek_detay}

**Bulunan Satış Linkleri ve Bilgiler:**
{json.dumps([{'title': r.get('title',''), 'url': r.get('url',''), 'content': r.get('content','')[:300]} for r in tum_veriler], ensure_ascii=False, indent=2)}

Bu verilerden **çok detaylı ve link ağırlıklı** bir rapor hazırla. 

**Mutlaka** şunları yap:
- Her satıcı için **doğrudan link** ver
- Fiyatları tablo yap
- Hangi kuponların geçerli olabileceğini belirt
- Matematiksel maliyet karşılaştırması yap
- En iyi 3 öneriyi net şekilde vurgula

Raporu okunaklı, emoji ve markdown ile zenginleştir.
"""

                with st.spinner("Uzman rapor oluşturuluyor..."):
                    rapor_payload = {"contents": [{"parts": [{"text": rapor_prompt}]}]}
                    rapor_resp = requests.post(url, json=rapor_payload, headers={"Content-Type": "application/json"})
                    final_rapor = rapor_resp.json()["candidates"][0]["content"]["parts"][0]["text"]

                    st.markdown("## 📊 Ultra Uzman Raporu")
                    st.markdown(final_rapor)

            except Exception as e:
                st.error("Hata oluştu")
                st.code(traceback.format_exc())
