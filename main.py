import streamlit as st
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Excel Entegrasyonlu Gümrük Hesaplayıcı", page_icon="📂", layout="wide")

st.title("📂 Excel Tabanlı Gümrük Maliyet Analizi")
st.markdown("""
Bu araç, yüklediğiniz **Excel dosyasındaki** ürünleri ve vergi oranlarını okuyarak maliyet hesabı yapar.
Veritabanı tamamen sizin kontrolünüzdedir.
""")

# --- YAN MENÜ: DOSYA YÜKLEME ---
with st.sidebar:
    st.header("1. Veri Kaynağı")
    uploaded_file = st.file_uploader("Vergi Listesi (Excel) Yükle", type=["xlsx", "xls"])
    
    st.info("💡 **İpucu:** Excel dosyanızda şu sütunlar olmalı:\n"
            "- Urun_Adi\n"
            "- GTIP\n"
            "- Gumruk_Vergisi\n"
            "- Ilave_Gumruk_Vergisi\n"
            "- OTV\n"
            "- KDV")

# --- ANA PROGRAM ---
if uploaded_file is not None:
    try:
        # Excel'i Oku
        df = pd.read_excel(uploaded_file)
        
        # Sütun isimlerini kontrol et (Hata önleyici)
        gerekli_sutunlar = ["Urun_Adi", "GTIP", "Gumruk_Vergisi", "Ilave_Gumruk_Vergisi", "OTV", "KDV"]
        eksik_sutunlar = [col for col in gerekli_sutunlar if col not in df.columns]
        
        if eksik_sutunlar:
            st.error(f"Excel dosyanızda şu sütun isimleri eksik: {eksik_sutunlar}")
            st.warning("Lütfen Excel başlıklarınızın yukarıdaki gibi (Türkçe karakter olmadan, bitişik) yazıldığından emin olun.")
        else:
            st.success("✅ Veritabanı Başarıyla Yüklendi!")
            
            # --- HESAPLAMA ARAYÜZÜ ---
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("2. Ürün Seçimi")
                # Excel'deki ürün isimlerini listeye koy
                secilen_urun_adi = st.selectbox("Listeden Ürün Seçiniz:", df["Urun_Adi"].unique())
                
                # Seçilen ürünün verilerini çek (Filter)
                secilen_veri = df[df["Urun_Adi"] == secilen_urun_adi].iloc[0]
                
                st.markdown("---")
                st.subheader("3. Sevkiyat Giderleri")
                mal_bedeli = st.number_input("Mal Bedeli (FOB - USD)", value=5000.0)
                navlun = st.number_input("Navlun (USD)", value=1000.0)
                sigorta = st.number_input("Sigorta (USD)", value=100.0)
                
                hesapla = st.button("HESAPLA", type="primary")

            with col2:
                if hesapla:
                    # --- OTOMATİK VERİ ÇEKME ---
                    gtip = secilen_veri["GTIP"]
                    gv_orani = secilen_veri["Gumruk_Vergisi"]
                    igv_orani = secilen_veri["Ilave_Gumruk_Vergisi"]
                    otv_orani = secilen_veri["OTV"]
                    kdv_orani = secilen_veri["KDV"]
                    
                    # --- HESAPLAMA MANTIĞI ---
                    cif_bedel = mal_bedeli + navlun + sigorta
                    
                    gv_tutari = cif_bedel * (gv_orani / 100)
                    igv_tutari = cif_bedel * (igv_orani / 100)
                    
                    # ÖTV Matrahı (CIF + GV + IGV)
                    otv_matrahi = cif_bedel + gv_tutari + igv_tutari
                    otv_tutari = otv_matrahi * (otv_orani / 100)
                    
                    # KDV Matrahı (Tüm vergiler dahil)
                    kdv_matrahi = otv_matrahi + otv_tutari
                    kdv_tutari = kdv_matrahi * (kdv_orani / 100)
                    
                    toplam_vergi = gv_tutari + igv_tutari + otv_tutari + kdv_tutari
                    toplam_maliyet = cif_bedel + toplam_vergi
                    
                    # --- SONUÇ GÖSTERİMİ ---
                    st.subheader(f"Analiz: {secilen_urun_adi} ({gtip})")
                    
                    # Kartlar
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Gümrük Vergisi", f"%{gv_orani}")
                    c2.metric("İlave Gümrük V.", f"%{igv_orani}")
                    c3.metric("ÖTV", f"%{otv_orani}")
                    c4.metric("KDV", f"%{kdv_orani}")
                    
                    st.divider()
                    
                    # Büyük Sonuç
                    st.markdown(f"""
                    <div style="background-color:#e8f5e9; padding:20px; border-radius:10px; border:1px solid #4caf50;">
                        <h3 style="color:#2e7d32; margin:0;">TOPLAM MALİYET: ${toplam_maliyet:,.2f}</h3>
                        <p style="margin:0;">(Toplam Ödenen Vergi: ${toplam_vergi:,.2f})</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Grafik
                    chart_data = pd.DataFrame({
                        "Kalem": ["Mal Bedeli", "Lojistik", "Vergiler"],
                        "Tutar": [mal_bedeli, navlun+sigorta, toplam_vergi]
                    })
                    st.bar_chart(chart_data, x="Kalem", y="Tutar")

    except Exception as e:
        st.error(f"Dosya okunurken bir hata oluştu: {e}")
else:
    # Dosya yüklenmemişse boş ekran yerine demo göster
    st.info("👈 Lütfen sol menüden Excel dosyanızı yükleyin.")
    st.markdown("""
    ### Excel Dosyanız Nasıl Olmalı?
    Aşağıdaki sütun
