"""İstek gövdesi akarken yükleme boyutunu sınırlayan dosya yükleme işleyicisi — H4-03 / Issue #35.

Serializer doğrulaması gövde tamamen alındıktan sonra çalışır; bu işleyici ise her parça alındığında
sayar ve sınır aşıldığında yüklemeyi durdurur (geçici dosyaya fazladan veri yazılmaz). ``Content-Length``
başlığı sınırı açıkça aşıyorsa istek gövde okunmadan 413 ile reddedilir (bkz. ``views``). Üretimde ters
vekil sunucuda da (ör. nginx ``client_max_body_size``) sınır tanımlanmalıdır.
"""
from django.core.files.uploadhandler import FileUploadHandler, StopUpload


class MaxSizeUploadHandler(FileUploadHandler):
    def __init__(self, request, limit: int):
        super().__init__(request)
        self.limit = limit
        self.received = 0
        self.exceeded = False
        self.file_fields: list[str] = []

    def new_file(self, field_name, *args, **kwargs):
        self.file_fields.append(field_name)
        super().new_file(field_name, *args, **kwargs)

    def receive_data_chunk(self, raw_data, start):
        self.received += len(raw_data)
        if self.received > self.limit:
            self.exceeded = True
            raise StopUpload(connection_reset=False)
        return raw_data

    def file_complete(self, file_size):
        return None
