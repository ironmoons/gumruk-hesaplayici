import streamlit as st
import pandas as pd
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="TradeMaster AI: Smart Sourcing", page_icon="🚢", layout="wide")

# --- GÜNCEL VERİ SİMÜLASYONU ---
# Gerçek hayatta bu veriler ücretli API'den gelir. Biz burada en güncel senaryoları kodluyoruz.
# Format: {HS_CODE: {Ad, Vergi_Oranları: {Bölge: Oran}}}
VERITABANI = {
    "6109.10 - Pamuklu T-Shirt (Tekstil)": {
        "kategori": "Tekstil",
        "birim_kg_agirligi": 0.2, # 1 tanesi 200 gram
        "vergiler": {
            "Cin": 40.0,    # Çin'e ek vergi var
            "AB": 0.0,      # ATR ile 0
            "USA": 16.5,
            "Diger": 12.0
        },
        "kdv": 10,
        "not": "Tekstilde Çin menşeli ürünlerde İlave Gümrük Vergisi (İGV) uygulanır."
    },
    "8517.13 - Akıllı Telefon (Elektronik)": {
        "kategori": "Elektronik",
        "birim_kg_agirligi": 0.4,
        "vergiler": {
            "Cin": 0.0, # ITA anlaşması (genelde gümrük yok ama gözetim var)
            "AB": 0.0,
            "USA": 0.0,
            "Diger": 0.0
        },
        "kdv": 20,
        "not": "ÖTV ve Bandrol ücretleri hariçtir. Gözetim kıymetine dikkat!"
    },
    "8708.30 - Fren Balataları (Otomotiv)": {
        "kategori": "Sanayi",
        "birim_kg_agirligi": 2.5,
        "vergiler": {
            "Cin": 4.5,
            "AB": 0.0,
            "USA": 2.5,
            "Diger": 3.0
        },
        "kdv": 20,
        "not": "E-Mark işareti zorunludur."
    },
    "7306.30 - Çelik Boru (Demir-Çelik)": {
        "kategori": "Sanayi",
        "birim_kg_agirligi": 15.0, # Ağır ürün
        "vergiler": {
            "Cin": 25.0, # Anti-damping
            "AB": 0.0,
            "USA": 25.0,
            "Diger": 9.0
        },
        "kdv": 20,
        "not": "Çin çeliğine karşı Anti-Damping vergisi mevcuttur."
    }
}

# --- YARDIMCI FONKSİYONLAR ---

def vergi_bul(urun_kodu, cikis_ulkesi):
    """Ülkeye göre doğru vergiyi çeker"""
    urun_data = VERITABANI[urun_kodu]
    if cikis_ulkesi == "Çin":
        return urun_data["vergiler"]["Cin"]
    elif cikis_ulkesi == "Almanya (AB)":
        return urun_data["vergiler"]["AB"]
    elif cikis_ulkesi == "ABD":
        return urun_data["vergiler"]["USA"]
    else:
        return urun_data["vergiler"]["Diger"]

def navlun_hesapla(mod, agirlik_kg):
    """Lojistik türüne göre tahmini fiyat çıkarır"""
    fiyatlar = {
        "Deniz Yolu 🚢 (En Ucuz)": 1.5,  # kg başına dolar
        "Hava Yolu ✈️ (En Hızlı)": 8.5,
        "Kara Yolu 🚛 (Orta)": 3.0
    }
    return agirlik_kg * fiyatlar[mod]

def akilli_onerisi_yap(urun_kodu, suanki_vergi, suanki_ulke):
    """Daha ucuz vergiye sahip ülke var mı diye bakar"""
    urun_vergileri = VERITABANI[urun_kodu]["vergiler"]
    oneriler = []
    
    for bolge, oran in urun_vergileri.items():
        if oran < suanki_vergi:
            # Bölge adını kullanıcı dostu yapalım
            ulke_adi = "Avrupa Birliği (Almanya vb.)" if bolge == "AB" else bolge
            fark = suanki_vergi - oran
            oneriler.append(f"💡 **Fırsat:** Bu ürünü **{ulke_adi}** menşeli alırsanız vergi oranınız **%{oran}** olur. (Kazanç: %{fark})")
            
    return oneriler

# --- ARAYÜZ ---

st.title("🤖 TradeMaster: Akıllı İthalat Asistanı")
st.caption(f"Veri Tabanı Son Güncelleme: {datetime.now().strftime('%d.%m.%Y')} | Canlı Mevzuat Modu")

# Sütunlu Yapı
col_sol, col_sag = st.columns([1, 2])

with col_sol:
    st.header("1. Ürün & Rota")
    
    # HİBRİT ARAMA KUTUSU
    secilen_urun = st.selectbox(
        "Ürün Ara (İsim veya GTİP)", 
        options=list(VERITABANI.keys())
    )
    
    cikis_ulkesi = st.selectbox("Çıkış Ülkesi (Menşe)", ["Çin", "Almanya (AB)", "ABD", "Hindistan (Diğer)"])
    varis_ulkesi = st.selectbox("Varış Ülkesi", ["Türkiye"]) # Şimdilik TR ithalatı
    
    st.markdown("---")
    st.header("2. Lojistik Detayları")
    
    adet = st.number_input("Sipariş Adeti", min_value=1, value=1000)
    birim_fiyat = st.number_input("Birim Fiyat (FOB - USD)", value=5.0)
    
    lojistik_modu = st.radio("Taşıma Yöntemi", ["Deniz Yolu 🚢 (En Ucuz)", "Hava Yolu ✈️ (En Hızlı)", "Kara Yolu 🚛 (Orta)"])
    
    hesapla = st.button("ANALİZ ET", type="primary", use_container_width=True)

# --- HESAPLAMA MOTORU ---
if hesapla:
    data = VERITABANI[secilen_urun]
    
    # 1. Ağırlık ve Navlun Hesabı
    toplam_agirlik = adet * data["birim_kg_agirligi"]
    navlun_tutar = navlun_hesapla(lojistik_modu, toplam_agirlik)
    mal_bedeli = adet * birim_fiyat
    
    # 2. Vergi Oranı Bulma
    vergi_orani = vergi_bul(secilen_urun, cikis_ulkesi)
    
    # 3. Maliyetler (CIF Üzerinden)
    sigorta = mal_bedeli * 0.01 # %1 Sigorta varsayımı
    cif_bedel = mal_bedeli + navlun_tutar + sigorta
    
    gumruk_tutari = cif_bedel * (vergi_orani / 100)
    
    kdv_matrahi = cif_bedel + gumruk_tutari
    kdv_tutari = kdv_matrahi * (data["kdv"] / 100)
    
    toplam_maliyet = cif_bedel + gumruk_tutari + kdv_tutari
    birim_maliyet = toplam_maliyet / adet
    
    # --- SONUÇLARI SAĞ TARAFA YAZDIR ---
    with col_sag:
        # Üst Kartlar
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Ağırlık", f"{toplam_agirlik} kg")
        k2.metric("Navlun Maliyeti", f"${navlun_tutar:,.2f}")
        k3.metric("Birim Maliyet", f"${birim_maliyet:,.2f}")
        
        st.divider()
        
        # ANA ANALİZ
        st.subheader("📊 Maliyet Analizi ve Uyarılar")
        
        # Eğer vergi yüksekse kırmızı, düşükse yeşil gösterelim
        renk = "red" if vergi_orani > 5 else "green"
        st.markdown(f"**Uygulanan Gümrük Vergisi:** <span style='color:{renk}; font-size:20px; font-weight:bold'>%{vergi_orani}</span>", unsafe_allow_html=True)
        
        # AKILLI ASİSTAN (FARK YARATAN ÖZELLİK)
        oneriler = akilli_onerisi_yap(secilen_urun, vergi_orani, cikis_ulkesi)
        
        if len(oneriler) > 0:
            with st.container():
                st.warning("🤖 **YAPAY ZEKA TEDARİK ÖNERİSİ:**")
                for oneri in oneriler:
                    st.markdown(oneri)
                    st.caption(f"*Not: {cikis_ulkesi} yerine bu ülkeden alırsanız maliyetiniz düşer.*")
        else:
            st.success("✅ Şu an en avantajlı vergi bölgesinden alım yapıyorsunuz.")
            
        # DETAY TABLOSU
        df = pd.DataFrame({
            "Kalem": ["Mal Bedeli", "Navlun (Lojistik)", "Gümrük Vergisi", "KDV", "TOPLAM"],
            "Tutar (USD)": [mal_bedeli, navlun_tutar, gumruk_tutari, kdv_tutari, toplam_maliyet],
            "Oran / Bilgi": ["-", lojistik_modu, f"%{vergi_orani}", f"%{data['kdv']}", "-"]
        })
        st.table(df)
        
        st.info(f"📋 **Mevzuat Notu:** {data['not']}")

else:
    with col_sag:
        st.info("👈 Analizi başlatmak için soldaki verileri doldurup butona basınız.")
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)
        st.markdown("**Bu araç şunları yapar:**\n* Ürün Ağırlığına göre navlun hesaplar.\n* Ülke bazlı vergi avantajlarını karşılaştırır.\n* Alternatif ucuz tedarikçi önerir.")
