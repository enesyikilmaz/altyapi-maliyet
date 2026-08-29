# Altyapı Maliyet Hesaplama

Kanal kazısı (boru döşeme) iş kalemlerinin metrajını ve yaklaşık maliyetini, kullanıcının girdiği
teknik parametrelere göre otomatik hesaplayan bir Streamlit uygulaması.

Canlı uygulama: https://altyapi-maliyet.streamlit.app/

## Ne yapar?

Kullanıcı; birim fiyat dönemi, hat uzunluğu, ortalama kazı derinliği, zemin tipi, boru iç çapı ve
nakliye mesafeleri gibi parametreleri girer. Uygulama bunlardan:

- Kazı hacmi, yataklama/kum dolgu hacmi, geri dolgu hacmi
- Boru döşeme metrajı ve (Ø800 mm ve üzeri boru için) hasır çelik donatı miktarı
- Kazı, boru ve kırmataş/kum nakliye miktarları

metrajlarını hesaplar; bu iş kalemlerini `Altyapı Birim Fiyatlar.xlsx` içindeki, seçilen aya ait
kârsız birim fiyatlarla eşleştirip yüklenici kârı eklenmiş yaklaşık maliyet tablosu üretir.
Nakliye kalemleri (kazı, boru, kırmataş/kum) için taşıt/zorluk katsayıları da seçilen aya göre
otomatik alınır. Sonuçlar; tablo ve kanal kesitinin şematik çizimi olarak sunulur, Excel raporu
olarak indirilebilir.

**Not:** Bu araç yaklaşık bir maliyet tahmini üretir; resmi bir keşif/metraj raporu yerine geçmez.

## Kurulum ve Çalıştırma

```bash
git clone https://github.com/enesyikilmaz/altyapi-maliyet.git
cd altyapi-maliyet
pip install -r requirements.txt
streamlit run app.py
```

Uygulama varsayılan olarak http://localhost:8501 adresinde açılır.

## Veri Kaynağı

Birim fiyatlar, repo içindeki `Altyapı Birim Fiyatlar.xlsx` dosyasının **Sayfa1** sayfasından
okunur. Sayfa şu yapıya sahip olmalıdır:

- İlk sütunlar: `SIRA NO`, `POZ NO`, `İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI`, `BİRİMİ`
- Her ay için bir dönemsel (kârsız) birim fiyat sütunu; sütun başlığı o ayın ilk gününü
  temsil eden bir tarih olmalıdır (örn. Eylül 2025 için `01.09.2025`)
- İş kalemi satırlarının altında, nakliye formülünde kullanılan katsayı satırları: zorluk
  katsayısı (A), taşıt katsayısı (K), betonarme boru ve kırmataş malzeme yoğunlukları (G),
  kazı nakliyesi döküm sahası harç bedeli ve yükleme/boşaltma/figüre bedeli — bu satırlar
  açıklama metnindeki anahtar kelimelerle (`config.py` → `NAKLIYE_KATSAYI_ANAHTARLARI`)
  bulunur, satır numarasına bağımlı değildir

Uygulama, sütun başlıklarındaki tarihleri okuyup sidebar'da "Birim Fiyat Dönemi" açılır
listesinde kronolojik sırada ("Eylül 2025", "Ekim 2025", ...) sunar; varsayılan olarak en
güncel (son) dönem seçili gelir. Seçilen döneme göre hem iş kalemi birim fiyatları hem de
nakliye katsayıları otomatik güncellenir. Hesaplamada kullanılan POZ numaraları `config.py`
içinde tanımlıdır.

**"Nakliye Formulleri" sayfası:** Excel'deki bu sayfa, kullanılan resmi nakliye formülünü
belgeler; uygulama bu sayfayı okumaz, sadece referans amaçlıdır. Formülün kendisi
`calculations.py` içinde uygulanmıştır ve sonuç ekranında kullanıcıya özetlenir.

## Metodoloji Özeti

- Kazı kesiti, 1,50 m'yi aşan derinliklerde 1/3 şevli trapez kesit olarak hesaplanır.
- Kazı hafriyat nakliyesi: `F = 1,25 × K × (0,0014×M + 0,02) − 0,00325×K` (KGM 14.210 poz
  notu, uzun mesafe formülü; M: taşıma mesafesi km, K: taşıt katsayısı). Üzerine seçilen ayın
  döküm sahası harç bedeli eklenir; yükleme/boşaltma bedeli eklenmez.
- Boru ve kırmataş/kum nakliye birim fiyatları: `F = A × K × (0,0007×M + 0,01) × G` (M: taşıma
  mesafesi km, G: ilgili malzemenin yoğunluğu). Boru nakliyesinde miktar ton cinsinden
  alındığından G=1 sabittir; kırmataş nakliyesine ayrıca yükleme/boşaltma bedeli eklenir.
- A, K, G ve ek bedeller seçilen birim fiyat dönemine göre Excel'den otomatik alınır; kullanıcı
  tarafından değiştirilemez.
- Boru et kalınlığı, iç çapa göre standart tablo değerlerinden alınır.

## Lisans

Açık kaynak, ticari olmayan bir tahmini hesaplama aracıdır.
