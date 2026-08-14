import streamlit as st
import pandas as pd
import math

# --- 1. ARAYÜZ VE BAŞLIK ---
st.set_page_config(page_title="Altyapı Yaklaşık Maliyet Motoru", layout="wide", page_icon="🏗️")
st.title("🚧 Altyapı Metraj ve Kârsız Yaklaşık Maliyet Motoru")
st.markdown("İdarelerin (İLBANK/KGM) yayınladığı resmi kârsız birim fiyatları baz alarak metraj ve maliyet hesaplar. Ana iş kalemlerine ait pozlar tam otomatiktir.")

# --- 2. VERİ YÜKLEME ---
st.sidebar.header("1. Fiyat Veritabanı (Excel)")
uploaded_file = st.sidebar.file_uploader("Birim Fiyat Excel Dosyasını Yükleyin", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Excel'i oku
    df_fiyatlar = pd.read_excel(uploaded_file)
    
    # Sabit sütunları ayırarak sadece fiyat içeren dönem sütunlarını bul
    sabit_sutunlar = ['SIRA NO', 'POZ NO', 'İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI', 'BİRİMİ']
    donem_sutunlari = [col for col in df_fiyatlar.columns if col not in sabit_sutunlar]
    
    # Poz Listesini Sözlüğe Çevir
    poz_listesi = df_fiyatlar['POZ NO'].astype(str).tolist()
    
    # --- 3. KULLANICI GİRİŞ PARAMETRELERİ ---
    st.sidebar.header("2. Metraj Parametreleri")
    
    secilen_donem = st.sidebar.selectbox("Fiyat Dönemini Seçin", donem_sutunlari)
    
    uzunluk = st.sidebar.number_input("Hat Uzunluğu (m)", min_value=0.0, value=100.0)
    derinlik = st.sidebar.number_input("Ortalama Kazı Derinliği (m)", min_value=0.0, value=2.0)
    zemin_tipi = st.sidebar.selectbox("Zemin Tipi", ["Yeşil Alan", "Sert Zemin (Asfalt/Beton)"])
    
    # Boru çapları liste olarak sunulur (Kullanıcının yanlış çap girmesi engellenir)
    boru_caplari = [300, 400, 500, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400]
    cap_mm = st.sidebar.selectbox("Boru Çapı (mm)", boru_caplari)

    # --- OTOMATİK POZ ATAMALARI ---
    # 1. Sabit Pozlar
    kazi_pozu = "KGM 14.210"
    kum_pozu = "43.610.1053"
    dolgu_pozu = "43.610.1064" if "Sert Zemin" in zemin_tipi else "43.610.1004"
    
    # 2. Çapa Göre Otomatik Boru Pozu Ataması
    boru_poz_sozlugu = {
        300: "43.526.1123", 400: "43.526.1124", 500: "43.526.1125", 600: "43.526.1126",
        800: "43.526.1162", 1000: "43.526.1163", 1200: "43.526.1164", 1400: "43.526.1165",
        1600: "43.526.1201", 1800: "43.526.1202", 2000: "43.526.1203", 2200: "43.526.1204", 
        2400: "43.526.1205"
    }
    boru_pozu = boru_poz_sozlugu.get(cap_mm)

    st.sidebar.markdown("---")
    st.sidebar.header("3. Otomatik Atanan Pozlar")
    st.sidebar.success(f"**Kazı:** {kazi_pozu}\n\n**Yataklama:** {kum_pozu}\n\n**Geri Dolgu:** {dolgu_pozu}\n\n**Boru (Ø{cap_mm}):** {boru_pozu}")

    st.sidebar.header("4. İlave İş Kalemleri (Opsiyonel)")
    nakliye_pozu_1 = st.sidebar.selectbox("Nakliye Pozu", ["Seçilmedi"] + poz_listesi)
    nakliye_metraj_1 = st.sidebar.number_input("Nakliye Miktarı (m3/ton)", min_value=0.0, value=0.0)
    
    asfalt_kesme_pozu, asfalt_kirma_pozu = None, None
    if "Sert Zemin" in zemin_tipi:
        asfalt_kesme_pozu = st.sidebar.selectbox("Asfalt Kesme Pozu", ["Seçilmedi"] + poz_listesi)
        asfalt_kirma_pozu = st.sidebar.selectbox("Asfalt Kırma Pozu", ["Seçilmedi"] + poz_listesi)

    # --- 4. HESAPLAMA MOTORU ---
    if st.button("Yaklaşık Maliyeti Çıkar", type="primary", use_container_width=True):
        # Seçilen pozların Excel'de olup olmadığını güvenlik amacıyla kontrol et
        eksik_pozlar = [poz for poz in [kazi_pozu, kum_pozu, dolgu_pozu, boru_pozu] if poz not in poz_listesi]
        
        if eksik_pozlar:
            st.error(f"⚠️ Hata: Yüklediğiniz Excel dosyasında şu otomatik pozlar bulunamadı: {', '.join(eksik_pozlar)}")
        else:
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
                {"İşlem": f"Boru Döşeme (Ø{cap_mm} mm)", "Poz": boru_pozu, "Miktar": uzunluk, "Birim": "m"},
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
            donem_adi = str(secilen_donem).replace(" 00:00:00", "")
            st.subheader(f"📊 {donem_adi} Dönemi Yaklaşık Maliyet Raporu")
            st.caption(f"**Uygulanan Parametreler:** {uzunluk} m Uzunluk | Ø{cap_mm} mm Boru | {derinlik} m Derinlik | Zemin: {zemin_tipi}")
            
            st.dataframe(pd.DataFrame(maliyet_tablosu), use_container_width=True)
            st.success(f"### 💰 KÂRSIZ GENEL TOPLAM: {genel_toplam:,.2f} ₺")

else:
    st.info("👈 Lütfen hesaplamaya başlamak için çoklu dönem fiyatlarını içeren Excel dosyanızı yükleyin.")