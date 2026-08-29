import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from data import donem_etiketlerini_olustur, nakliye_katsayilarini_bul, ACIKLAMA_SUTUNU


class TestDonemEtiketleriniOlustur:
    def test_kronolojik_siralama(self):
        # sütunlar bilerek karışık sırada, çıktı kronolojik olmalı
        sutunlar = ["01.11.2025", "01.09.2025", "01.10.2025"]
        eslesmeler = donem_etiketlerini_olustur(sutunlar)
        etiketler = [e for e, _ in eslesmeler]
        assert etiketler == ["Eylül 2025", "Ekim 2025", "Kasım 2025"]

    def test_sutun_adi_korunur(self):
        sutunlar = ["01.09.2025"]
        eslesmeler = donem_etiketlerini_olustur(sutunlar)
        etiket, sutun = eslesmeler[0]
        assert sutun == "01.09.2025"
        assert etiket == "Eylül 2025"

    def test_yil_donumu_dogru_siralanir(self):
        sutunlar = ["01.01.2026", "01.12.2025"]
        eslesmeler = donem_etiketlerini_olustur(sutunlar)
        etiketler = [e for e, _ in eslesmeler]
        assert etiketler == ["Aralık 2025", "Ocak 2026"]

    def test_tam_donem_araligi(self):
        # Eylül 2025 - Ağustos 2026, 12 ay
        aylar = [
            "01.09.2025", "01.10.2025", "01.11.2025", "01.12.2025",
            "01.01.2026", "01.02.2026", "01.03.2026", "01.04.2026",
            "01.05.2026", "01.06.2026", "01.07.2026", "01.08.2026",
        ]
        eslesmeler = donem_etiketlerini_olustur(aylar)
        etiketler = [e for e, _ in eslesmeler]
        assert etiketler[0] == "Eylül 2025"
        assert etiketler[-1] == "Ağustos 2026"
        assert len(etiketler) == 12


def _ornek_fiyat_df():
    return pd.DataFrame({
        "SIRA NO": [1, 20, 21, 22, 23, 24, 25],
        "POZ NO": ["KGM 14.210", "-", "-", "10.110.1003", "-", "-", "15.100.1002"],
        ACIKLAMA_SUTUNU: [
            "Kazı işi",
            "A: Zorluk katsayısı",
            "K: Taşıt katsayısı",
            "G: Betonarme boru malzeme yoğunluğu",
            "G: Kırmataş malzeme yoğunluğu",
            "Kazı nakliyesi için döküm sahası harç bedeli",
            "1 m³ kum... taşıtlara yükleme, boşaltma ve figüresi",
        ],
        "BİRİMİ": ["m³", "-", "-", "t/m³", "t/m³", "m³", "m³"],
        "01.09.2025": [300.0, 1.75, 2048.01, 2.40, 1.60, 80.0, 29.28],
    })


class TestNakliyeKatsayilariniBul:
    def test_tum_katsayilar_okunur(self):
        df = _ornek_fiyat_df()
        katsayilar = nakliye_katsayilarini_bul(df, "01.09.2025")
        assert katsayilar["A"] == 1.75
        assert katsayilar["K"] == 2048.01
        assert katsayilar["G_BETON"] == 2.40
        assert katsayilar["G_KIRMATAS"] == 1.60
        assert katsayilar["KAZI_DOKUM_HARC"] == 80.0
        assert katsayilar["YUKLEME_BOSALTMA"] == 29.28

    def test_eksik_satir_keyerror_verir(self):
        df = _ornek_fiyat_df()
        df = df[~df[ACIKLAMA_SUTUNU].str.contains("Zorluk", case=False)]
        import pytest
        with pytest.raises(KeyError):
            nakliye_katsayilarini_bul(df, "01.09.2025")
