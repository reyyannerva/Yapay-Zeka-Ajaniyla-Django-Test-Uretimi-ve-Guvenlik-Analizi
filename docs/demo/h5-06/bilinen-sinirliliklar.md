# Bilinen sınırlılıklar ve notlar · H5-06 / #44

Entegrasyon kontrolünde tespit edilenler. **Politika:** başka bir ekip üyesinin (Reyyan) koduna
müdahale edilmez; sınırlılıklar belgelenir ve ilgili sahibe/issue'ya bırakılır (CLAUDE.md ekip sınırı).
Bu demoda **gösterimi engelleyen kritik bir hata bulunmamıştır.**

## Kurulum / ortam notları (kod hatası değil)

| Not | Durum | Çözüm |
|---|---|---|
| Frontend `node_modules` güncel değilse `recharts` bulunamaz (build/vitest 1 süit kırılır) | Ortam; `recharts@2.15.4` **package.json'da tanımlı** (H5-05'te eklendi) | `cd frontend && npm install` (koda dokunulmaz). Demo kurulum adımlarına eklendi. |
| PostgreSQL için depo içinde `docker-compose.yml` yok | Tasarım kararı (yerel/Docker tek konteyner) | README'de `docker run ... h4pg` komutu verildi |
| `npm audit` dev-only uyarıları | Kabul edildi (sabit sürüm kuralı; major yükseltme kapsam dışı) | H6+'da yeniden değerlendirilebilir |

## Prototip sınırları (tasarım gereği, Hafta 6 kapsamı)

| Konu | Açıklama |
|---|---|
| Analiz yürütme motoru otomatik başlamaz | AnalysisRun QUEUED kaydı oluşur; AST→LLM→sandbox→tarama→rapor pipeline'ı bu sürümde bağlı değil. Bkz. `gercek-vs-prototip.md`. |
| Analiz sonuç ekranları DEMO veriyle | Mock veri + "DEMO" rozeti; gerçek sonuçlar H6 entegrasyonu sonrası gelecek |

## Davranış notları (hata değil, netleştirme)

| Konu | Açıklama |
|---|---|
| Hesap kilidi canlı smoke'ta 429 (throttle) olarak gözlendi | Oran sınırlayıcı (anonim giriş 10/dk) axes 3-hata→403 kilidinden önce devreye girebilir. **3 hatalı giriş → 403 / 15 dk axes kilidi** davranışının birebir doğruluğu backend test suite'inde (470 test) doğrulanır. İkisi birlikte kaba kuvvet korumasını sağlar. |
| Demo verisindeki parolalar açık yazılı | Yalnızca yerel demo hesapları; gerçek sır/parola değil (dosyada açıkça belirtildi). Gerçek parola/anahtar repoya girmez. |

## İlgili sahiplere bırakılanlar

- Analiz motoru entegrasyonu ve gerçek analiz sonuç ekranlarının canlıya bağlanması: **Hafta 6
  issue'ları** (ilgili sahipleriyle planlanır).
- Bu kontrolde Reyyan'ın frontend koduna (#40/#41/#43) ait **düzeltme gerektiren** bir demo-engelleyici
  hata saptanmamıştır.
