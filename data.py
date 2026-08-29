"""Birim fiyat Excel dosyasının okunması, önbelleğe alınması ve şema doğrulaması."""

import pandas as pd
import streamlit as st

from config import SABIT_SUTUNLAR, AY_ADLARI_TR, FIYAT_SAYFASI, NAKLIYE_KATSAYI_ANAHTARLARI

ACIKLAMA_SUTUNU = 'İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI'


@st.cache_data
def fiyat_listesini_yukle(dosya_yolu):
    """Birim fiyat Excel'ini okur, şemayı doğrular ve önbelleğe alır."""
    df = pd.read_excel(dosya_yolu, sheet_name=FIYAT_SAYFASI)

    eksik_sutunlar = [s for s in SABIT_SUTUNLAR if s not in df.columns]
    if eksik_sutunlar:
        raise KeyError(
            f"Excel dosyasında beklenen sütun(lar) bulunamadı: {', '.join(eksik_sutunlar)}"
        )

    donem_sutunlari = [col for col in df.columns if col not in SABIT_SUTUNLAR]
    if not donem_sutunlari:
        raise KeyError("Excel dosyasında en az bir dönemsel birim fiyat sütunu bulunmalı.")

    return df, donem_sutunlari


def _anahtar_satiri_bul(df_fiyatlar, anahtar_metin):
    """Açıklama sütununda anahtar metni (büyük/küçük harf duyarsız) içeren ilk satırı bulur."""
    eslesen = df_fiyatlar[
        df_fiyatlar[ACIKLAMA_SUTUNU].astype(str).str.contains(anahtar_metin, case=False, na=False)
    ]
    if eslesen.empty:
        raise KeyError(
            f"Excel dosyasında '{anahtar_metin}' ifadesini içeren bir satır bulunamadı. "
            f"Nakliye katsayı satırlarının '{ACIKLAMA_SUTUNU}' sütunundaki metni kontrol edin."
        )
    return eslesen.iloc[0]


def nakliye_katsayilarini_bul(df_fiyatlar, donem):
    """
    Sayfa1'in alt kısmındaki nakliye formülü katsayılarını (A, K, G-beton, G-kırmataş,
    kazı döküm harç bedeli, yükleme/boşaltma bedeli) seçilen döneme göre okur.
    """
    return {
        anahtar: float(_anahtar_satiri_bul(df_fiyatlar, metin)[donem])
        for anahtar, metin in NAKLIYE_KATSAYI_ANAHTARLARI.items()
    }


def donem_etiketlerini_olustur(donem_sutunlari):
    """
    Excel dönem sütun başlıklarını (tarih tipi veya 'GG.AA.YYYY' metni) kronolojik
    sırada, kullanıcıya gösterilecek 'Ay YYYY' etiketleriyle eşleştirir.
    Döner: [(etiket, sütun_adı), ...] — kronolojik (eskiden yeniye) sıralı.
    """
    eslesmeler = []
    for sutun in donem_sutunlari:
        tarih = pd.to_datetime(sutun, dayfirst=True, errors="coerce")
        if pd.isna(tarih):
            eslesmeler.append((str(sutun), sutun, None))
            continue
        etiket = f"{AY_ADLARI_TR[tarih.month]} {tarih.year}"
        eslesmeler.append((etiket, sutun, tarih))

    eslesmeler.sort(key=lambda x: (x[2] is None, x[2]))
    return [(etiket, sutun) for etiket, sutun, _ in eslesmeler]


def birim_fiyat_bul(df_fiyatlar, poz_no, donem):
    """Verilen poz numarası ve dönem için birim fiyatı döner."""
    return df_fiyatlar[df_fiyatlar['POZ NO'].astype(str) == poz_no].iloc[0][donem]
