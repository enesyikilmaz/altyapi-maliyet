import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation import girdileri_dogrula, gerekli_pozlari_kontrol_et


VALID = dict(uzunluk=100, derinlik=2.0, mesafe_kazi=12, mesafe_boru=12, mesafe_kirmatas=14, kar_orani=15)


class TestGirdileriDogrula:
    def test_gecerli_girdi_hatasiz(self):
        assert girdileri_dogrula(**VALID) == []

    def test_sifir_uzunluk_hata(self):
        hatalar = girdileri_dogrula(**{**VALID, "uzunluk": 0})
        assert any("Uzunluğu" in h for h in hatalar)

    def test_negatif_uzunluk_hata(self):
        hatalar = girdileri_dogrula(**{**VALID, "uzunluk": -10})
        assert any("Uzunluğu" in h for h in hatalar)

    def test_sifir_derinlik_hata(self):
        hatalar = girdileri_dogrula(**{**VALID, "derinlik": 0})
        assert any("Derinliği" in h for h in hatalar)

    def test_8m_altinda_derinlik_gecerli(self):
        assert girdileri_dogrula(**{**VALID, "derinlik": 7.99}) == []

    def test_8m_derinlik_hata(self):
        hatalar = girdileri_dogrula(**{**VALID, "derinlik": 8.0})
        assert any("maksimum" in h for h in hatalar)

    def test_8m_ustu_derinlik_hata(self):
        hatalar = girdileri_dogrula(**{**VALID, "derinlik": 8.5})
        assert any("maksimum" in h for h in hatalar)

    def test_negatif_mesafe_hata(self):
        hatalar = girdileri_dogrula(**{**VALID, "mesafe_kazi": -1})
        assert any("negatif olamaz" in h for h in hatalar)

    def test_negatif_kar_orani_hata(self):
        hatalar = girdileri_dogrula(**{**VALID, "kar_orani": -1})
        assert any("Yüklenici kârı" in h for h in hatalar)

    def test_birden_fazla_hata_birikir(self):
        hatalar = girdileri_dogrula(**{**VALID, "uzunluk": 0, "derinlik": 0})
        assert len(hatalar) == 2


class TestGerekliPozlariKontrolEt:
    def test_tum_pozlar_mevcut(self):
        assert gerekli_pozlari_kontrol_et(["A", "B"], ["A", "B", "C"]) == []

    def test_eksik_poz_bulunur(self):
        eksik = gerekli_pozlari_kontrol_et(["A", "B", "X"], ["A", "B", "C"])
        assert eksik == ["X"]
