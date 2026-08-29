"""Sabitler ve konfigürasyon: poz numaraları, boru katalog verileri, nakliye formülü satır anahtarları."""

FIYAT_DOSYASI = "Altyapı Birim Fiyatlar.xlsx"
FIYAT_SAYFASI = "Sayfa1"

SABIT_SUTUNLAR = ['SIRA NO', 'POZ NO', 'İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI', 'BİRİMİ']

# Sayfa1'in alt kısmındaki nakliye formülü katsayı satırlarını "İŞ KALEMİNİN ADI VE KISA
# AÇIKLAMASI" sütunundaki metne göre bulmak için kullanılan anahtar kelimeler. Satır
# numarası değil metin araması kullanılıyor çünkü Excel'e satır eklenip çıkarılabilir.
NAKLIYE_KATSAYI_ANAHTARLARI = {
    "A": "zorluk katsay",
    "K": "taşıt katsay",
    "G_BETON": "betonarme boru malzeme yoğunlu",
    "G_KIRMATAS": "kırmataş malzeme yoğunlu",
    "KAZI_DOKUM_HARC": "döküm sahası harç",
    "YUKLEME_BOSALTMA": "yükleme, boşaltma ve figür",
}

KAZI_POZU = "KGM 14.210"
KUM_POZU = "43.610.1053"
DOLGU_POZU_SERT = "43.610.1064"
DOLGU_POZU_YESIL = "43.610.1004"
HASIR_CELIK_POZU = "43.665.1011"

BORU_CAPLARI = [300, 400, 500, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400]

BORU_POZ_SOZLUGU = {
    300: "43.526.1123", 400: "43.526.1124", 500: "43.526.1125", 600: "43.526.1126",
    800: "43.526.1162", 1000: "43.526.1163", 1200: "43.526.1164", 1400: "43.526.1165",
    1600: "43.526.1201", 1800: "43.526.1202", 2000: "43.526.1203", 2200: "43.526.1204",
    2400: "43.526.1205"
}

ET_KALINLIKLARI_MM = {
    300: 50, 400: 50, 500: 60, 600: 70, 800: 90, 1000: 110,
    1200: 130, 1400: 150, 1600: 170, 1800: 180, 2000: 200, 2200: 220, 2400: 240
}

MAKS_KAZI_DERINLIGI = 8.0

AY_ADLARI_TR = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

# Nakliye poz kodları (resmi birim fiyat analiz yöntemi formülleri).
NAKLIYE_KAZI_POZU = "SNBF.27-A"
NAKLIYE_BORU_POZU = "SNBF.BF"
NAKLIYE_KIRMATAS_POZU = "SNBF.14"

RENK_PALETI = {
    "arka_plan": "#E4E0E1",
    "sidebar": "#D6C0B3",
    "metin": "#493628",
    "buton_hover": "#AB886D",
}
