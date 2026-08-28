"""Kullanıcı girdilerinin doğrulanması."""

from config import MAKS_KAZI_DERINLIGI


def girdileri_dogrula(uzunluk, derinlik, mesafe_kazi, mesafe_boru, mesafe_kirmatas, kar_orani):
    """HESAPLA öncesi tüm sayısal girdileri kontrol eder, hata mesajları listesini döner."""
    hatalar = []
    if uzunluk <= 0:
        hatalar.append("Hat Uzunluğu 0'dan büyük olmalı.")
    if derinlik <= 0:
        hatalar.append("Ortalama Kazı Derinliği 0'dan büyük olmalı.")
    if derinlik > MAKS_KAZI_DERINLIGI:
        hatalar.append(
            f"İş güvenliği ve teknik standartlar gereği ortalama kazı derinliği maksimum "
            f"{MAKS_KAZI_DERINLIGI:.0f} metre olabilir. Daha derin kazılar için özel iksa veya "
            f"kademeli kazı projesi gereklidir."
        )
    if mesafe_kazi < 0 or mesafe_boru < 0 or mesafe_kirmatas < 0:
        hatalar.append("Nakliye mesafeleri negatif olamaz.")
    if kar_orani < 0:
        hatalar.append("Yüklenici kârı negatif olamaz.")
    return hatalar


def gerekli_pozlari_kontrol_et(gerekli_pozlar, poz_listesi):
    """Fiyat listesinde eksik olan poz numaralarını döner."""
    return [poz for poz in gerekli_pozlar if poz not in poz_listesi]
