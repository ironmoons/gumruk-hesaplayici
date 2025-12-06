import streamlit as st
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Customs Pro: Kesin Hesaplayıcı", page_icon="🧮", layout="wide")

# --- BAŞLIK ---
st.title("🧮 Gümrük Vergisi & Maliyet Hesaplama Uzmanı")
st.info("""
**Neden Manuel Giriş?** Gümrük vergileri ürünün GTİP koduna, menşeine ve güncel kararnamelere göre her gün değişir. 
En doğru sonuç için vergiyi resmi kaynaktan öğrenip aşağıya giriniz. Biz karmaşık matrah hesabını yapacağız.
""")

# --- LİNKLER (KULLANICIYA YARDIM) ---
with st.expander("🔍 Gümrük Vergisi Oranını Nereden Bulurum? (Resmi Linkler)"):
    st.markdown("""
    1. **Ticaret Bakanlığı (Tarife Arama):** [Tıklayın ve GTİP Arayın](https://uygulama.gtb.gov.tr/Tara)
    2. **Mevzuat Bilgi Sistemi:** [İthalat Rejimi Kararı](https://www.mevzuat.gov.tr/)
    3. **AB Access2Markets:** [Avrupa Pazarı İçin Sorgulama](https://trade.ec.europa.eu/access-to-markets/en/home)
    """)

# --- HESAPLAMA MOTORU ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. Ürün ve Fiyat")
    urun_adi = st.text_input("Ürün Adı (Opsiyonel)", "Örn: Akıllı Saat")
    mal_bedeli = st.number_input("Mal Bedeli (FOB - USD)", min_value=1.0, value=10000.0, step=100.0)
    
    st.markdown("---")
    st.header("2. Lojistik (CIF Oluşumu)")
    navlun = st.number_input("Navlun (Nakliye - USD)", value=2000.0)
    sigorta = st.number_input("Sigorta (USD)", value=150.0)
    
    st.markdown("---")
    st.header("3. Vergi Oranları (%)")
    st.caption("Lütfen bulduğunuz güncel oranları giriniz.")
    
    gv_orani = st.number_input("Gümrük Vergisi (%)", value=0.0, help="AB ülkeleri için genelde 0, Çin için yüksektir.")
    igv_orani = st.number_input("İlave Gümrük Vergisi - İGV (%)", value=0.0, help="Çin, Hindistan vb. ülkeler için ek vergi.")
    otv_orani = st.number_input("ÖTV (%)", value=0.0, help="Lüks ürün, Araba, Telefon, Parfüm vb. için.")
    kdv_orani = st.number_input("KDV (%)", value=20.0)
    
    antrepo_ardiye = st.number_input("Tahmini Lokal Masraflar (Ardiye/Ordino - USD)", value=300.0)

    hesapla = st.button("HESAPLA", type="primary", use_container_width=True)

with col2:
    if hesapla:
        # --- MATEMATİK (TÜRKİYE GÜMRÜK MEVZUATI) ---
        
        # 1. CIF BEDEL (Verginin temeli)
        cif_bedel = mal_bedeli + navlun + sigorta
        
        # 2. Gümrük Vergisi (CIF üzerinden)
        gv_tutari = cif_bedel * (gv_orani / 100)
        
        # 3. İGV (CIF üzerinden)
        igv_tutari = cif_bedel * (igv_orani / 100)
        
        # 4. ÖTV MATRAHI (CIF + GV + İGV) -> Burası çok kritiktir, verginin vergisi!
        otv_matrahi = cif_bedel + gv_tutari + igv_tutari
        otv_tutari = otv_matrahi * (otv_orani / 100)
        
        # 5. KDV MATRAHI (ÖTV Matrahı + ÖTV Tutarı + Lokal Giderler kısmen)
        # Basitlik adına lokal giderleri matraha eklemiyoruz ama pratikte etkisi olur.
        kdv_matrahi = otv_matrahi + otv_tutari 
        kdv_tutari = kdv_matrahi * (kdv_orani / 100)
        
        # 6. TOPLAM VERGİLER
        toplam_vergi = gv_tutari + igv_tutari + otv_tutari + kdv_tutari
        
        # 7. SONUÇ (Landed Cost)
        toplam_maliyet = cif_bedel + toplam_vergi + antrepo_ardiye
        
        # --- GÖRSELLEŞTİRME ---
        st.success("✅ Hesaplama Başarıyla Tamamlandı")
        
        # Büyük Kartlar
        c_a, c_b, c_c = st.columns(3)
        c_a.metric("Mal Bedeli", f"${mal_bedeli:,.2f}")
        c_b.metric("Toplam Vergi Yükü", f"${toplam_vergi:,.2f}", delta_color="inverse")
        c_c.metric("TOPLAM MALİYET", f"${toplam_maliyet:,.2f}")
        
        st.divider()
        
        # Detay Tablosu (Fatura Gibi)
        st.subheader("🧾 Maliyet Dökümü")
        df = pd.DataFrame({
            "Kalem": [
                "1. Mal Bedeli (FOB)", 
                "2. Navlun + Sigorta", 
                "=== CIF BEDEL ===", 
                f"3. Gümrük Vergisi (%{gv_orani})", 
                f"4. İGV (%{igv_orani})", 
                f"5. ÖTV (%{otv_orani}) [Matrahlı]", 
                f"6. KDV (%{kdv_orani}) [Matrahlı]",
                "7. Lokal Masraflar (Ardiye vb.)",
                "=== GENEL TOPLAM ==="
            ],
            "Tutar ($)": [
                mal_bedeli, 
                navlun+sigorta, 
                cif_bedel, 
                gv_tutari, 
                igv_tutari, 
                otv_tutari, 
                kdv_tutari,
                antrepo_ardiye,
                toplam_maliyet
            ]
        })
        st.dataframe(df, use_container_width=True)
        
        # Grafik
        st.subheader("📊 Paranız Nereye Gidiyor?")
        chart_data = pd.DataFrame({
            "Kategori": ["Ürün Bedeli", "Lojistik", "Devlet (Vergiler)", "Lokal Masraf"],
            "Tutar": [mal_bedeli, navlun+sigorta, toplam_vergi, antrepo_ardiye]
        })
        st.bar_chart(chart_data, x="Kategori", y="Tutar", color="#FF4B4B")
        
    else:
        st.info("👈 Soldaki panelden vergi oranlarını girip 'Hesapla' butonuna basınız.")
        st.write("Örnek Senaryo: Çin'den Tişört alıyorsan GV: %12, İGV: %20, KDV: %10 gir.")
