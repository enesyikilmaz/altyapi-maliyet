import streamlit as st
import pandas as pd
import math

# --- ÖZEL FORMATLAMA FONKSİYONLARI ---
def format_currency(value):
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"₺{formatted}"

def format_quantity(value):
    formatted = f"{value:.2f}"
    return formatted.replace('.', ',')

st.set_page_config(page_title="Altyapı Yaklaşık Maliyet Motoru", layout="wide", page_icon="🏗️")
st.title("🚧 Altyapı Metraj ve Kârsız Yaklaşık Maliyet Motoru")
st.markdown("Otomatik Poz Seçimi, Geometrik Şev Kontrolü, Dinamik Nakliye ve Q188/188 Donatı Analizleri (Eylül 2025)")

# --- 1. VERİ YÜKLEME (OTOMATİK DOSYADAN) ---
file_path = "Altyapı Birim Fiyatlar_2.xlsx"

try:
    df_fiyatlar = pd.read_excel(file_path)
    sabit_sutunlar = ['SIRA NO', 'POZ NO', 'İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI', 'BİRİMİ']
    donem_sutunlari = [col for col in df_fiyatlar.columns if col not in sabit_sutunlar]
    secilen_donem = donem_sutunlari[0]
    poz_listesi = df_fiyatlar['POZ NO'].astype(str).tolist()
    
    # --- 2. KULLANICI GİRİŞ PARAMETRELERİ ---
    st.sidebar.header("1. Metraj Parametreleri")
    st.sidebar.info("Dönem: **Eylül 2025**")
    
    uzunluk = st.sidebar.number_input("Hat Uzunluğu (m)", min_value=0.0, value=100.0)
    derinlik = st.sidebar.number_input("Ortalama Kazı Derinliği (m)", min_value=0.0, value=2.0)
    zemin_tipi = st.sidebar.selectbox("Zemin Tipi", ["Yeşil Alan", "Sert Zemin (Asfalt/Beton)"])
    
    boru_caplari = [300, 400, 500, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400]
    ic_cap_mm = st.sidebar.selectbox("Boru İç Çapı (mm)", boru_caplari)

    # --- 3. NAKLİYE PARAMETRELERİ ---
    st.sidebar.header("2. Nakliye Mesafeleri (km)")
    mesafe_kazi = st.sidebar.number_input("Kazı Döküm Mesafesi (km)", min_value=0.0, value=12.0, step=1.0)
    mesafe_boru = st.sidebar.number_input("Boru Nakliye Mesafesi (km)", min_value=0.0, value=12.0, step=1.0)
    mesafe_kirmatas = st.sidebar.number_input("Kırmataş/Kum Nakliye Mesafesi (km)", min_value=0.0, value=14.0, step=1.0)
    
    with st.sidebar.expander("Gelişmiş Nakliye Katsayıları (Eylül 2025)"):
        K_katsayisi = st.number_input("Taşıt Katsayısı (K)", value=2048.01)
        A_katsayisi = st.number_input("Zorluk Katsayısı (A)", value=1.75)
        kirmata_yogunluk = st.number_input("Kırmataş Yoğunluğu (t/m³)", value=1.60)
        beton_yogunluk = st.number_input("Beton Boru Yoğunluğu (t/m³)", value=2.40)

    # --- OTOMATİK POZ ATAMALARI ---
    kazi_pozu = "KGM 14.210"
    kum_pozu = "43.610.1053"
    dolgu_pozu = "43.610.1064" if "Sert Zemin" in zemin_tipi else "43.610.1004"
    hasir_celik_pozu = "43.665.1011"
    
    boru_poz_sozlugu = {
        300: "43.526.1123", 400: "43.526.1124", 500: "43.526.1125", 600: "43.526.1126",
        800: "43.526.1162", 1000: "43.526.1163", 1200: "43.526.1164", 1400: "43.526.1165",
        1600: "43.526.1201", 1800: "43.526.1202", 2000: "43.526.1203", 2200: "43.526.1204", 
        2400: "43.526.1205"
    }
    boru_pozu = boru_poz_sozlugu.get(ic_cap_mm)

    # --- 4. HESAPLAMA MOTORU ---
    if st.button("Yaklaşık Maliyeti Çıkar", type="primary", use_container_width=True):
        gerekli_pozlar = [kazi_pozu, kum_pozu, dolgu_pozu, boru_pozu]
        if ic_cap_mm >= 800:
            gerekli_pozlar.append(hasir_celik_pozu)
            
        eksik_pozlar = [poz for poz in gerekli_pozlar if poz not in poz_listesi]
        
        if eksik_pozlar:
            st.error(f"⚠️ Hata: 'Altyapı Birim Fiyatlar_2.xlsx' dosyasında şu otomatik pozlar bulunamadı: {', '.join(eksik_pozlar)}")
        else:
            # 1. Boru Dış Çapı Hesabı
            et_kalinlikleri_mm = {300: 50, 400: 50, 500: 60, 600: 70, 800: 90, 1000: 110, 1200: 130, 1400: 150, 1600: 170, 1800: 180, 2000: 200, 2200: 220, 2400: 240}
            et_kalinligi = et_kalinlikleri_mm.get(ic_cap_mm, ic_cap_mm * 0.1)
            dis_cap_mm = ic_cap_mm + (2 * et_kalinligi)
            dis_cap_m = dis_cap_mm / 1000.0

            # 2. Geometrik Kesit ve Şev Hesabı
            taban_genisligi = dis_cap_m + 0.40
            ortalama_genislik = taban_genisligi + (derinlik / 3) if derinlik > 1.50 else taban_genisligi

            # 3. İmalat Metrajları
            kazi_hacmi = ortalama_genislik * derinlik * uzunluk
            boru_hacmi_dis = math.pi * ((dis_cap_m / 2) ** 2) * uzunluk
            kum_dolgu_yuksekligi = 0.10 + dis_cap_m + 0.30
            kum_ortalama_genislik = taban_genisligi + (kum_dolgu_yuksekligi / 3) if derinlik > 1.50 else taban_genisligi
            kum_dolgu_hacmi_brut = kum_ortalama_genislik * kum_dolgu_yuksekligi * uzunluk
            kum_dolgu_hacmi_net = kum_dolgu_hacmi_brut - boru_hacmi_dis
            tuvenan_dolgu_hacmi = kazi_hacmi - kum_dolgu_hacmi_brut

            # 4. Hasır Çelik (Donatı) Metrajı (Q188/188 Tek Kat)
            hasir_celik_miktari_ton = 0
            hasir_celik_alani_m2 = 0
            if ic_cap_mm >= 800:
                hasir_celik_kg_m2 = 2.95 # Q188/188 tipi hasır çelik standart ağırlığı
                donati_capi_m = (ic_cap_mm + et_kalinligi) / 1000.0 # Et kalınlığının ortasından geçen büküm çapı
                bir_metre_cevre = math.pi * donati_capi_m
                hasir_celik_alani_m2 = bir_metre_cevre * uzunluk
                hasir_celik_miktari_ton = (hasir_celik_alani_m2 * hasir_celik_kg_m2) / 1000.0 # Tona çevirilir

            # 5. Nakliye Metrajları ve Analizleri
            nakliye_kazi_miktari = kazi_hacmi - (tuvenan_dolgu_hacmi if dolgu_pozu == "43.610.1004" else 0)
            fiyat_SNBF_27A = 0
            if mesafe_kazi > 0:
                mesafe_metre = mesafe_kazi * 1000
                fiyat_SNBF_27A = 1.25 * K_katsayisi * ((0.00046 * math.sqrt(mesafe_metre)) - 0.0046) + 29.28 + 80.00

            boru_malzeme_hacmi = math.pi * (((dis_cap_m/2)**2) - ((ic_cap_mm/2000)**2)) * uzunluk
            nakliye_boru_ton = boru_malzeme_hacmi * beton_yogunluk
            fiyat_SNBF_BF = 0
            if mesafe_boru > 0:
                fiyat_SNBF_BF = A_katsayisi * K_katsayisi * ((0.0007 * mesafe_boru) + 0.01) * 1.0

            nakliye_kirmatas_miktari = kum_dolgu_hacmi_net + (tuvenan_dolgu_hacmi if dolgu_pozu == "43.610.1064" else 0)
            fiyat_SNBF_14 = 0
            if mesafe_kirmatas > 0:
                fiyat_SNBF_14 = A_katsayisi * K_katsayisi * ((0.0007 * mesafe_kirmatas) + 0.01) * kirmata_yogunluk + 29.28

            # 6. Tablo Hazırlığı
            hesap_kalemleri = [
                {"İşlem": "Kazı", "Poz": kazi_pozu, "Miktar": kazi_hacmi, "Birim": "m³"},
                {"İşlem": f"Boru Döşeme (Ø{ic_cap_mm} mm)", "Poz": boru_pozu, "Miktar": uzunluk, "Birim": "m"},
                {"İşlem": "Yataklama (Kırmataş/Kum)", "Poz": kum_pozu, "Miktar": kum_dolgu_hacmi_net, "Birim": "m³"},
                {"İşlem": "Geri Dolgu", "Poz": dolgu_pozu, "Miktar": tuvenan_dolgu_hacmi, "Birim": "m³"}
            ]
            
            if hasir_celik_miktari_ton > 0:
                hesap_kalemleri.append({"İşlem": "Boru İçi Hasır Çelik Donatı", "Poz": hasir_celik_pozu, "Miktar": hasir_celik_miktari_ton, "Birim": "ton"})

            maliyet_tablosu = []
            genel_toplam = 0.0
            
            # İmalatlar
            for kalem in hesap_kalemleri:
                if kalem["Miktar"] > 0:
                    satir = df_fiyatlar[df_fiyatlar['POZ NO'].astype(str) == kalem["Poz"]].iloc[0]
                    birim_fiyati = satir[secilen_donem] 
                    tutar = kalem["Miktar"] * birim_fiyati
                    genel_toplam += tutar
                    maliyet_tablosu.append({
                        "İşlem Adı": kalem["İşlem"], 
                        "Poz No": kalem["Poz"], 
                        "Miktar": format_quantity(kalem["Miktar"]), 
                        "Birim": kalem["Birim"],
                        "Birim Fiyat": format_currency(birim_fiyati), 
                        "Toplam Tutar": format_currency(tutar)
                    })
            
            # Nakliyeler
            nakliyeler = [
                {"İşlem": "Kazı Hafriyat Nakliyesi", "Poz": "SNBF.27-A", "Miktar": nakliye_kazi_miktari, "Birim": "m³", "Fiyat": fiyat_SNBF_27A},
                {"İşlem": "Boru Nakliyesi", "Poz": "SNBF.BF", "Miktar": nakliye_boru_ton, "Birim": "ton", "Fiyat": fiyat_SNBF_BF},
                {"İşlem": "Kırmataş/Kum Nakliyesi", "Poz": "SNBF.14", "Miktar": nakliye_kirmatas_miktari, "Birim": "m³", "Fiyat": fiyat_SNBF_14}
            ]
            
            for nak in nakliyeler:
                if nak["Miktar"] > 0 and nak["Fiyat"] > 0:
                    tutar = nak["Miktar"] * nak["Fiyat"]
                    genel_toplam += tutar
                    maliyet_tablosu.append({
                        "İşlem Adı": nak["İşlem"], 
                        "Poz No": nak["Poz"], 
                        "Miktar": format_quantity(nak["Miktar"]), 
                        "Birim": nak["Birim"],
                        "Birim Fiyat": format_currency(nak["Fiyat"]), 
                        "Toplam Tutar": format_currency(tutar)
                    })

            # --- 7. SONUÇ EKRANI ---
            st.divider()
            st.subheader(f"📊 Eylül 2025 Dönemi Yaklaşık Maliyet Raporu")
            
            donati_bilgisi = f" | Hasır Çelik: {format_quantity(hasir_celik_miktari_ton)} Ton ({format_quantity(hasir_celik_alani_m2)} m²)" if hasir_celik_miktari_ton > 0 else " | Hasır Çelik: Yok (Boru Çapı < 800mm)"
            
            st.info(f"📐 **Metraj Detayları:** İç Çap: Ø{ic_cap_mm} mm | Dış Çap: Ø{dis_cap_mm} mm | Boru Ağırlığı: {format_quantity(nakliye_boru_ton)} Ton{donati_bilgisi}\n\n" 
                    f"🚚 **Nakliye Fiyat Testi:** Kazı ({format_quantity(mesafe_kazi)} km) = {format_currency(fiyat_SNBF_27A)} / m³ | Kırmataş ({format_quantity(mesafe_kirmatas)} km) = {format_currency(fiyat_SNBF_14)} / m³ | Boru ({format_quantity(mesafe_boru)} km) = {format_currency(fiyat_SNBF_BF)} / ton")
            
            df_sonuc = pd.DataFrame(maliyet_tablosu)
            st.dataframe(df_sonuc, use_container_width=True)
            st.success(f"### 💰 KÂRSIZ GENEL TOPLAM: {format_currency(genel_toplam)}")

except FileNotFoundError:
    st.error(f"⚠️ HATA: '{file_path}' dosyası bulunamadı. Lütfen Excel dosyasını GitHub deponuza yüklediğinizden emin olun.")
except Exception as e:
    st.error(f"⚠️ Kritik bir hata oluştu: {e}")