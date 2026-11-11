# H3-06 — Değerlendirme Sınırlılıkları

1. **Küçük örneklem.** 18 senaryo, 3 pozitif. Recall için %95 Wilson aralığı ≈ [0.21, 0.94]. F1 = 0.80
   bir nokta tahminidir; genellenemez.
2. **Kapsam boşluğu.** Test kümesinde POST yöntemi ve 201/405 durum kodları yoktur; GET yalnızca 1 senaryo
   ile temsil edilir. Bu yöntem/kodlar için metrik **ölçülemedi**. Test kümesi bağımsızlığı korumak için
   sonradan genişletilmemiştir; H4+ için yeni, önceden kayda geçirilmiş bir test kümesi önerilir.
3. **Ayırt edicilik.** İki baseline 18/18 senaryoda aynı sonucu vermiştir; bu küme yöntemler arası farkı
   ölçemez. Kusurların tamamı tek bir kontrollü uygulamada bilerek eklenmiştir.
4. **İçerik düzeyi kusurlar.** İki yöntem de yanıt gövdesini doğrulamaz; SC-FLW-003 türü kusurlar FN'dir.
5. **LLM yeniden üretimi yapılmadı.** Bu ortamda Groq erişimi yoktur; PR #83'teki özgün ilk geçiş
   artefaktları köken kontrolünden sonra değerlendirilmiştir. LLM çıktısının tekrarlanabilirliği (aynı
   istemle aynı kod) **ölçülmedi**. Kullanılan sıcaklık kayıtta yoktur (varsayılan 0.0).
6. **Model sapması.** Issue #31 Llama 3.3 70B'yi öngörür; model sağlayıcıda kullanılamadığı için
   (`model_not_found`) H3-05 `groq/openai/gpt-oss-120b` ile yapılmıştır. Sonuçlar Llama 3.3 70B için
   geçerli sayılamaz.
7. **İstem tasarımı ve veri bilgisi.** Her iki üretici de test kümesi dahil 38 senaryonun tamamı için
   çalıştırılmıştır (girdi olarak; eğitim/ayar yok). LLM istem şablonu veri kümesi bilinerek yazılmıştır;
   güvenli beklenen kod isteme açıkça verilir. Bu nedenle sonuçlar "gereksinimden test üretme" yeteneğini
   ölçer, beklenen davranışı kendi başına çıkarma yeteneğini ölçmez.
8. **Kural tabanlı docstring'leri** kusur bilgisini açıklama olarak içerir (H3-04 üretim raporlaması);
   doğrulama ifadelerini etkilemez, ancak katı "kör" üretim değildir.
9. **Mutation score: Bu aşamada ölçülmedi.** Test gücü yalnızca 3 bilinen kusur üzerinden ölçülmüştür.
10. **Desteklenmeyen uç türleri** (dinamik rota, özel izin sınıfı, dosya yükleme, sayfalama…) test
    kümesinde yoktur; gerçek projelerde çalıştırılabilirlik daha düşük olabilir.
11. **Tek ortam.** Değerlendirme Linux / Python 3.13.18 / Django 5.2.19 / DRF 3.18.3 / pytest 9.2.0 ile
    yapılmıştır; H3-05 üretimi Windows'ta yapılmıştır. Başka sürümlerde sonuçlar değişebilir.
