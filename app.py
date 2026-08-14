import streamlit as st
import pandas as pd
import math

# --- 1. ARAYÜZ VE BAŞLIK ---
st.set_page_config(page_title="Altyapı Yaklaşık Maliyet Motoru", layout="wide", page_icon="🏗️")
st.title("🚧 Altyapı Metraj ve Kârsız Yaklaşık Maliyet Motoru")
st.markdown("İdarelerin (İLBANK/KGM) yayınladığı resmi kârsız birim fiyatları baz alarak metraj ve maliyet hesaplar.")

# --- 2. VERİ YÜKLEME ---
st.sidebar.header("1. Fiyat Veritabanı (Excel)")
uploaded_file = st.sidebar.file_uploader("Birim Fiyat Excel Dosyasını Yükleyin", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Excel'i oku
    df_fiyatlar = pd.read_excel(uploaded_file)
    
    # Sabit sütunları ayırarak sadece fiyat içeren dönem sütunlarını bul
    sabit_sutunlar = ['SIRA NO', 'POZ NO', 'İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI', 'BİRİMİ']
    donem_sutunlari = [col for col in df_fiyatlar.columns if col not in sabit_sutunlar]
    
    # Poz Listesini Sözlüğe Çevir (Kolay seçim arayüzü için)
    poz_listesi = df_fiyatlar['POZ NO'].astype(str).tolist()
    
    # --- 3. KULLANICI GİRİŞ PARAMETRELERİ ---
    st.sidebar.header("2. Metraj Parametreleri")
    
    # Kullanıcı sadece Excel'de var olan dönemleri seçebilir
    secilen_donem = st.sidebar.selectbox("Fiyat Dönemini Seçin", donem_sutunlari)
    
    uzunluk = st.sidebar.number_input("Hat Uzunluğu (m)", min_value=0.0, value=100.0)
    derinlik = st.sidebar.number_input("Ortalama Kazı Derinliği (m)", min_value=0.0, value=2.0)
    cap_mm = st.sidebar.number_input("Boru Çapı (mm)", min_value=100, value=300, step=100)
    zemin_tipi = st.sidebar.selectbox("Zemin Tipi", ["Yeşil Alan", "Sert Zemin (Asfalt/Beton)"])
    
    st.sidebar.header("3. Kullanılacak Pozlar (Eşleştirme)")
    st.sidebar.info("Excel'inizdeki nakliye ve imalat pozlarını eşleştirin.")
    kazi_pozu = st.sidebar.selectbox("Kazı Pozu", poz_listesi)
    boru_pozu = st.sidebar.selectbox("Boru Pozu", poz_listesi)
    kum_pozu = st.sidebar.selectbox("Yataklama (Kum) Pozu", poz_listesi)
    dolgu_pozu = st.sidebar.selectbox("Geri Dolgu Pozu", poz_listesi)
    
    # Nakliye Pozları
    nakliye_pozu_1 = st.sidebar.selectbox("Nakliye Pozu 1 (Örn: Kazı/Dolgu Nakliyesi)", ["Seçilmedi"] + poz_listesi)
    nakliye_metraj_1 = st.sidebar.number_input("Nakliye 1 Miktarı (m3/ton)", min_value=0.0, value=0.0)
    
    asfalt_kesme_pozu, asfalt_kirma_pozu = None, None
    if "Sert Zemin" in zemin_tipi:
        asfalt_kesme_pozu = st.sidebar.selectbox("Asfalt Kesme Pozu", ["Seçilmedi"] + poz_listesi)
        asfalt_kirma_pozu = st.sidebar.selectbox("Asfalt Kırma Pozu", ["Seçilmedi"] + poz_listesi)

    # --- 4. HESAPLAMA MOTORU ---
    if st.button("Yaklaşık Maliyeti Çıkar", type="primary", use_container_width=True):
        # 1. Geometrik Kesit ve Şev Hesabı
        cap_m = cap_mm / 1000.0
        taban_genisligi = cap_m + 0.60 
        
        if derinlik > 1.50: 
            ekstra_genislik = (derinlik - 1.50) * (1/3) * 2
            ortalama_genislik = taban_genisligi + (ekstra_genislik / 2)
        else:
            ortalama_genislik = taban_genisligi

        # 2. Hacim (Metraj) Hesapları
        kazi_hacmi = ortalama_genislik * derinlik * uzunluk
        boru_hacmi = math.pi * ((cap_m / 2) ** 2) * uzunluk
        kum_dolgu_yuksekligi = 0.10 + cap_m + 0.30
        kum_dolgu_hacmi_brut = taban_genisligi * kum_dolgu_yuksekligi * uzunluk
        kum_dolgu_hacmi_net = kum_dolgu_hacmi_brut - boru_hacmi
        tuvenan_dolgu_hacmi = kazi_hacmi - kum_dolgu_hacmi_brut
        
        asfalt_kesme_metraj, asfalt_kirma_hacmi = 0, 0
        if "Sert Zemin" in zemin_tipi:
            asfalt_kesme_metraj = uzunluk * 2 
            asfalt_kirma_hacmi = ortalama_genislik * 0.20 * uzunluk 

        # 3. Tablo Hazırlığı
        hesap_kalemleri = [
            {"İşlem": "Kazı", "Poz": kazi_pozu, "Miktar": kazi_hacmi, "Birim": "m3"},
            {"İşlem": "Boru Döşeme", "Poz": boru_pozu, "Miktar": uzunluk, "Birim": "m"},
            {"İşlem": "Yataklama (Kum)", "Poz": kum_pozu, "Miktar": kum_dolgu_hacmi_net, "Birim": "m3"},
            {"İşlem": "Geri Dolgu", "Poz": dolgu_pozu, "Miktar": tuvenan_dolgu_hacmi, "Birim": "m3"}
        ]
        
        if "Sert Zemin" in zemin_tipi:
            if asfalt_kesme_pozu != "Seçilmedi":
                hesap_kalemleri.append({"İşlem": "Asfalt Kesme", "Poz": asfalt_kesme_pozu, "Miktar": asfalt_kesme_metraj, "Birim": "m"})
            if asfalt_kirma_pozu != "Seçilmedi":
                hesap_kalemleri.append({"İşlem": "Asfalt Kırma", "Poz": asfalt_kirma_pozu, "Miktar": asfalt_kirma_hacmi, "Birim": "m3"})
                
        if nakliye_pozu_1 != "Seçilmedi" and nakliye_metraj_1 > 0:
            hesap_kalemleri.append({"İşlem": "Nakliye", "Poz": nakliye_pozu_1, "Miktar": nakliye_metraj_1, "Birim": "m3/ton"})

        maliyet_tablosu = []
        genel_toplam = 0.0
        
        # 4. Fiyatları Excel'den Çekip Çarpma
        for kalem in hesap_kalemleri:
            if kalem["Miktar"] > 0:
                satir = df_fiyatlar[df_fiyatlar['POZ NO'].astype(str) == kalem["Poz"]].iloc[0]
                
                # Excel'deki ilgili ayın sütunundan fiyatı doğrudan al (Çarpan yok)
                birim_fiyati = satir[secilen_donem] 
                tanim = satir['İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI']
                
                tutar = kalem["Miktar"] * birim_fiyati
                genel_toplam += tutar
                
                maliyet_tablosu.append({
                    "İşlem Adı": kalem["İşlem"],
                    "Poz No": kalem["Poz"],
                    "Tanım": tanim[:70] + "..." if len(tanim) > 70 else tanim,
                    "Miktar": round(kalem["Miktar"], 2),
                    "Birim": kalem["Birim"],
                    f"Kârsız Birim Fiyat (₺)": round(birim_fiyati, 2),
                    "Toplam Tutar (₺)": round(tutar, 2)
                })
        
        # --- 5. SONUÇ EKRANI ---
        st.divider()
        donem_adi = str(secilen_donem).replace(" 00:00:00", "") # Varsa saat formatını temizle
        st.subheader(f"📊 {donem_adi} Dönemi Yaklaşık Maliyet Raporu")
        st.caption(f"**Uygulanan Parametreler:** {uzunluk} m Uzunluk | Ø{cap_mm} mm Boru | {derinlik} m Derinlik | Zemin: {zemin_tipi}")
        
        st.dataframe(pd.DataFrame(maliyet_tablosu), use_container_width=True)
        st.success(f"### 💰 KÂRSIZ GENEL TOPLAM: {genel_toplam:,.2f} ₺")

else:
    st.info("👈 Lütfen hesaplamaya başlamak için çoklu dönem fiyatlarını içeren Excel dosyanızı yükleyin.")