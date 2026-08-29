"""Kanal kazısı metraj ve maliyet hesaplama mantığı — saf fonksiyonlar, Streamlit'ten bağımsız."""

import math

from config import (
    ET_KALINLIKLARI_MM,
    KAZI_POZU,
    KUM_POZU,
    DOLGU_POZU_SERT,
    DOLGU_POZU_YESIL,
    HASIR_CELIK_POZU,
    BORU_POZ_SOZLUGU,
    NAKLIYE_KAZI_POZU,
    NAKLIYE_BORU_POZU,
    NAKLIYE_KIRMATAS_POZU,
)


def boru_pozlarini_belirle(zemin_tipi, ic_cap_mm):
    """Zemin tipi ve boru çapına göre kullanılacak poz numaralarını döner."""
    return {
        "kazi_pozu": KAZI_POZU,
        "kum_pozu": KUM_POZU,
        "dolgu_pozu": DOLGU_POZU_SERT if "Sert Zemin" in zemin_tipi else DOLGU_POZU_YESIL,
        "hasir_celik_pozu": HASIR_CELIK_POZU,
        "boru_pozu": BORU_POZ_SOZLUGU.get(ic_cap_mm),
    }


def metraj_hesapla(ic_cap_mm, derinlik, uzunluk, dolgu_pozu):
    """Kazı, boru, yataklama, geri dolgu ve donatı metrajlarını hesaplar."""
    et_kalinligi = ET_KALINLIKLARI_MM.get(ic_cap_mm, ic_cap_mm * 0.1)
    dis_cap_mm = ic_cap_mm + (2 * et_kalinligi)
    dis_cap_m = dis_cap_mm / 1000.0

    # Çalışma payı eklendi (Boru dış çapı + 100 cm)
    taban_genisligi = dis_cap_m + 1.00
    ortalama_genislik = taban_genisligi + (derinlik / 3) if derinlik > 1.50 else taban_genisligi

    kazi_hacmi = ortalama_genislik * derinlik * uzunluk
    boru_hacmi_dis = math.pi * ((dis_cap_m / 2) ** 2) * uzunluk
    kum_dolgu_yuksekligi = 0.10 + dis_cap_m + 0.30
    kum_ortalama_genislik = taban_genisligi + (kum_dolgu_yuksekligi / 3) if derinlik > 1.50 else taban_genisligi
    kum_dolgu_hacmi_brut = kum_ortalama_genislik * kum_dolgu_yuksekligi * uzunluk
    kum_dolgu_hacmi_net = kum_dolgu_hacmi_brut - boru_hacmi_dis
    tuvenan_dolgu_hacmi = kazi_hacmi - kum_dolgu_hacmi_brut

    hasir_celik_miktari_ton = 0
    if ic_cap_mm >= 800:
        donati_capi_m = (ic_cap_mm + et_kalinligi) / 1000.0
        hasir_celik_alani_m2 = (math.pi * donati_capi_m) * uzunluk
        hasir_celik_miktari_ton = (hasir_celik_alani_m2 * 2.95) / 1000.0

    nakliye_kazi_miktari = kazi_hacmi - (tuvenan_dolgu_hacmi if dolgu_pozu == DOLGU_POZU_YESIL else 0)
    boru_malzeme_hacmi = math.pi * (((dis_cap_m/2)**2) - ((ic_cap_mm/2000)**2)) * uzunluk
    nakliye_kirmatas_miktari = kum_dolgu_hacmi_net + (tuvenan_dolgu_hacmi if dolgu_pozu == DOLGU_POZU_SERT else 0)

    return {
        "et_kalinligi": et_kalinligi,
        "dis_cap_mm": dis_cap_mm,
        "dis_cap_m": dis_cap_m,
        "taban_genisligi": taban_genisligi,
        "kazi_hacmi": kazi_hacmi,
        "kum_dolgu_hacmi_net": kum_dolgu_hacmi_net,
        "tuvenan_dolgu_hacmi": tuvenan_dolgu_hacmi,
        "hasir_celik_miktari_ton": hasir_celik_miktari_ton,
        "nakliye_kazi_miktari": nakliye_kazi_miktari,
        "boru_malzeme_hacmi": boru_malzeme_hacmi,
        "nakliye_kirmatas_miktari": nakliye_kirmatas_miktari,
    }


def nakliye_fiyatlarini_hesapla(
    mesafe_kazi, mesafe_boru, mesafe_kirmatas,
    nakliye_katsayilari, boru_malzeme_hacmi,
):
    """
    Excel'in 'Nakliye Formulleri' sayfasındaki resmi formüle göre nakliye birim
    fiyatlarını ve boru tonajını hesaplar.

    Boru ve kırmataş nakliyesi: F = A x K x (0.0007xM + 0.01) x G
    Kazı nakliyesi, aynı ailenin özel bir türevi olarak farklı bir katsayı setiyle
    hesaplanır (bkz. proje geçmişi); üzerine seçilen ayın döküm sahası harç bedeli eklenir.
    """
    A = nakliye_katsayilari["A"]
    K = nakliye_katsayilari["K"]
    g_beton = nakliye_katsayilari["G_BETON"]
    g_kirmatas = nakliye_katsayilari["G_KIRMATAS"]
    kazi_dokum_harc = nakliye_katsayilari["KAZI_DOKUM_HARC"]
    yukleme_bosaltma = nakliye_katsayilari["YUKLEME_BOSALTMA"]

    fiyat_kazi = (
        1.25 * K * ((0.00046 * math.sqrt(mesafe_kazi * 1000)) - 0.0046) + yukleme_bosaltma + kazi_dokum_harc
        if mesafe_kazi > 0 else 0
    )
    nakliye_boru_ton = boru_malzeme_hacmi * g_beton
    fiyat_boru = (
        A * K * ((0.0007 * mesafe_boru) + 0.01) * g_beton
        if mesafe_boru > 0 else 0
    )
    fiyat_kirmatas = (
        A * K * ((0.0007 * mesafe_kirmatas) + 0.01) * g_kirmatas + yukleme_bosaltma
        if mesafe_kirmatas > 0 else 0
    )
    return {
        "fiyat_kazi": fiyat_kazi,
        "nakliye_boru_ton": nakliye_boru_ton,
        "fiyat_boru": fiyat_boru,
        "fiyat_kirmatas": fiyat_kirmatas,
    }


def hesap_kalemlerini_olustur(pozlar, ic_cap_mm, uzunluk, metraj):
    """Ana iş kalemleri listesini (kazı, boru, yataklama, geri dolgu, donatı) oluşturur."""
    kalemler = [
        {"İşlem": "Kazı", "Poz": pozlar["kazi_pozu"], "Miktar (Sayısal)": metraj["kazi_hacmi"], "Birim": "m³"},
        {"İşlem": f"Boru Döşeme (Ø{ic_cap_mm} mm)", "Poz": pozlar["boru_pozu"], "Miktar (Sayısal)": uzunluk, "Birim": "m"},
        {"İşlem": "Yataklama (Kırmataş/Kum)", "Poz": pozlar["kum_pozu"], "Miktar (Sayısal)": metraj["kum_dolgu_hacmi_net"], "Birim": "m³"},
        {"İşlem": "Geri Dolgu", "Poz": pozlar["dolgu_pozu"], "Miktar (Sayısal)": metraj["tuvenan_dolgu_hacmi"], "Birim": "m³"},
    ]
    if metraj["hasir_celik_miktari_ton"] > 0:
        kalemler.append({
            "İşlem": "Boru İçi Hasır Çelik Donatı",
            "Poz": pozlar["hasir_celik_pozu"],
            "Miktar (Sayısal)": metraj["hasir_celik_miktari_ton"],
            "Birim": "ton",
        })
    return kalemler


def satir_hesapla(miktar, karsiz_fiyat, k_carpan):
    """Bir iş kaleminin kârsız/kârlı birim fiyat ve tutarını hesaplar. Miktar veya fiyat sıfırsa None döner."""
    if miktar <= 0 or karsiz_fiyat <= 0:
        return None
    karli_fiyat = karsiz_fiyat * k_carpan
    return {
        "karsiz_fiyat": karsiz_fiyat,
        "karli_fiyat": karli_fiyat,
        "karsiz_tutar": miktar * karsiz_fiyat,
        "karli_tutar": miktar * karli_fiyat,
    }


def maliyet_tablosunu_hesapla(hesap_kalemleri, birim_fiyat_bul_fn, k_carpan,
                               nakliye_kalemleri):
    """
    Ana iş kalemleri + nakliye kalemleri için satır satır maliyet hesaplar.
    birim_fiyat_bul_fn(poz) -> kârsız birim fiyat döndüren bir fonksiyon olmalı.
    nakliye_kalemleri: [{"İşlem", "Poz", "Miktar (Sayısal)", "Birim", "Fiyat"}] listesi.
    Döner: (satirlar, genel_toplam_karsiz, genel_toplam_karli)
    satirlar: her biri {"İşlem Adı", "Poz No", "Miktar", "Birim", "karsiz_fiyat", "karli_fiyat", "karsiz_tutar", "karli_tutar"}
    """
    satirlar = []
    genel_toplam_karsiz = 0.0
    genel_toplam_karli = 0.0

    for kalem in hesap_kalemleri:
        karsiz_bf = birim_fiyat_bul_fn(kalem["Poz"])
        sonuc = satir_hesapla(kalem["Miktar (Sayısal)"], karsiz_bf, k_carpan)
        if sonuc is None:
            continue
        satirlar.append({
            "İşlem Adı": kalem["İşlem"], "Poz No": kalem["Poz"],
            "Miktar": kalem["Miktar (Sayısal)"], "Birim": kalem["Birim"],
            **sonuc,
        })
        genel_toplam_karsiz += sonuc["karsiz_tutar"]
        genel_toplam_karli += sonuc["karli_tutar"]

    for kalem in nakliye_kalemleri:
        sonuc = satir_hesapla(kalem["Miktar (Sayısal)"], kalem["Fiyat"], k_carpan)
        if sonuc is None:
            continue
        satirlar.append({
            "İşlem Adı": kalem["İşlem"], "Poz No": kalem["Poz"],
            "Miktar": kalem["Miktar (Sayısal)"], "Birim": kalem["Birim"],
            **sonuc,
        })
        genel_toplam_karsiz += sonuc["karsiz_tutar"]
        genel_toplam_karli += sonuc["karli_tutar"]

    return satirlar, genel_toplam_karsiz, genel_toplam_karli


def nakliye_formul_notlarini_olustur():
    """Kullanıcıya gösterilecek, nakliye hesaplarında kullanılan formüllerin açıklama metinlerini döner."""
    return [
        "Kazı Hafriyat Nakliyesi: F = 1,25 × K × (0,00046 × √(M×1000) − 0,0046) + Yükleme/Boşaltma Bedeli + Döküm Sahası Harç Bedeli",
        "Boru Nakliyesi: F = A × K × (0,0007 × M + 0,01) × G (G: betonarme boru malzeme yoğunluğu)",
        "Kırmataş/Kum Nakliyesi: F = A × K × (0,0007 × M + 0,01) × G + Yükleme/Boşaltma Bedeli (G: kırmataş malzeme yoğunluğu)",
        "A: Zorluk katsayısı, K: Taşıt katsayısı, M: Taşıma mesafesi (km) — değerler seçilen birim fiyat dönemine göre Excel'den alınır.",
    ]


def nakliye_kalemlerini_olustur(nakliye_fiyatlari, metraj):
    """Kazı/boru/kırmataş nakliye kalemlerini maliyet tablosu formatında oluşturur."""
    return [
        {
            "İşlem": "Kazı Hafriyat Nakliyesi", "Poz": NAKLIYE_KAZI_POZU,
            "Miktar (Sayısal)": metraj["nakliye_kazi_miktari"], "Birim": "m³",
            "Fiyat": nakliye_fiyatlari["fiyat_kazi"],
        },
        {
            "İşlem": "Boru Nakliyesi", "Poz": NAKLIYE_BORU_POZU,
            "Miktar (Sayısal)": nakliye_fiyatlari["nakliye_boru_ton"], "Birim": "ton",
            "Fiyat": nakliye_fiyatlari["fiyat_boru"],
        },
        {
            "İşlem": "Kırmataş/Kum Nakliyesi", "Poz": NAKLIYE_KIRMATAS_POZU,
            "Miktar (Sayısal)": metraj["nakliye_kirmatas_miktari"], "Birim": "m³",
            "Fiyat": nakliye_fiyatlari["fiyat_kirmatas"],
        },
    ]
