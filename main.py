import streamlit as st
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gümrük Tarife Analizi (Fasıl 04)", page_icon="🥛", layout="wide")

st.title("🥛 Gümrük Tarife Cetveli Hesaplayıcısı (Fasıl 04)")
st.markdown("""
Bu araç, yüklediğiniz **Gümrük Tarife Cetveli (Excel/CSV)** dosyasını analiz eder. 
Dosyadaki **GTİP** ve **Vergi Haddi** sütunlarını otomatik bularak maliyet hesabı yapar.
""")

# --- YAN MENÜ: DOSYA YÜKLEME ---
with st.sidebar:
    st.header("1. Tarife Dosyası Yükle")
    uploaded_file = st.file_uploader("Fasıl Dosyası (CSV veya Excel)", type=["csv", "xlsx", "xls"])
    st.info("Sisteme '04 fasıl 2024' dosyanızı yükleyiniz.")

# --- VERİ TEMİZLEME VE OKUMA FONKSİYONU ---
def veriyi_temizle(file):
    try:
        # Dosya uzantısına göre oku
        if file.name.endswith('.csv'):
            # Senin dosyanın formatına özel okuma ayarları
            df = pd.read_csv(file, header=None, skiprows=4) 
        else:
            df = pd.read_excel(file, header=None, skiprows=4)
        
        # Sadece işimize yarayan sütunları alalım (Dosya yapına göre)
        # 0: GTİP, 1: Tanım, 3: Vergi Oranı (Genelde en sağdaki dolu sütun)
        df_clean = df.iloc[:, [0, 1, 3]] 
        df_clean.columns = ["GTIP", "Tanim", "Vergi_Orani"]
        
        # Vergi oranı boş olan satırları (Başlıkları) at
        df_clean = df_clean.dropna(subset=["Vergi_Orani"])
        
        # Vergi oranını sayıya çevir (Hata verenleri temizle)
        df_clean["Vergi_Orani"] = pd.to_numeric(df_clean["Vergi_Orani"], errors='coerce')
        
        # GTİP boş olanları at
        df_clean = df_clean.dropna(subset=["GTIP"])
        
        # Tanımı ve GTİP'i birleştirip arama sütunu yap
        df_clean["Arama"] = df_clean["GTIP"].astype(str) + " - " + df_clean["Tanim"].astype(str)
        
        return df_clean
    except Exception as e:
        st.error(f"Dosya formatı okunamadı. Hata: {e}")
        return None

# --- ANA PROGRAM ---
if uploaded_file is not None:
    df = veriyi_temizle(uploaded_file)
    
    if df is not None:
        st.success(f"✅ Dosya Başarıyla İşlendi! {len(df)} adet ürün kodu bulundu.")
        
        # --- HESAPLAMA ARAYÜZÜ ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("2. Ürün Seçimi")
            
            # ARAMA KUTUSU (SELECTBOX)
            secilen_urun_string = st.selectbox(
                "Listeden GTİP veya Ürün Adı Arayın:", 
                options=df["Arama"].tolist()
            )
            
            # Seçilen satırın verilerini çek
            secilen_veri = df[df["Arama"] == secilen_urun_string].iloc[0]
            
            st.info(f"**Seçilen Ürün:**\n{secilen_veri['Tanim']}")
            
            st.markdown("---")
            st.subheader("3. Maliyet Verileri")
            mal_bedeli = st.number_input("Mal Bedeli (FOB - USD)", value=10000.0, step=100.0)
            navlun = st.number_input("Navlun (Nakliye - USD)", value=1500.0)
            sigorta = st.number_input("Sigorta (USD)", value=150.0)
            
            # Dosyada sadece Gümrük Vergisi var, KDV'yi kullanıcıya soralım
            kdv_orani = st.number_input("KDV Oranı (%)", value=10.0, help="Gıda ürünlerinde genelde %1, %10 veya %20'dir.")
            
            hesapla = st.button("MALİYET HESAPLA", type="primary")

        with col2:
            if hesapla:
                # --- VERİLERİ DOSYADAN AL ---
                gtip_kodu = secilen_veri["GTIP"]
                gv_orani = secilen_veri["Vergi_Orani"] # Dosyadan gelen oran (Örn: 200.0)
                
                # --- HESAPLAMA MANTIĞI ---
                
                # 1. CIF Bedel
                cif_bedel = mal_bedeli + navlun + sigorta
                
                # 2. Gümrük Vergisi (Tarım ürünlerinde dosyadaki oran çok yüksek olabilir)
                gv_tutari = cif_bedel * (gv_orani / 100)
                
                # 3. KDV Matrahı (CIF + Gümrük Vergisi)
                kdv_matrahi = cif_bedel + gv_tutari
                kdv_tutari = kdv_matrahi * (kdv_orani / 100)
                
                # 4. Toplamlar
                toplam_vergi = gv_tutari + kdv_tutari
                toplam_maliyet = cif_bedel + toplam_vergi
                
                # --- SONUÇ EKRANI ---
                st.subheader(f"📊 Analiz Sonucu: {gtip_kodu}")
                
                # Uyarı: Tarım Ürünü Yüksek Vergi
                if gv_orani > 50:
                    st.warning(f"⚠️ DİKKAT: Bu ürün için dosyadaki vergi oranı **%{gv_orani}**. Tarım ürünlerinde koruma amaçlı yüksek vergiler normaldir.")
                
                # Kartlar
                c1, c2, c3 = st.columns(3)
                c1.metric("Gümrük Vergisi Oranı", f"%{gv_orani}")
                c2.metric("Ödenecek Toplam Vergi", f"${toplam_vergi:,.0f}", delta_color="inverse")
                c3.metric("TOPLAM MALİYET", f"${toplam_maliyet:,.0f}")
                
                st.divider()
                
                # Tablo
                data = {
                    "Kalem": ["Mal Bedeli", "Navlun + Sigorta", "Gümrük Vergisi (Dosyadan)", "KDV", "GENEL TOPLAM"],
                    "Tutar ($)": [mal_bedeli, navlun+sigorta, gv_tutari, kdv_tutari, toplam_maliyet],
                    "Oran": ["-", "-", f"%{gv_orani}", f"%{kdv_orani}", "-"]
                }
                st.dataframe(pd.DataFrame(data), use_container_width=True)
                
                # Grafik
                st.subheader("💰 Maliyet Dağılımı")
                chart_data = pd.DataFrame({
                    "Kategori": ["Ürün Bedeli", "Lojistik", "Vergiler"],
                    "Tutar": [mal_bedeli, navlun+sigorta, toplam_vergi]
                })
                st.bar_chart(chart_data, x="Kategori", y="Tutar", color="#FF4B4B")

else:
    st.info("👈 Lütfen sol taraftan '04 fasıl 2024' dosyanızı yükleyin.")
    st.markdown("""
    ### Bu Araç Nasıl Çalışır?
    1. Attığınız dosyadaki karmaşık tabloyu temizler.
    2. **GTİP** kodlarını ve karşısındaki **Vergi Haddi** (Örn: %200) sütununu okur.
    3. Siz ürünü seçince, o ürüne ait özel vergiyi dosyadan çekip hesabı yapar.
    """)
