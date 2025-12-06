import streamlit as st
from openai import OpenAI

# Sayfa Düzeni
st.set_page_config(page_title="AI Gümrük Hesaplayıcı", page_icon="🌍", layout="centered")

# Başlıklar
st.title("🌍 Yapay Zeka Gümrük Vergisi Hesaplayıcı")
st.markdown("Bu araç, ürününüzün **GTİP kodunu** tahmin eder ve **tahmini maliyet** çıkarır.")
st.warning("⚠️ YASAL UYARI: Bu sonuçlar yapay zeka tahminidir. Kesin bilgi için gümrük müşavirine danışınız.")

# Yan Menü (API Key Girişi)
with st.sidebar:
    st.header("Ayarlar")
    api_key = st.text_input("OpenAI API Anahtarı", type="password", help="OpenAI sitesinden alacağınız sk-... ile başlayan kod.")
    st.markdown("[API Anahtarı Nereden Alınır?](https://platform.openai.com/api-keys)")
    st.info("Not: API anahtarınız kaydedilmez, sadece işlem anında kullanılır.")

# Ana Form
with st.form("gumruk_formu"):
    col1, col2 = st.columns(2)
    with col1:
        cikis_ulkesi = st.text_input("Çıkış Ülkesi", "Türkiye")
    with col2:
        varis_ulkesi = st.text_input("Varış Ülkesi", "Almanya")
    
    urun = st.text_area("Ürün Tanımı (Ne kadar detay, o kadar iyi)", "Örn: %100 Pamuklu örme erkek tişörtü, 250 gram")
    fiyat = st.number_input("Ürün Fatura Değeri (USD)", min_value=1, value=5000)
    
    hesapla = st.form_submit_button("💰 Vergiyi ve Maliyeti Hesapla")

# Hesaplama Mantığı
if hesapla:
    if not api_key:
        st.error("Lütfen sol menüden OpenAI API Anahtarınızı giriniz!")
    else:
        try:
            client = OpenAI(api_key=api_key)
            with st.spinner('Yapay zeka mevzuatları tarıyor...'):
                
                prompt = f"""
                Sen uzman bir gümrük müşavirisini. Aşağıdaki ticari işlem için bir analiz yap.
                
                Ürün: {urun}
                Çıkış: {cikis_ulkesi} -> Varış: {varis_ulkesi}
                Mal Bedeli: {fiyat} USD
                
                Lütfen şu formatta, TÜRKÇE ve tablo şeklinde yanıt ver:
                1. Tahmini GTİP (HS Code): (En uygun 6 haneli kodu bul)
                2. Gümrük Vergisi Oranı: (Varış ülkesi standartlarına göre tahmini %)
                3. KDV Oranı: (Varış ülkesi standartlarına göre tahmini %)
                4. Ek Vergiler: (Varsa anti-damping vb.)
                5. MALİYET TABLOSU:
                   - Mal Bedeli:
                   - Tahmini Gümrük Vergisi Tutarı:
                   - Tahmini KDV Tutarı:
                   - TOPLAM TAHMİNİ MALİYET (Landed Cost):
                
                Son olarak ihracatçının dikkat etmesi gereken 1 kritik belgeyi söyle (ATR, EUR1 vs.)
                """
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                sonuc = response.choices[0].message.content
                
                st.success("✅ Analiz Tamamlandı")
                st.markdown(sonuc)
                
        except Exception as e:
            st.error(f"Bir hata oluştu. API Anahtarınızı veya bakiyenizi kontrol edin. Hata: {e}")