import streamlit as st
import pandas as pd
import io
import base64

from config import (
    FIYAT_DOSYASI,
    BORU_CAPLARI,
    VARSAYILAN_K_KATSAYISI,
    VARSAYILAN_A_KATSAYISI,
    VARSAYILAN_KIRMATAS_YOGUNLUK,
    VARSAYILAN_BETON_YOGUNLUK,
)
from data import fiyat_listesini_yukle, birim_fiyat_bul, donem_etiketlerini_olustur
from validation import girdileri_dogrula, gerekli_pozlari_kontrol_et
from calculations import (
    boru_pozlarini_belirle,
    metraj_hesapla,
    nakliye_fiyatlarini_hesapla,
    hesap_kalemlerini_olustur,
    nakliye_kalemlerini_olustur,
    maliyet_tablosunu_hesapla,
)
from drawing import cizim_olustur

# --- ARAYÜZ VE BAŞLIK ---
st.set_page_config(
    page_title="Kanal Kazısı Yaklaşık Maliyet",
    page_icon="🛠️",
    layout="wide",
)

# --- EK STİL İNCELİKLERİ ---
# Temel renk paleti .streamlit/config.toml [theme] üzerinden yönetiliyor.
# Burada sadece Streamlit'in native tema desteğinin karşılamadığı ince ayarlar var
# (buton hover rengi, alert kutusu şeffaflığı).
# Hover rengi #8A6B52, beyaz metinle WCAG AA kontrastını (>=4.5:1) sağlamak için
# orijinal #AB886D'den koyulaştırıldı.
st.markdown(
    """
    <style>
    div[data-testid="stButton"] > button:hover {
        background-color: #8A6B52 !important;
        color: #FFFFFF !important;
    }
    .stAlert {
        background-color: rgba(214, 192, 179, 0.4) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Kanal Kazısı Yaklaşık Maliyet Hesaplama")


EXCEL_IKON_SVG = (
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="2" y="2" width="20" height="20" rx="3" fill="#1B6E43"/>'
    '<path d="M6.5 6.5l4 5.5-4 5.5h2.4l2.8-3.9 2.8 3.9h2.4l-4-5.5 4-5.5h-2.4l-2.8 3.9-2.8-3.9z" fill="#FFFFFF"/>'
    "</svg>"
)


def format_currency(value):
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"₺{formatted}"


def format_quantity(value):
    formatted = f"{value:.2f}"
    return formatted.replace('.', ',')


try:
    df_fiyatlar, donem_sutunlari = fiyat_listesini_yukle(FIYAT_DOSYASI)
    donem_etiketleri = donem_etiketlerini_olustur(donem_sutunlari)
    poz_listesi = df_fiyatlar['POZ NO'].astype(str).tolist()

    st.sidebar.header("1. Metraj Parametreleri")

    secilen_etiket = st.sidebar.selectbox(
        "Birim Fiyat Dönemi",
        options=[etiket for etiket, _ in donem_etiketleri],
        index=len(donem_etiketleri) - 1,
        help="Hesaplamada kullanılacak aylık birim fiyat dönemi.",
    )
    secilen_donem = dict(donem_etiketleri)[secilen_etiket]

    uzunluk = st.sidebar.number_input("Hat Uzunluğu (m)", min_value=0.0, value=100.0, step=1.0)

    # max_value kaldırıldı (Önbellek çökmesini engellemek için)
    derinlik = st.sidebar.number_input("Ortalama Kazı Derinliği (m)", min_value=0.0, value=2.0, step=1.0)
    st.sidebar.caption("⚠️ *8m ve üzeri kazılar için bu modül üzerinden hesap yapılamaz; özel iksa/güvenlik projesi gerektirir.*")

    zemin_tipi = st.sidebar.selectbox("Zemin Tipi", ["Yeşil Alan", "Sert Zemin (Asfalt/Beton)"])
    ic_cap_mm = st.sidebar.selectbox("Boru İç Çapı (mm)", BORU_CAPLARI)

    st.sidebar.header("2. Nakliye Mesafeleri (km)")
    mesafe_kazi = st.sidebar.number_input("Kazı Döküm Mesafesi (km)", min_value=0.0, value=12.0, step=1.0)
    mesafe_boru = st.sidebar.number_input("Boru Nakliye Mesafesi (km)", min_value=0.0, value=12.0, step=1.0)
    mesafe_kirmatas = st.sidebar.number_input("Kırmataş/Kum Nakliye Mesafesi (km)", min_value=0.0, value=14.0, step=1.0)

    st.sidebar.header("3. Maliyet Ayarları")
    kar_orani = st.sidebar.number_input("Yüklenici Kârı (%)", min_value=0.0, value=15.0, step=1.0)
    k_carpan = 1 + (kar_orani / 100)

    uzman_modu = st.sidebar.checkbox(
        "Uzman Modu (nakliye katsayılarını düzenle)",
        value=False,
        help="Resmi birim fiyat analizi yönteminin taşıma formülü katsayılarıdır. "
             "Varsayılan değerler dışına çıkmak sonuçları etkiler; sadece bu formüllere "
             "hakim kullanıcılar tarafından değiştirilmelidir.",
    )
    with st.sidebar.expander("Gelişmiş Nakliye Katsayıları"):
        K_katsayisi = st.number_input(
            "Taşıt Katsayısı (K)", value=VARSAYILAN_K_KATSAYISI, disabled=not uzman_modu,
            help="Nakliye birim fiyat formülündeki resmi taşıt katsayısı.",
        )
        A_katsayisi = st.number_input(
            "Zorluk Katsayısı (A)", value=VARSAYILAN_A_KATSAYISI, disabled=not uzman_modu,
            help="Yol/arazi zorluğuna göre resmi nakliye zorluk katsayısı.",
        )
        kirmata_yogunluk = st.number_input(
            "Kırmataş Yoğunluğu (t/m³)", value=VARSAYILAN_KIRMATAS_YOGUNLUK, disabled=not uzman_modu,
            help="Kırmataş/kum nakliye tonajı hesabında kullanılan yoğunluk.",
        )
        beton_yogunluk = st.number_input(
            "Beton Boru Yoğunluğu (t/m³)", value=VARSAYILAN_BETON_YOGUNLUK, disabled=not uzman_modu,
            help="Boru nakliye tonajı hesabında kullanılan beton yoğunluğu.",
        )

    pozlar = boru_pozlarini_belirle(zemin_tipi, ic_cap_mm)

    if st.button("HESAPLA", type="primary"):
        dogrulama_hatalari = girdileri_dogrula(
            uzunluk, derinlik, mesafe_kazi, mesafe_boru, mesafe_kirmatas, kar_orani
        )
        if dogrulama_hatalari:
            st.session_state.pop("sonuc", None)
            for hata in dogrulama_hatalari:
                st.error(f"⚠️ {hata}")
        else:
            gerekli_pozlar = [pozlar["kazi_pozu"], pozlar["kum_pozu"], pozlar["dolgu_pozu"], pozlar["boru_pozu"]]
            if ic_cap_mm >= 800:
                gerekli_pozlar.append(pozlar["hasir_celik_pozu"])

            eksik_pozlar = gerekli_pozlari_kontrol_et(gerekli_pozlar, poz_listesi)

            if eksik_pozlar:
                st.session_state.pop("sonuc", None)
                st.error(f"⚠️ Hata: '{FIYAT_DOSYASI}' dosyasında şu otomatik pozlar bulunamadı: {', '.join(eksik_pozlar)}")
            else:
                with st.spinner("Hesaplanıyor..."):
                    metraj = metraj_hesapla(ic_cap_mm, derinlik, uzunluk, pozlar["dolgu_pozu"])
                    nakliye_fiyatlari = nakliye_fiyatlarini_hesapla(
                        mesafe_kazi, mesafe_boru, mesafe_kirmatas,
                        K_katsayisi, A_katsayisi, kirmata_yogunluk, beton_yogunluk,
                        metraj["boru_malzeme_hacmi"],
                    )
                    hesap_kalemleri = hesap_kalemlerini_olustur(pozlar, ic_cap_mm, uzunluk, metraj)
                    nakliye_kalemleri = nakliye_kalemlerini_olustur(nakliye_fiyatlari, metraj)

                    satirlar, genel_toplam_karsiz, genel_toplam_karli = maliyet_tablosunu_hesapla(
                        hesap_kalemleri,
                        lambda poz: birim_fiyat_bul(df_fiyatlar, poz, secilen_donem),
                        k_carpan,
                        nakliye_kalemleri,
                    )

                    st.session_state["sonuc"] = {
                        "satirlar": satirlar,
                        "genel_toplam_karsiz": genel_toplam_karsiz,
                        "genel_toplam_karli": genel_toplam_karli,
                        "metraj": metraj,
                        "nakliye_fiyatlari": nakliye_fiyatlari,
                        "ic_cap_mm": ic_cap_mm,
                        "derinlik": derinlik,
                        "uzunluk": uzunluk,
                        "zemin_tipi": zemin_tipi,
                        "kar_orani": kar_orani,
                        "secilen_etiket": secilen_etiket,
                    }

    if "sonuc" in st.session_state:
        s = st.session_state["sonuc"]
        satirlar = s["satirlar"]
        genel_toplam_karsiz = s["genel_toplam_karsiz"]
        genel_toplam_karli = s["genel_toplam_karli"]
        metraj = s["metraj"]
        nakliye_fiyatlari = s["nakliye_fiyatlari"]
        ic_cap_mm_sonuc = s["ic_cap_mm"]
        derinlik_sonuc = s["derinlik"]
        uzunluk_sonuc = s["uzunluk"]
        zemin_tipi_sonuc = s["zemin_tipi"]
        kar_orani_sonuc = s["kar_orani"]
        secilen_etiket_sonuc = s["secilen_etiket"]

        maliyet_tablosu_gorsel = [
            {
                "Poz No": r["Poz No"], "İşlem Adı": r["İşlem Adı"],
                "Miktar": format_quantity(r["Miktar"]), "Birim": r["Birim"],
                "Kârlı Birim Fiyat": format_currency(r["karli_fiyat"]),
                "Kârlı Tutar": format_currency(r["karli_tutar"]),
            }
            for r in satirlar
        ]
        maliyet_tablosu_excel = [
            {
                "Poz No": r["Poz No"], "İşlem Adı": r["İşlem Adı"],
                "Miktar": r["Miktar"], "Birim": r["Birim"],
                "Kârlı Birim Fiyat (TL)": r["karli_fiyat"],
                "Kârlı Tutar (TL)": r["karli_tutar"],
            }
            for r in satirlar
        ]

        maliyet_tablosu_gorsel.append({
            "Poz No": "", "İşlem Adı": "TOPLAM",
            "Miktar": "", "Birim": "",
            "Kârlı Birim Fiyat": "",
            "Kârlı Tutar": format_currency(genel_toplam_karli)
        })

        st.divider()
        donati_bilgisi = (
            f" | Hasır Çelik: {format_quantity(metraj['hasir_celik_miktari_ton'])} Ton"
            if metraj["hasir_celik_miktari_ton"] > 0 else " | Hasır Çelik: Yok"
        )
        st.info(
            f"📐 **Metraj Detayları:** İç Çap: Ø{ic_cap_mm_sonuc} mm | Dış Çap: Ø{metraj['dis_cap_mm']} mm | "
            f"Boru Ağırlığı: {format_quantity(nakliye_fiyatlari['nakliye_boru_ton'])} Ton{donati_bilgisi}"
        )
        st.caption(f"💲 Kullanılan birim fiyat dönemi: **{secilen_etiket_sonuc}** — kaynak: `{FIYAT_DOSYASI}`")

        col1, col2 = st.columns([7, 4])

        with col1:
            df_sonuc_gorsel = pd.DataFrame(maliyet_tablosu_gorsel)
            df_sonuc_gorsel.index = df_sonuc_gorsel.index + 1

            def style_last_row(row):
                if row.name == df_sonuc_gorsel.index[-1]:
                    return ['background-color: transparent; color: black; font-weight: bold; font-size: 1.15em;'] * len(row)
                return [''] * len(row)

            styled_df = df_sonuc_gorsel.style.set_properties(
                subset=['İşlem Adı'], **{'text-align': 'left'}
            ).set_properties(
                subset=['Poz No', 'Birim'], **{'text-align': 'center'}
            ).set_properties(
                subset=['Miktar', 'Kârlı Birim Fiyat', 'Kârlı Tutar'], **{'text-align': 'right'}
            ).apply(style_last_row, axis=1)

            styled_df = styled_df.set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#493628'), ('color', '#E4E0E1'), ('font-weight', 'bold'), ('text-align', 'center')]}
            ])

            st.dataframe(styled_df, use_container_width=True)

            df_sonuc_excel = pd.DataFrame(maliyet_tablosu_excel)
            df_sonuc_excel.index = df_sonuc_excel.index + 1

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_sonuc_excel.to_excel(writer, sheet_name='Yaklaşık Maliyet Raporu')
            b64 = base64.b64encode(buffer.getvalue()).decode()

            excel_href = (
                '<div style="margin-top: 5px;">'
                f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" '
                'download="Altyapi_Yaklasik_Maliyet_Raporu.xlsx" '
                'style="display: inline-flex; align-items: center; justify-content: center; '
                'background-color: #217346; padding: 10px; border-radius: 5px; width: 42px; height: 42px;">'
                f'{EXCEL_IKON_SVG}'
                '</a>'
                '</div>'
            )
            st.markdown(excel_href, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            kar_farki = genel_toplam_karli - genel_toplam_karsiz
            st.metric(
                f"📈 Genel Toplam (%{format_quantity(kar_orani_sonuc)} kârlı)",
                format_currency(genel_toplam_karli),
                delta=f"+{format_currency(kar_farki)} kâr",
            )
            if uzunluk_sonuc > 0:
                metretul_maliyeti = genel_toplam_karli / uzunluk_sonuc
                st.metric("📏 Metretül Maliyeti", f"{format_currency(metretul_maliyeti)}/m")

        with col2:
            fig = cizim_olustur(ic_cap_mm_sonuc, metraj["dis_cap_m"], derinlik_sonuc, metraj["taban_genisligi"], zemin_tipi_sonuc)
            st.pyplot(fig)

except FileNotFoundError:
    st.error(f"⚠️ HATA: '{FIYAT_DOSYASI}' dosyası bulunamadı. Lütfen Excel dosyasını GitHub deponuza yüklediğinizden emin olun.")
except KeyError as e:
    st.error(f"⚠️ Birim fiyat dosyasının yapısı beklenenden farklı: {e}")
except Exception as e:
    st.error(f"⚠️ Kritik bir hata oluştu: {e}")

st.divider()
st.caption(
    "🛠️ Bu araç, girilen parametrelere göre yaklaşık bir maliyet tahmini üretir; "
    "resmi bir keşif/metraj raporu yerine geçmez. Açık kaynak — "
    "[GitHub üzerinde inceleyin](https://github.com/enesyikilmaz/altyapi-maliyet)."
)
