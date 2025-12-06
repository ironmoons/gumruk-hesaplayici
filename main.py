import streamlit as st
import pandas as pd
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ProCustoms: Global Vergi Uzmanı", page_icon="globe_with_meridians", layout="wide")

# --- GERÇEKÇİ VERİTABANI (2024-2025 Simülasyonu) ---
# Türkiye İthalat Rejimine Göre Hazırlanmıştır.
# gv: Gümrük Vergisi, igv: İlave Gümrük Vergisi (Özellikle Çin vb. için), otv: Özel Tüketim Vergisi
VERITABANI = {
    "8703.80 - Elektrikli Otomobil (TOGG/Tesla vb.)": {
        "gv_genel": 10,  "igv_cin": 40, "otv": 10, "kdv": 20, 
        "risk": "Çin menşeli elektrikli araçlarda %40 Ek Vergi ve 7 Bölge Servis Şartı vardır."
    },
    "6109.10 - Pamuklu T-Shirt (Tekstil)": {
        "gv_genel": 12, "igv_cin": 20, "otv": 0, "kdv": 10,
        "risk": "Tekstil ürünlerinde referans fiyat uygulaması vardır. İGV yüksektir."
    },
    "8517.13 - Akıllı Telefon (Cep Telefonu)": {
        "gv_genel": 0, "igv_cin": 0, "otv": 50, "kdv": 20, # Telefonlarda ÖTV çok yüksektir
        "risk": "Kültür fonu payı ve TRT bandrolü hesaplamaya dahil edilmemiştir (Ekstra %10-12 maliyet bindirir)."
    },
    "1509.10 - Zeytinyağı (Gıda)": {
        "gv_genel": 10, "igv_cin": 0, "otv": 0, "kdv": 1,
        "risk": "Tarım ve Orman Bakanlığı uygunluk yazısı şarttır."
    },
    "8471.30 - Laptop / Dizüstü Bilgisayar": {
        "gv_genel": 0, "igv_cin": 0, "otv": 0, "kdv": 20,
        "risk": "Gümrük vergisi %0'dır (ITA Anlaşması). Sadece KDV ödenir."
    },
    "9503.00 - Plastik Oyuncak": {
        "gv_genel": 4.7, "igv_cin": 15, "otv": 20, "kdv": 20,
        "risk": "Oyuncaklarda ÖTV vardır ve ağır metal testleri (Tareks) zorunludur."
    },
    "7306.30 - Çelik Boru (Sanayi)": {
        "gv_genel": 9, "igv_cin": 15, "otv": 0, "kdv": 20,
        "risk": "Anti-Damping önlemlerine tabidir."
    }
}

# --- ÜLKE GRUPLARI ---
ULKELER = {
    "AB Ülkeleri (Almanya, İtalya, Fransa...)": {"tip": "AB"},
    "Güney Kore (STA)": {"tip": "STA"},
    "İngiltere (STA)": {"tip": "STA"},
    "Çin Halk Cumhuriyeti": {"tip": "CIN"},
    "ABD": {"tip": "DIGER"},
    "Hindistan": {"tip": "DIGER"},
    "Diğer Ülkeler": {"tip": "DIGER"}
}

# --- YARDIMCI HESAPLAMA FONKSİYONLARI ---
def vergi_oranlarini_getir(urun_kodu, mense_ulke):
    urun = VERITABANI[urun_kodu]
    ulke_tipi = ULKELER[mense_ulke]["tip"]
    
    # Baz Oranlar
    uygulanan_gv = urun["gv_genel"]
    uygulanan_igv = 0 # İlave Gümrük Vergisi
    
    # Senaryolar
    if ulke_tipi == "AB":
        uygulanan_gv = 0 # Gümrük Birliği (ATR)
        uygulanan_igv = 0
    elif ulke_tipi == "STA": # Serbest Ticaret Anlaşması olan ülkeler
        uygulanan_gv = 0
        uygulanan_igv = 0
    elif ulke_tipi == "CIN":
        uygulanan_igv = urun["igv_cin"] # Çin'e özel ek vergi
        
    return uygulanan_gv, uygulanan_igv, urun["otv"], urun["kdv"]

def navlun_tahmini(tasima_tipi, ulke_adi):
    # Basit bir simülasyon katsayısı
    baz_fiyat = 1000 # Başlangıç
    if "Çin" in ulke_adi or "Hindistan" in ulke_adi:
        carpan = 3.5 if tasima_tipi == "Hava" else 1.2
    elif "AB" in ulke_adi:
        carpan = 1.0 if tasima_tipi == "Kara" else 0.5 # Gemi çok ucuz AB'den
    elif "ABD" in ulke_adi:
        carpan = 4.0 if tasima_tipi == "Hava" else 1.8
    else:
        carpan = 2.0
        
    return baz_fiyat * carpan

# --- ARAYÜZ ---
st.title("🚀 ProCustoms: İthalat Maliyet Hesaplayıcı")
st.markdown("**Not:** Bu araç Türkiye İthalat Rejimi'ndeki 'Matrah Zinciri' (Verginin vergisi) kuralına göre çalışır.")

# SOL MENÜ
with st.sidebar:
    st.header("1. Sevkiyat Bilgileri")
    secilen_urun = st.selectbox("GTİP ve Ürün Seçimi", list(VERITABANI.keys()))
    mense_ulke = st.selectbox("Çıkış Ülkesi (Menşe)", list(ULKELER.keys()))
    
    st.markdown("---")
    st.header("2. Maliyet Kalemleri")
    mal_bedeli = st.number_input("Mal Bedeli (FOB - USD)", value=10000, step=100)
    tasima_modu = st.radio("Nakliye Yöntemi", ["Deniz", "Hava", "Kara"])
    
    # Kullanıcı navlunu elle girmek isterse diye
    otomatik_navlun = st.checkbox("Navlunu Otomatik Hesapla", value=True)
    if otomatik_navlun:
        navlun = navlun_tahmini(tasima_modu, mense_ulke)
        st.info(f"Tahmini Navlun: ${navlun:,.2f}")
    else:
        navlun = st.number_input("Navlun Tutarı (USD)", value=1500)
        
    sigorta = st.number_input("Sigorta Tutarı (USD)", value=150)
    
    hesapla = st.button("HESAPLA VE ANALİZ ET", type="primary")

# ANA EKRAN
if hesapla:
    # 1. ORANLARI BELİRLE
    gv_orani, igv_orani, otv_orani, kdv_orani = vergi_oranlarini_getir(secilen_urun, mense_ulke)
    
    # 2. HESAPLAMA MANTIĞI (Doğru Gümrük Formülü)
    cif_bedel = mal_bedeli + navlun + sigorta
    
    # a) Gümrük Vergisi Tutarı
    gumruk_vergisi_tutari = cif_bedel * (gv_orani / 100)
    
    # b) İlave Gümrük Vergisi (İGV) Tutarı
    igv_tutari = cif_bedel * (igv_orani / 100)
    
    # c) ÖTV Matrahı = CIF + GV + İGV
    otv_matrahi = cif_bedel + gumruk_vergisi_tutari + igv_tutari
    otv_tutari = otv_matrahi * (otv_orani / 100)
    
    # d) KDV Matrahı = CIF + GV + İGV + ÖTV (Verginin Vergisi)
    kdv_matrahi = otv_matrahi + otv_tutari
    kdv_tutari = kdv_matrahi * (kdv_orani / 100)
    
    # e) Toplamlar
    toplam_vergi = gumruk_vergisi_tutari + igv_tutari + otv_tutari + kdv_tutari
    toplam_maliyet = cif_bedel + toplam_vergi
    
    # --- SONUÇLARI GÖSTER ---
    st.subheader(f"Analiz Raporu: {secilen_urun.split('-')[1]}")
    
    # KARTLAR
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CIF Bedel (Mal+Nakliye)", f"${cif_bedel:,.0f}")
    c2.metric("Toplam Ödenecek Vergi", f"${toplam_vergi:,.0f}", delta_color="inverse")
    c3.metric("Vergi Yükü Oranı", f"%{(toplam_vergi/cif_bedel)*100:.1f}")
    c4.metric("TOPLAM MALİYET", f"${toplam_maliyet:,.0f}")
    
    st.markdown("---")
    
    # DETAY TABLOSU (HESAP DÖKÜMÜ)
    col_table, col_advice = st.columns([2, 1])
    
    with col_table:
        st.write("#### 🧾 Detaylı Vergi Hesap Dökümü (Gümrük Beyannamesi Taslağı)")
        data = {
            "Kalem": ["Mal Bedeli (FOB)", "Navlun + Sigorta", "CIF BEDEL (Vergi Matrahı)", 
                      f"Gümrük Vergisi (%{gv_orani})", f"İlave Gümrük Vergisi (%{igv_orani})", 
                      f"ÖTV (%{otv_orani})", f"KDV (%{kdv_orani})", "TOPLAM"],
            "Tutar ($)": [mal_bedeli, navlun+sigorta, cif_bedel, 
                          gumruk_vergisi_tutari, igv_tutari, otv_tutari, kdv_tutari, toplam_maliyet],
            "Açıklama": ["Ürün Faturası", "Lojistik Gider", "Vergilerin hesaplandığı taban fiyat", 
                         "Temel Vergi", "Ek Koruma Vergisi", "Lüks/Özel Tüketim", "Katma Değer Vergisi", "Cebinizden çıkacak toplam para"]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    with col_advice:
        st.write("#### 💡 Akıllı Tavsiyeler")
        
        # Risk Uyarısı
        st.warning(f"**Mevzuat Riski:** {VERITABANI[secilen_urun]['risk']}")
        
        # Karşılaştırmalı Analiz (Alternative Sourcing)
        if igv_orani > 0:
            st.error(f"⚠️ DİKKAT: Seçtiğiniz ülkeden (Çin vb.) bu ürünü getirmek pahalıdır. %{igv_orani} İlave Gümrük Vergisi ödüyorsunuz.")
            st.success("✅ TAVSİYE: Bu ürünü 'AB Ülkeleri' veya 'Güney Kore'den alırsanız İGV ödemez, maliyeti düşürürsünüz.")
        elif gv_orani == 0 and mense_ulke != "Diğer Ülkeler":
             st.success("✅ HARİKA: Gümrük Birliği veya STA avantajından yararlanıyorsunuz. Gümrük Vergisi %0.")

else:
    st.info("👈 Lütfen soldan ürün ve ülke seçip hesaplaya basın.")

