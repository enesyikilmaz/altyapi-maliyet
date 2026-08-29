# Altyapı Maliyet Hesaplama

Kanal kazısı (boru döşeme) iş kalemlerinin metrajını ve yaklaşık maliyetini, kullanıcının girdiği
teknik parametrelere göre otomatik hesaplayan bir Streamlit uygulaması.

Canlı uygulama: https://altyapi-maliyet.streamlit.app/

## Ne yapar?

Kullanıcı; hat uzunluğu, ortalama kazı derinliği, zemin tipi, boru iç çapı ve nakliye
mesafeleri gibi parametreleri girer. Uygulama bunlardan:

- Kazı hacmi, yataklama/kum dolgu hacmi, geri dolgu hacmi
- Boru döşeme metrajı ve (Ø800 mm ve üzeri boru için) hasır çelik donatı miktarı
- Kazı, boru ve kırmataş/kum nakliye miktarları

metrajlarını hesaplar; bu iş kalemlerini `Altyapı Birim Fiyatlar_2.xlsx` içindeki resmi birim
fiyatlarla eşleştirip kârsız ve kârlı (yüklenici kârı eklenmiş) yaklaşık maliyet tablosu üretir.
Sonuçlar; tablo, kanal kesitinin şematik çizimi ve Excel raporu olarak sunulur.

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

Birim fiyatlar, repo içindeki `Altyapı Birim Fiyatlar_2.xlsx` dosyasından okunur. Dosya şu
sütunları içermelidir:

- `SIRA NO`, `POZ NO`, `İŞ KALEMİNİN ADI VE KISA AÇIKLAMASI`, `BİRİMİ`
- En az bir dönemsel birim fiyat sütunu (örn. bir tarih/dönem adı)

Uygulama, dosyadaki ilk dönem sütununu kullanır. Hesaplamada kullanılan POZ numaraları
`config.py` içinde tanımlıdır.

Kendi birim fiyat listeni kullanmak istersen, sayfadaki "Kendi birim fiyat listeni kullan
(opsiyonel)" bölümünden aynı sütun yapısına sahip bir `.xlsx` dosyası yükleyebilirsin.

## Metodoloji Özeti

- Kazı kesiti, 1,50 m'yi aşan derinliklerde 1/3 şevli trapez kesit olarak hesaplanır.
- Nakliye birim fiyatları (kazı, boru, kırmataş/kum), resmi taşıma birim fiyat analizi
  formülüne göre mesafe ve taşıt/zorluk katsayıları (K, A) kullanılarak hesaplanır. Bu
  katsayılar sidebar'daki "Uzman Modu" açıldığında düzenlenebilir; varsayılan değerler resmi
  yönteme göre önceden ayarlanmıştır.
- Boru et kalınlığı, iç çapa göre standart tablo değerlerinden alınır.

## Lisans

Açık kaynak, ticari olmayan bir tahmini hesaplama aracıdır.
