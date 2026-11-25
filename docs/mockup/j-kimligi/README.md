# J Kimliği — Uygulama Ekran Görüntüleri

Bu klasör, #39 frontend'inin **çalışan uygulamadan** alınan ekran görüntülerini içindir
(J "Gece-Sinyal" kimliği: açık tema varsayılan + koyu mod). Figma mockup'ları ayrı klasörde
(`docs/mockup/ekranlar/`); bunlar gerçek React uygulamasının görüntüleridir.

## Nasıl alınır

```bash
cd frontend
npm install     # ilk sefer
npm run dev     # http://localhost:5173
```

Tarayıcıda sırayla aç, her ekranı **açık** ve **koyu** temada yakala (sağ üstteki tema düğmesi):

1. Giriş ekranı
2. Giriş yap (mock; herhangi bir e-posta + parola) → Genel bakış (dashboard)
3. Projeler → Yeni proje (ProjectUpload)

## Dosya adı şablonu

| Dosya | İçerik |
|---|---|
| `01-giris-acik.png` / `01-giris-koyu.png` | Giriş (01) |
| `02-dashboard-acik.png` / `02-dashboard-koyu.png` | Genel bakış (02) |
| `03-proje-yukleme-acik.png` / `03-proje-yukleme-koyu.png` | Proje yükleme (03) |

> Tasarım önizlemesi (kodsuz, paylaşılabilir) olarak J kimliğinin yayımlanmış hâli de kullanılabilir;
> ekip bağlantıyı ayrıca paylaşabilir.
