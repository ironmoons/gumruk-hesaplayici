import streamlit as st
import pandas as pd
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Pro Trade: Gümrük Analiz", page_icon="globe_with_meridians", layout="wide")

# --- BAŞLIK ---
st.title("🌐 ProTrade: Akıllı İhracat Maliyet Analizi")
st.markdown("---")

# --- SOL MENÜ (GİRİŞLER) ---
with st.sidebar:
    st.header("📦 Ürün ve Sevkiyat Bilgileri")
    
    # Ülke Seçimi
    cikis_ulke = st.selectbox("Çıkış Ülkesi", ["Türkiye", "Çin", "Almanya"])
    varis_ulke = st.selectbox("Varış Ülkesi", ["Almanya (AB)", "ABD", "İngiltere", "Rusya"])
    
    st.markdown("---")
    
    # Ürün Girişi
    urun_input = st.text_input("Ürün Adı", placeholder="Örn: Pamuklu Tişört, Zeytinyağı...")
    mal_bedeli = st.number_input("Mal Bedeli (FOB - USD)", min_value=100, value=10000)
    
    # Ekstra Giderler
    navlun = st.number_input("Navlun (Nakliye) - USD", value=1500)
    sigorta = st.number_input("Sigorta - USD", value=150)
    
    hesapla_btn = st.button("ANALİZİ BAŞLAT", type="primary")

# --- GERÇEKÇİ VERİ TABANI (MOCK DATA) ---
# Buradaki veriler gerçek senaryolara yakın hazırlanmıştır.
DATABASE = {
    "tekstil": {
        "gtip": "6109.10",
        "ad": "Örme Giyim / T-Shirt",
        "gumruk_ab": 0,    # ATR ile 0
        "gumruk_usa": 16.5, # ABD tekstil vergisi yüksek
        "gumruk_diger": 12,
        "kdv": 19,
        "risk": "Menşe şahadetnamesi ve Azo boyar madde testi gerektirir."
    },
    "zeytin": {
        "gtip": "1509.10",
        "ad": "Saf Zeytinyağı",
        "gumruk_ab": 0, # Tarım ürünü olsa da bazı kotalar var, genelde 0 varsayalım
        "gumruk_usa": 3.4, # Şişelenmiş yağ
        "gumruk_diger": 10,
        "kdv": 7,
        "risk": "FDA kaydı (ABD için) ve Sağlık Sertifikası zorunludur."
    },
    "otomotiv": {
        "gtip": "8708.99",
        "ad": "Motorlu Taşıt Aksamı",
        "gumruk_ab": 0, # Sanayi ürünü ATR ile 0
        "gumruk_usa": 2.5,
        "gumruk_diger": 5,
        "kdv": 19,
        "risk": "Standart sanayi ürünü. CE belgesi gerekebilir."
    },
    "findik": {
        "gtip": "0802.22",
        "ad": "Kabuksuz Fındık",
        "gumruk_ab": 3, 
        "gumruk_usa": 0, # Bazı tarım ürünleri gümrüksüz olabilir
        "gumruk_diger": 5,
        "kdv": 7,
        "risk": "Aflatoksin analizi kesinlikle gereklidir."
    },
     "elektronik": {
        "gtip": "8517.13",
        "ad": "Akıllı Telefon / Elektronik",
        "gumruk_ab": 0, 
        "gumruk_usa": 0, 
        "gumruk_diger": 0, # ITA anlaşması gereği çoğu yerde 0
        "kdv": 20,
        "risk": "Batarya test raporları (MSDS) gereklidir."
    }
}

# --- HESAPLAMA FONKSİYONU ---
def get_data(search_text):
    search_text = search_text.lower()
    
    # Basit bir kelime eşleştirme
    if "tişört" in search_text or "giyim" in search_text or "pantolon" in search_text:
        return DATABASE["tekstil"]
    elif "zeytin" in search_text or "yag" in search_text or "yağ" in search_text:
        return DATABASE["zeytin"]
    elif "parça" in search_text or "motor" in search_text or "yedek" in search_text or "fren" in search_text:
        return DATABASE["otomotiv"]
    elif "fındık" in search_text or "findik" in search_text:
        return DATABASE["findik"]
    elif "telefon" in search_text or "bilgisayar" in search_text:
        return DATABASE["elektronik"]
    else:
        # Eşleşme yoksa varsayılan genel veri
        return {
            "gtip": "GENEL-00.00",
            "ad": "Diğer Ticari Eşya",
            "gumruk_ab": 2.7,
            "gumruk_usa": 5.0,
            "gumruk_diger": 10.0,
            "kdv": 20,
            "risk": "Ürün spesifik mevzuat kontrol edilmelidir."
        }

# --- EKRAN ÇIKTILARI ---
if hesapla_btn:
    if not urun_input:
        st.error("Lütfen bir ürün adı giriniz.")
    else:
        # İŞLEM BAŞLIYOR EFEKTİ
        with st.spinner('GTİP Veritabanı taranıyor...'):
            time.sleep(1)
        with st.spinner(f'{varis_ulke} gümrük mevzuatı kontrol ediliyor...'):
            time.sleep(1)

        # VERİLERİ ÇEK
        data = get_data(urun_input)
        
        # HEDEF ÜLKEYE GÖRE VERGİ SEÇİMİ
        secilen_vergi_orani = 0
        not_mesaji = ""
        
        if "Almanya" in varis_ulke:
            secilen_vergi_orani = data["gumruk_ab"]
            if cikis_ulke == "Türkiye" and data["gumruk_ab"] == 0:
                not_mesaji = "✅ Türkiye-AB Gümrük Birliği: ATR Belgesi ile Gümrük Vergisi %0 uygulanır."
        elif "ABD" in varis_ulke:
            secilen_vergi_orani = data["gumruk_usa"]
        else:
            secilen_vergi_orani = data["gumruk_diger"]

        # HESAPLAMALAR (CIF Üzerinden)
        cif_bedel = mal_bedeli + navlun + sigorta
        gumruk_tutari = cif_bedel * (secilen_vergi_orani / 100)
        
        kdv_matrahi = cif_bedel + gumruk_tutari
        kdv_tutari = kdv_matrahi * (data["kdv"] / 100)
        
        toplam_maliyet = cif_bedel + gumruk_tutari + kdv_tutari
        landing_cost_birim = toplam_maliyet / (mal_bedeli / 10) # Örnek birim hesabı

        # --- SONUÇ EKRANI (2 KOLONLU) ---
        col_ozet, col_grafik = st.columns([1, 2])

        with col_ozet:
            st.subheader("📋 Sonuç Kartı")
            st.info(f"Tespit Edilen Kategori:\n**{data['ad']}**")
            st.metric("GTİP Kodu", data['gtip'])
            st.metric("Uygulanan Gümrük Vergisi", f"%{secilen_vergi_orani}")
            st.metric("Tahmini KDV", f"%{data['kdv']}")
            
            st.error(f"⚠️ **Kritik Uyarı:**\n{data['risk']}")
            if not_mesaji:
                st.success(not_mesaji)

        with col_grafik:
            st.subheader("💰 Maliyet Dağılımı (Landed Cost)")
            
            # Grafik Verisi Hazırlama
            chart_data = pd.DataFrame({
                'Kalemler': ['Mal Bedeli', 'Lojistik (Navlun+Sigorta)', 'Gümrük Vergisi', 'KDV'],
                'Tutar (USD)': [mal_bedeli, (navlun+sigorta), gumruk_tutari, kdv_tutari]
            })
            
            st.bar_chart(chart_data, x='Kalemler', y='Tutar (USD)', color="#4CAF50")
            
            # Toplam Büyük Rakam
            st.markdown(f"""
            <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; text-align:center;">
                <h3>TOPLAM VARIŞ MALİYETİ</h3>
                <h1 style="color:#2e7d32;">${toplam_maliyet:,.2f}</h1>
                <p>(Ürün + Lojistik + Vergiler)</p>
            </div>
            """, unsafe_allow_html=True)
