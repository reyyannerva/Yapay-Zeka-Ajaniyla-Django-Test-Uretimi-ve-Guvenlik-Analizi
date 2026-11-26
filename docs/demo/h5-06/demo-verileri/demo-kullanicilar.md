# Demo kullanıcıları (H5-06)

> **UYARI:** Bu kullanıcılar ve parolalar **yalnızca yerel demo içindir; gerçek kimlik bilgisi
> değildir.** Üretimde kullanılmaz. Parolalar burada bilerek açık yazılmıştır çünkü yerel/geçici
> demo hesaplarıdır. Gerçek parola veya API anahtarı repoya yazılmaz.

Demo veritabanına (yerel PostgreSQL `h4pg`, port 5433) aşağıdaki kullanıcılar tohumlanır:

| Kullanıcı adı | E-posta | Parola (demo) | Amaç |
|---|---|---|---|
| `demo_merve` | demo.merve@example.test | `DemoParola!2026` | Ana demo kullanıcısı (giriş, proje CRUD, analiz) |
| `demo_ikinci` | demo.ikinci@example.test | `DemoParola!2026` | İkinci kullanıcı (sahiplik/erişim kontrolü: başkasının kaydını görememe) |
| `demo_kilit` | demo.kilit@example.test | `DemoParola!2026` | Hesap kilidi demosu (3 hatalı giriş → 15 dk kilit) için ayrılmıştır |

## Tohumlama komutu

Depo kökünden (backend ortamı + PostgreSQL `h4pg` ayakta iken):

```bash
cd backend && bvenv/Scripts/python.exe manage.py shell -c "
from django.contrib.auth import get_user_model
U=get_user_model()
for u,e in [('demo_merve','demo.merve@example.test'),('demo_ikinci','demo.ikinci@example.test'),('demo_kilit','demo.kilit@example.test')]:
    o,_=U.objects.get_or_create(username=u, defaults={'email':e})
    o.email=e; o.set_password('DemoParola!2026'); o.is_active=True; o.save()
"
```

> Not: `demo_kilit` kullanıcısı kilit demosunda 15 dakika kilitlenir; kilidi kaldırmak için
> `python manage.py axes_reset` veya bekleme süresi.
