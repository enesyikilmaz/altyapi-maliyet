import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import donem_etiketlerini_olustur


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
