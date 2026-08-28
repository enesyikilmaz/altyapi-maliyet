"""Birim fiyat Excel dosyasının okunması, önbelleğe alınması ve şema doğrulaması."""

import pandas as pd
import streamlit as st

from config import SABIT_SUTUNLAR


@st.cache_data
def fiyat_listesini_yukle(dosya_yolu):
    """Birim fiyat Excel'ini okur, şemayı doğrular ve önbelleğe alır."""
    df = pd.read_excel(dosya_yolu)

    eksik_sutunlar = [s for s in SABIT_SUTUNLAR if s not in df.columns]
    if eksik_sutunlar:
        raise KeyError(
            f"Excel dosyasında beklenen sütun(lar) bulunamadı: {', '.join(eksik_sutunlar)}"
        )

    donem_sutunlari = [col for col in df.columns if col not in SABIT_SUTUNLAR]
    if not donem_sutunlari:
        raise KeyError("Excel dosyasında en az bir dönemsel birim fiyat sütunu bulunmalı.")

    return df, donem_sutunlari


def birim_fiyat_bul(df_fiyatlar, poz_no, donem):
    """Verilen poz numarası ve dönem için birim fiyatı döner."""
    return df_fiyatlar[df_fiyatlar['POZ NO'].astype(str) == poz_no].iloc[0][donem]
