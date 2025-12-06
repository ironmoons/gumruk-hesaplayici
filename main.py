import streamlit as st
import time
import random

# Sayfa Ayarları
st.set_page_config(page_title="Gümrük Hesaplayıcı (Demo)", page_icon="🚢", layout="centered")

# --- BAŞLIK KISMI ---
st.title("🚢 İhracat/İthalat Vergi Hesaplayıcı")
st.markdown("""
Bu araç, ürün detaylarına göre **Tahmini Gümrük Maliyeti** ve **GTİP Analizi** yapar.
*Veriler güncel mevzuat simülasyonudur.*
""")

# --- SOL MENÜ ---
with st.sidebar:
    st.header("⚙️ Operasyon Detayları")
    st.info("Bu sürüm Demo modundadır. API anahtarı gerektirmez.")
    doviz = st.radio("Para Birimi", ["USD ($)", "EUR (€)"])

# --- ANA FORM ---
with st.form("hesaplama_formu"):
    col1, col2 = st.columns(2)
    with col1:
        cikis = st.selectbox("Çıkış Ülkesi", ["Türkiye", "Çin", "Almanya", "ABD"])
    with col2:
        varis = st.selectbox("Varış Ülkesi", ["Almanya (AB)", "İngiltere", "ABD", "Türkiye"])
    
    urun_adi = st.text_input("Ürün Nedir?", placeholder="Örn: Pamuklu Tişört, Zeytinyağı, Makine Parçası...")
    fiyat = st.number_input(f"Fatura Tutarı ({doviz})", min_value=100, value=5000)
    
    hesapla_btn = st.form_submit_button("Analizi Başlat")

# --- HESAPLAMA MOTORU (YAPAY ZEKA TAKLİDİ) ---
def analizi_yap(urun, tutar, hedef_ulke):
    # Girilen metni küçült (büyük-küçük harf duyarlılığı için)
    text = urun.lower()
    
    # Varsayılan değerler
    gtip = "Diğer - 9999.99"
    gumruk_orani = 5  # %5 genel
    kdv_orani = 19    # %19 genel
    notlar = "Genel ticaret ürünü."
    risk = "Düşük"

    # --- SİMÜLASYON KURALLARI ---
    # 1. Tekstil Ürünleri
    if any(x in text for x in ["tişört", "tekstil", "kumaş", "pantolon", "gömlek", "pamuk"]):
        gtip = "6109.10 (Örme Giyim)"
        gumruk_orani = 12
        notlar = "Tekstil ürünlerinde 'Menşe Şahadetnamesi' kritiktir. Azo boyar madde testi gerekebilir."
        risk = "Orta (Test Gerekliliği)"
    
    # 2. Gıda Ürünleri
    elif any(x in text for x in ["gıda", "zeytinyağı", "fındık", "bisküvi", "meyve"]):
        gtip = "1509.20 (Bitkisel Yağlar / Gıda)"
        gumruk_orani = 0  # Genelde gıdada vergi düşüktür ama analiz şarttır
        kdv_orani = 7
        notlar = "Sağlık sertifikası ve karantina kontrolü zorunludur. Soğuk zincir gerektirebilir."
        risk = "Yüksek (Bozulabilir Ürün)"

    # 3. Elektronik
    elif any(x in text for x in ["telefon", "bilgisayar", "elektronik", "devre", "kablo"]):
        gtip = "8517.13 (Elektronik Cihazlar)"
        gumruk_orani = 0  # Teknoloji ürünlerinde genelde vergi yoktur (ITA anlaşması)
        notlar = "CE belgesi ve RoHS uygunluğu kesinlikle gereklidir."
        risk = "Orta"

    # 4. Makine / Metal
    elif any(x in text for x in ["makine", "çelik", "demir", "yedek parça", "motor"]):
        gtip = "8407.34 (Motor ve Aksam)"
        gumruk_orani = 2.7
        notlar = "Sanayi ürünü. ATR belgesi varsa AB ülkelerine vergi %0 olur."
    
    # Hedef Ülke AB ise ve Çıkış Türkiye ise (Gümrük Birliği)
    if hedef_ulke == "Almanya (AB)" and cikis == "Türkiye":
        if gumruk_orani > 0:
            notlar += " (Türkiye-AB Gümrük Birliği kapsamında ATR ile vergi %0'a düşebilir!)"
            gumruk_orani = 0  # ATR etkisi simülasyonu

    # Hesaplamalar
    gumruk_tutari = tutar * (gumruk_orani / 100)
    matrah = tutar + gumruk_tutari
    kdv_tutari = matrah * (kdv_orani / 100)
    toplam_maliyet = tutar + gumruk_tutari + kdv_tutari

    return {
        "gtip": gtip,
        "gumruk_orani": gumruk_orani,
        "gumruk_tutari": gumruk_tutari,
        "kdv_orani": kdv_orani,
        "kdv_tutari": kdv_tutari,
        "toplam": toplam_maliyet,
        "not": notlar,
        "risk": risk
    }

# --- SONUÇLARI GÖSTERME ---
if hesapla_btn:
    if len(urun_adi) < 3:
        st.error("Lütfen geçerli bir ürün adı giriniz.")
    else:
        # Sanki AI düşünüyormuş gibi bekleme efekti verelim
        with st.spinner('Veritabanı taranıyor ve mevzuat kontrol ediliyor...'):
            time.sleep(2) # 2 saniye bekle
            sonuc = analizi_yap(urun_adi, fiyat, varis)
        
        st.success("✅ Analiz Başarıyla Tamamlandı!")
        
        # Sonuç Kartları
        c1, c2, c3 = st.columns(3)
        c1.metric("Tahmini GTİP", sonuc["gtip"])
        c2.metric("Gümrük Vergisi", f"%{sonuc['gumruk_orani']}")
        c3.metric("Tahmini Risk", sonuc["risk"])
        
        st.markdown("---")
        
        # Maliyet Tablosu
        st.subheader("💰 Maliyet Dökümü")
        st.write(f"**Mal Bedeli:** {fiyat:,.2f} {doviz}")
        st.write(f"**+ Gümrük Vergisi:** {sonuc['gumruk_tutari']:,.2f} {doviz}")
        st.write(f"**+ KDV (İthalat):** {sonuc['kdv_tutari']:,.2f} {doviz}")
        st.markdown(f"### = Toplam Tahmini Maliyet: {sonuc['toplam']:,.2f} {doviz}")
        
        st.info(f"💡 **Uzman Notu:** {sonuc['not']}")
