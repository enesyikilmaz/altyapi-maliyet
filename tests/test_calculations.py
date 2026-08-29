import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations import (
    boru_pozlarini_belirle,
    metraj_hesapla,
    nakliye_fiyatlarini_hesapla,
    hesap_kalemlerini_olustur,
    nakliye_kalemlerini_olustur,
    satir_hesapla,
    maliyet_tablosunu_hesapla,
)
from config import DOLGU_POZU_SERT, DOLGU_POZU_YESIL, BORU_POZ_SOZLUGU


class TestBoruPozlariniBelirle:
    def test_yesil_alan_dolgu_pozu(self):
        pozlar = boru_pozlarini_belirle("Yeşil Alan", 300)
        assert pozlar["dolgu_pozu"] == DOLGU_POZU_YESIL

    def test_sert_zemin_dolgu_pozu(self):
        pozlar = boru_pozlarini_belirle("Sert Zemin (Asfalt/Beton)", 300)
        assert pozlar["dolgu_pozu"] == DOLGU_POZU_SERT

    def test_boru_pozu_katalogdan_gelir(self):
        pozlar = boru_pozlarini_belirle("Yeşil Alan", 600)
        assert pozlar["boru_pozu"] == BORU_POZ_SOZLUGU[600]

    def test_bilinmeyen_cap_icin_boru_pozu_none(self):
        pozlar = boru_pozlarini_belirle("Yeşil Alan", 9999)
        assert pozlar["boru_pozu"] is None


class TestMetrajHesapla:
    def test_sig_kazi_dikdortgen_kesit(self):
        # derinlik <= 1.50 -> şevsiz (dikdörtgen) kesit, ortalama genişlik = taban genişliği
        metraj = metraj_hesapla(ic_cap_mm=300, derinlik=1.0, uzunluk=10, dolgu_pozu=DOLGU_POZU_YESIL)
        taban = metraj["taban_genisligi"]
        assert metraj["kazi_hacmi"] == taban * 1.0 * 10

    def test_derin_kazi_sevli_kesit_daha_genis(self):
        sig = metraj_hesapla(ic_cap_mm=300, derinlik=1.5, uzunluk=10, dolgu_pozu=DOLGU_POZU_YESIL)
        derin = metraj_hesapla(ic_cap_mm=300, derinlik=3.0, uzunluk=10, dolgu_pozu=DOLGU_POZU_YESIL)
        # aynı uzunlukta iki katı derinlik, şev nedeniyle kazı hacmi orantısızca artmalı
        assert derin["kazi_hacmi"] > sig["kazi_hacmi"] * 2

    def test_disCap_ic_captan_buyuk(self):
        metraj = metraj_hesapla(ic_cap_mm=300, derinlik=2.0, uzunluk=10, dolgu_pozu=DOLGU_POZU_YESIL)
        assert metraj["dis_cap_mm"] > 300

    def test_hasir_celik_800_altinda_sifir(self):
        metraj = metraj_hesapla(ic_cap_mm=600, derinlik=2.0, uzunluk=10, dolgu_pozu=DOLGU_POZU_YESIL)
        assert metraj["hasir_celik_miktari_ton"] == 0

    def test_hasir_celik_800_ve_uzeri_pozitif(self):
        metraj = metraj_hesapla(ic_cap_mm=800, derinlik=2.0, uzunluk=10, dolgu_pozu=DOLGU_POZU_YESIL)
        assert metraj["hasir_celik_miktari_ton"] > 0

    def test_yesil_alan_dolgu_nakliyeye_dahil_degil(self):
        # DOLGU_POZU_YESIL: tuvenan dolgu kazıdan çıkan toprakla yapılır, nakliye miktarından düşülür
        metraj = metraj_hesapla(ic_cap_mm=300, derinlik=2.0, uzunluk=10, dolgu_pozu=DOLGU_POZU_YESIL)
        assert metraj["nakliye_kazi_miktari"] == metraj["kazi_hacmi"] - metraj["tuvenan_dolgu_hacmi"]

    def test_sert_zemin_dolgu_kirmatas_nakliyesine_dahil(self):
        metraj = metraj_hesapla(ic_cap_mm=300, derinlik=2.0, uzunluk=10, dolgu_pozu=DOLGU_POZU_SERT)
        assert metraj["nakliye_kirmatas_miktari"] == metraj["kum_dolgu_hacmi_net"] + metraj["tuvenan_dolgu_hacmi"]


ORNEK_NAKLIYE_KATSAYILARI = {
    "A": 1.75,
    "K": 2048.01,
    "G_BETON": 2.40,
    "G_KIRMATAS": 1.60,
    "KAZI_DOKUM_HARC": 80.0,
    "YUKLEME_BOSALTMA": 29.28,
}


class TestNakliyeFiyatlariniHesapla:
    def test_sifir_mesafe_sifir_fiyat(self):
        sonuc = nakliye_fiyatlarini_hesapla(
            mesafe_kazi=0, mesafe_boru=0, mesafe_kirmatas=0,
            nakliye_katsayilari=ORNEK_NAKLIYE_KATSAYILARI,
            boru_malzeme_hacmi=5.0,
        )
        assert sonuc["fiyat_kazi"] == 0
        assert sonuc["fiyat_boru"] == 0
        assert sonuc["fiyat_kirmatas"] == 0

    def test_pozitif_mesafe_pozitif_fiyat(self):
        sonuc = nakliye_fiyatlarini_hesapla(
            mesafe_kazi=12, mesafe_boru=12, mesafe_kirmatas=14,
            nakliye_katsayilari=ORNEK_NAKLIYE_KATSAYILARI,
            boru_malzeme_hacmi=5.0,
        )
        assert sonuc["fiyat_kazi"] > 0
        assert sonuc["fiyat_boru"] > 0
        assert sonuc["fiyat_kirmatas"] > 0

    def test_boru_tonaji_hacim_carpi_yogunluk(self):
        sonuc = nakliye_fiyatlarini_hesapla(
            mesafe_kazi=0, mesafe_boru=0, mesafe_kirmatas=0,
            nakliye_katsayilari=ORNEK_NAKLIYE_KATSAYILARI,
            boru_malzeme_hacmi=5.0,
        )
        assert sonuc["nakliye_boru_ton"] == 5.0 * 2.40

    def test_boru_fiyati_g_beton_kullanir(self):
        # F = A x K x (0.0007xM+0.01) x G_beton
        sonuc = nakliye_fiyatlarini_hesapla(
            mesafe_kazi=0, mesafe_boru=12, mesafe_kirmatas=0,
            nakliye_katsayilari=ORNEK_NAKLIYE_KATSAYILARI,
            boru_malzeme_hacmi=5.0,
        )
        beklenen = 1.75 * 2048.01 * ((0.0007 * 12) + 0.01) * 2.40
        assert math.isclose(sonuc["fiyat_boru"], beklenen)

    def test_kirmatas_fiyati_yukleme_bosaltma_ekler(self):
        sonuc = nakliye_fiyatlarini_hesapla(
            mesafe_kazi=0, mesafe_boru=0, mesafe_kirmatas=14,
            nakliye_katsayilari=ORNEK_NAKLIYE_KATSAYILARI,
            boru_malzeme_hacmi=5.0,
        )
        beklenen = 1.75 * 2048.01 * ((0.0007 * 14) + 0.01) * 1.60 + 29.28
        assert math.isclose(sonuc["fiyat_kirmatas"], beklenen)

    def test_kazi_fiyati_dokum_harc_ekler(self):
        sonuc = nakliye_fiyatlarini_hesapla(
            mesafe_kazi=12, mesafe_boru=0, mesafe_kirmatas=0,
            nakliye_katsayilari=ORNEK_NAKLIYE_KATSAYILARI,
            boru_malzeme_hacmi=5.0,
        )
        beklenen = 1.25 * 2048.01 * ((0.00046 * math.sqrt(12 * 1000)) - 0.0046) + 29.28 + 80.0
        assert math.isclose(sonuc["fiyat_kazi"], beklenen)


class TestSatirHesapla:
    def test_normal_hesaplama(self):
        sonuc = satir_hesapla(miktar=100, karsiz_fiyat=10, k_carpan=1.15)
        assert sonuc["karsiz_tutar"] == 1000
        assert sonuc["karli_fiyat"] == 11.5
        assert sonuc["karli_tutar"] == 1150

    def test_sifir_miktar_none_doner(self):
        assert satir_hesapla(miktar=0, karsiz_fiyat=10, k_carpan=1.15) is None

    def test_sifir_fiyat_none_doner(self):
        assert satir_hesapla(miktar=100, karsiz_fiyat=0, k_carpan=1.15) is None

    def test_negatif_miktar_none_doner(self):
        assert satir_hesapla(miktar=-5, karsiz_fiyat=10, k_carpan=1.15) is None


class TestHesapKalemleriVeTablo:
    def test_maliyet_tablosu_toplamlar_dogru(self):
        pozlar = boru_pozlarini_belirle("Yeşil Alan", 300)
        metraj = metraj_hesapla(ic_cap_mm=300, derinlik=2.0, uzunluk=100, dolgu_pozu=pozlar["dolgu_pozu"])
        hesap_kalemleri = hesap_kalemlerini_olustur(pozlar, 300, 100, metraj)

        sabit_fiyatlar = {
            pozlar["kazi_pozu"]: 100.0,
            pozlar["kum_pozu"]: 200.0,
            pozlar["dolgu_pozu"]: 50.0,
            pozlar["boru_pozu"]: 900.0,
        }

        satirlar, toplam_karsiz, toplam_karli = maliyet_tablosunu_hesapla(
            hesap_kalemleri,
            lambda poz: sabit_fiyatlar.get(poz, 0.0),
            k_carpan=1.15,
            nakliye_kalemleri=[],
        )

        beklenen_karsiz = sum(s["karsiz_tutar"] for s in satirlar)
        assert math.isclose(toplam_karsiz, beklenen_karsiz)
        assert math.isclose(toplam_karli, toplam_karsiz * 1.15)

    def test_800_altinda_hasir_celik_kalemi_yok(self):
        pozlar = boru_pozlarini_belirle("Yeşil Alan", 300)
        metraj = metraj_hesapla(ic_cap_mm=300, derinlik=2.0, uzunluk=100, dolgu_pozu=pozlar["dolgu_pozu"])
        hesap_kalemleri = hesap_kalemlerini_olustur(pozlar, 300, 100, metraj)
        assert not any(k["İşlem"] == "Boru İçi Hasır Çelik Donatı" for k in hesap_kalemleri)

    def test_800_ve_uzeri_hasir_celik_kalemi_var(self):
        pozlar = boru_pozlarini_belirle("Yeşil Alan", 800)
        metraj = metraj_hesapla(ic_cap_mm=800, derinlik=2.0, uzunluk=100, dolgu_pozu=pozlar["dolgu_pozu"])
        hesap_kalemleri = hesap_kalemlerini_olustur(pozlar, 800, 100, metraj)
        assert any(k["İşlem"] == "Boru İçi Hasır Çelik Donatı" for k in hesap_kalemleri)

    def test_nakliye_kalemleri_uc_kalem(self):
        pozlar = boru_pozlarini_belirle("Yeşil Alan", 300)
        metraj = metraj_hesapla(ic_cap_mm=300, derinlik=2.0, uzunluk=100, dolgu_pozu=pozlar["dolgu_pozu"])
        nakliye_fiyatlari = nakliye_fiyatlarini_hesapla(
            mesafe_kazi=12, mesafe_boru=12, mesafe_kirmatas=14,
            nakliye_katsayilari=ORNEK_NAKLIYE_KATSAYILARI,
            boru_malzeme_hacmi=metraj["boru_malzeme_hacmi"],
        )
        nakliye_kalemleri = nakliye_kalemlerini_olustur(nakliye_fiyatlari, metraj)
        assert len(nakliye_kalemleri) == 3
