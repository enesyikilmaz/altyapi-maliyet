import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- ÖZEL FORMATLAMA FONKSİYONLARI ---
def format_currency(value):
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"₺{formatted}"

def format_quantity(value):
    formatted = f"{value:.2f}"
    return formatted.replace('.', ',')

# --- DİNAMİK KESİT ÇİZİM FONKSİYONU ---
def cizim_olustur(ic_cap_mm, dis_cap_m, derinlik, taban_genisligi, zemin_tipi):
    fig, ax = plt.subplots(figsize=(6, 8), facecolor='white')
    
    kum_h = 0.10 + dis_cap_m + 0.30  # Yataklama ve gömlekleme toplam yüksekliği
    
    # 1.50m kontrolüne göre üst genişlik
    if derinlik > 1.50:
        ust_genislik = taban_genisligi + 2 * (derinlik / 3)
        kum_ust_genislik = taban_genisligi + 2 * (kum_h / 3)
    else:
        ust_genislik = taban_genisligi
        kum_ust_genislik = taban_genisligi
        
    # Renk ve Tarama (Hatch) Ayarları
    if "Sert Zemin" in zemin_tipi:
        dolgu_color = '#d3d3d3' # Kırmataş için gri
        dolgu_hatch = 'O'       # Taşları temsil eden yuvarlaklar
        dolgu_label = "Kırmataş Geri Dolgu"
        zemin_cizgi = 'black'
    else:
        dolgu_color = '#deb887' # Toprak için kahvemsi
        dolgu_hatch = '+'       # Toprağı temsil eden artılar
        dolgu_label = "Kazıdan Çıkan Toprak\n(Geri Dolgu)"
        zemin_cizgi = 'green'

    # Geri Dolgu Poligonu
    dolgu_poly = patches.Polygon([
        (-kum_ust_genislik/2, kum_h), (kum_ust_genislik/2, kum_h),
        (ust_genislik/2, derinlik), (-ust_genislik/2, derinlik)
    ], closed=True, facecolor=dolgu_color, edgecolor='black', hatch=dolgu_hatch, linewidth=1.5)
    ax.add_patch(dolgu_poly)
    
    # Yataklama ve Gömlekleme Poligonu (Kum/Kırmataş)
    yatak_poly = patches.Polygon([
        (-taban_genisligi/2, 0), (taban_genisligi/2, 0),
        (kum_ust_genislik/2, kum_h), (-kum_ust_genislik/2, kum_h)
    ], closed=True, facecolor='#f4a460', edgecolor='black', hatch='.', linewidth=1.5)
    ax.add_patch(yatak_poly)
    
    # Boru Çizimi (İç ve Dış Çap)
    pipe_center_y = 0.10 + (dis_cap_m / 2)
    pipe_outer = patches.Circle((0, pipe_center_y), dis_cap_m/2, facecolor='#f0f0f0', edgecolor='black', linewidth=2)
    pipe_inner = patches.Circle((0, pipe_center_y), (ic_cap_mm/2000), facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(pipe_outer)
    ax.add_patch(pipe_inner)
    
    # Terasman / Tabii Zemin Çizgisi
    ax.plot([-ust_genislik/2 - 0.5, ust_genislik/2 + 0.5], [derinlik, derinlik], color=zemin_cizgi, linewidth=3)
    
    # Metinler ve Etiketler
    ax.text(0, derinlik + 0.15, zemin_tipi.upper(), ha='center', fontweight='bold', fontsize=12, color=zemin_cizgi)
    ax.text(0, pipe_center_y, f"Ø{ic_cap_mm}", ha='center', va='center', fontweight='bold', fontsize=10)
    ax.text(0, kum_h/2, "Yataklama\n& Gömlekleme", ha='center', va='center', fontsize=9, backgroundcolor='white')
    ax.text(0, kum_h + (derinlik - kum_h)/2, dolgu_label, ha='center', va='center', fontsize=10, backgroundcolor='white')
    
    # Ölçü Okları
    # Derinlik (HT)
    ax.annotate('', xy=(-ust_genislik/2 - 0.2, 0), xytext=(-ust_genislik/2 - 0.2, derinlik), arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
    ax.text(-ust_genislik/2 - 0.3, derinlik/2, f"HT = {derinlik:.2f} m", va='center', ha='right', color='red', rotation=90, fontweight='bold')
    
    # Taban Genişliği
    ax.annotate('', xy=(-taban_genisligi/2, -0.15), xytext=(taban_genisligi/2, -0.15), arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
    ax.text(0, -0.25, f"Taban = {taban_genisligi:.2f} m", ha='center', va='top', color='blue', fontweight='bold')
    
    # Şev Oranı (Sadece Derinlik > 1.50 ise)
    if derinlik > 1.50:
        ax.text(ust_genislik/2 + 0.1, derinlik/2, "1/3\nŞev", ha='left', va='center', color='black', fontweight='bold')
    
    ax.set_aspect('equal')
    ax.axis('off')
    ax.autoscale_view()
    
    return fig

# --- 1. ARAYÜZ VE BAŞLIK ---
st.set_page_config(page_title="Altyapı Yaklaşık Maliyet Motoru", layout="wide", page_icon="🚜")
st.title("🚧Kanal Kazısı Yaklaşık Maliyet Hesaplama 🚜")

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

    # --- 3. NAKLİYE VE KÂR PARAMETRELERİ ---
    st.sidebar.header("2. Nakliye Mesafeleri (km)")
    mesafe_kazi = st.sidebar.number_input("Kazı Döküm Mesafesi (km)", min_value=0.0, value=12.0, step=1.0)
    mesafe_boru = st.sidebar.number_input("Boru Nakliye Mesafesi (km)", min_value=0.0, value=12.0, step=1.0)
    mesafe_kirmatas = st.sidebar.number_input("Kırmataş/Kum Nakliye Mesafesi (km)", min_value=0.0, value=14.0, step=1.0)
    
    st.sidebar.header("3. Maliyet Ayarları")
    kar_orani = st.sidebar.number_input("Yüklenici Kârı (%)", min_value=0.0, value=15.0, step=1.0)
    k_carpan = 1 + (kar_orani / 100)
    
    with st.sidebar.expander("Gelişmiş Nakliye Katsayıları"):
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
            # Geometrik Kesit Hesapları
            et_kalinlikleri_mm = {300: 50, 400: 50, 500: 60, 600: 70, 800: 90, 1000: 110, 1200: 130, 1400: 150, 1600: 170, 1800: 180, 2000: 200, 2200: 220, 2400: 240}
            et_kalinligi = et_kalinlikleri_mm.get(ic_cap_mm, ic_cap_mm * 0.1)
            dis_cap_mm = ic_cap_mm + (2 * et_kalinligi)
            dis_cap_m = dis_cap_mm / 1000.0

            taban_genisligi = dis_cap_m + 0.40
            ortalama_genislik = taban_genisligi + (derinlik / 3) if derinlik > 1.50 else taban_genisligi

            # İmalat Metrajları
            kazi_hacmi = ortalama_genislik * derinlik * uzunluk
            boru_hacmi_dis = math.pi * ((dis_cap_m / 2) ** 2) * uzunluk
            kum_dolgu_yuksekligi = 0.10 + dis_cap_m + 0.30
            kum_ortalama_genislik = taban_genisligi + (kum_dolgu_yuksekligi / 3) if derinlik > 1.50 else taban_genisligi
            kum_dolgu_hacmi_brut = kum_ortalama_genislik * kum_dolgu_yuksekligi * uzunluk
            kum_dolgu_hacmi_net = kum_dolgu_hacmi_brut - boru_hacmi_dis
            tuvenan_dolgu_hacmi = kazi_hacmi - kum_dolgu_hacmi_brut

            # Donatı Metrajı
            hasir_celik_miktari_ton = 0
            if ic_cap_mm >= 800:
                donati_capi_m = (ic_cap_mm + et_kalinligi) / 1000.0
                hasir_celik_alani_m2 = (math.pi * donati_capi_m) * uzunluk
                hasir_celik_miktari_ton = (hasir_celik_alani_m2 * 2.95) / 1000.0 

            # Nakliye Metrajları
            nakliye_kazi_miktari = kazi_hacmi - (tuvenan_dolgu_hacmi if dolgu_pozu == "43.610.1004" else 0)
            fiyat_SNBF_27A = 1.25 * K_katsayisi * ((0.00046 * math.sqrt(mesafe_kazi * 1000)) - 0.0046) + 29.28 + 80.00 if mesafe_kazi > 0 else 0
            boru_malzeme_hacmi = math.pi * (((dis_cap_m/2)**2) - ((ic_cap_mm/2000)**2)) * uzunluk
            nakliye_boru_ton = boru_malzeme_hacmi * beton_yogunluk
            fiyat_SNBF_BF = A_katsayisi * K_katsayisi * ((0.0007 * mesafe_boru) + 0.01) * 1.0 if mesafe_boru > 0 else 0
            nakliye_kirmatas_miktari = kum_dolgu_hacmi_net + (tuvenan_dolgu_hacmi if dolgu_pozu == "43.610.1064" else 0)
            fiyat_SNBF_14 = A_katsayisi * K_katsayisi * ((0.0007 * mesafe_kirmatas) + 0.01) * kirmata_yogunluk + 29.28 if mesafe_kirmatas > 0 else 0

            # Tablo Hazırlığı
            hesap_kalemleri = [
                {"İşlem": "Kazı", "Poz": kazi_pozu, "Miktar": kazi_hacmi, "Birim": "m³"},
                {"İşlem": f"Boru Döşeme (Ø{ic_cap_mm} mm)", "Poz": boru_pozu, "Miktar": uzunluk, "Birim": "m"},
                {"İşlem": "Yataklama (Kırmataş/Kum)", "Poz": kum_pozu, "Miktar": kum_dolgu_hacmi_net, "Birim": "m³"},
                {"İşlem": "Geri Dolgu", "Poz": dolgu_pozu, "Miktar": tuvenan_dolgu_hacmi, "Birim": "m³"}
            ]
            if hasir_celik_miktari_ton > 0:
                hesap_kalemleri.append({"İşlem": "Boru İçi Hasır Çelik Donatı", "Poz": hasir_celik_pozu, "Miktar": hasir_celik_miktari_ton, "Birim": "ton"})

            maliyet_tablosu = []
            genel_toplam_karsiz = 0.0
            genel_toplam_karli = 0.0
            
            def satir_ekle(islem, poz, miktar, birim, karsiz_fiyat):
                nonlocal genel_toplam_karsiz, genel_toplam_karli
                if miktar > 0 and karsiz_fiyat > 0:
                    karli_fiyat = karsiz_fiyat * k_carpan
                    karsiz_tutar = miktar * karsiz_fiyat
                    karli_tutar = miktar * karli_fiyat
                    
                    genel_toplam_karsiz += karsiz_tutar
                    genel_toplam_karli += karli_tutar
                    
                    maliyet_tablosu.append({
                        "İşlem Adı": islem, "Poz No": poz, 
                        "Miktar": format_quantity(miktar), "Birim": birim,
                        "Kârsız Birim Fiyat": format_currency(karsiz_fiyat), 
                        "Kârlı Birim Fiyat": format_currency(karli_fiyat), 
                        "Kârsız Tutar": format_currency(karsiz_tutar),
                        "Kârlı Tutar": format_currency(karli_tutar)
                    })

            # İmalatlar ve Nakliyeler
            for kalem in hesap_kalemleri:
                karsiz_bf = df_fiyatlar[df_fiyatlar['POZ NO'].astype(str) == kalem["Poz"]].iloc[0][secilen_donem]
                satir_ekle(kalem["İşlem"], kalem["Poz"], kalem["Miktar"], kalem["Birim"], karsiz_bf)
                
            satir_ekle("Kazı Hafriyat Nakliyesi", "SNBF.27-A", nakliye_kazi_miktari, "m³", fiyat_SNBF_27A)
            satir_ekle("Boru Nakliyesi", "SNBF.BF", nakliye_boru_ton, "ton", fiyat_SNBF_BF)
            satir_ekle("Kırmataş/Kum Nakliyesi", "SNBF.14", nakliye_kirmatas_miktari, "m³", fiyat_SNBF_14)

            # --- 5. SONUÇ EKRANI VE ÇİZİM ---
            st.divider()
            st.subheader(f"📊 Eylül 2025 Dönemi Yaklaşık Maliyet Raporu")
            
            donati_bilgisi = f" | Hasır Çelik: {format_quantity(hasir_celik_miktari_ton)} Ton" if hasir_celik_miktari_ton > 0 else " | Hasır Çelik: Yok"
            st.info(f"📐 **Metraj Detayları:** İç Çap: Ø{ic_cap_mm} mm | Dış Çap: Ø{dis_cap_mm} mm | Boru Ağırlığı: {format_quantity(nakliye_boru_ton)} Ton{donati_bilgisi}")
            
            # Ekranı İkiye Böl: Sol Tarafta Tablo, Sağ Tarafta Çizim
            col1, col2 = st.columns([7, 4])
            
            with col1:
                df_sonuc = pd.DataFrame(maliyet_tablosu)
                df_sonuc.index = df_sonuc.index + 1 # Sıra numarasını 1'den başlatır
                st.dataframe(df_sonuc, use_container_width=True)
                
                st.warning(f"### 💰 KÂRSIZ GENEL TOPLAM: {format_currency(genel_toplam_karsiz)}")
                st.success(f"### 📈 KÂRLI GENEL TOPLAM (%{kar_orani} Kâr): {format_currency(genel_toplam_karli)}")
                
            with col2:
                # Dinamik Çizimi Oluştur ve Göster
                fig = cizim_olustur(ic_cap_mm, dis_cap_m, derinlik, taban_genisligi, zemin_tipi)
                st.pyplot(fig)

except FileNotFoundError:
    st.error(f"⚠️ HATA: '{file_path}' dosyası bulunamadı. Lütfen Excel dosyasını GitHub deponuza yüklediğinizden emin olun.")
except Exception as e:
    st.error(f"⚠️ Kritik bir hata oluştu: {e}")