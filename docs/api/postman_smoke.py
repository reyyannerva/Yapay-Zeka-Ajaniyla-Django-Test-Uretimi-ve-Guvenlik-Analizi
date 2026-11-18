"""Postman koleksiyonunu (v2.1) canlı sunucuya karşı sırayla çalıştıran küçük doğrulayıcı — H4-05.

Bu araç Postman/Newman DEĞİLDİR. Koleksiyondaki JavaScript test betiklerini çalıştırmaz; yalnızca
koleksiyonda kullanılan iki kalıbı yorumlar:

* ``pm.response.to.have.status(N)``                → durum kodu denetimi
* ``pm.collectionVariables.set("x", <ifade>.alan)`` → yanıt JSON'undaki alanı değişkene yazma

Kullanım (kimlik bilgileri komut satırından/ortamdan verilir, dosyaya yazılmaz):

    API_USERNAME=... API_PASSWORD=... python docs/api/postman_smoke.py --archive proje.zip \
        [--base-url http://127.0.0.1:8000] [--skip "Yeni parola belirle"]
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import uuid
from pathlib import Path
from urllib import error, request

COLLECTION = Path(__file__).with_name("postman_collection.json")
VAR = re.compile(r"\{\{(\w+)\}\}")
STATUS = re.compile(r"to\.have\.status\((\d+)\)")
SET = re.compile(r'collectionVariables\.set\("(\w+)",\s*[\w.()]*?\.(\w+)\)')


def substitute(text: str, variables: dict) -> str:
    return VAR.sub(lambda m: str(variables.get(m.group(1), "")), text)


def flatten(items):
    for it in items:
        if "item" in it:
            yield from flatten(it["item"])
        else:
            yield it


def multipart(fields: list[dict], variables: dict, archive: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = bytearray()
    for f in fields:
        out += f"--{boundary}\r\n".encode()
        if f["type"] == "file":
            ctype = mimetypes.guess_type(archive.name)[0] or "application/zip"
            out += (f'Content-Disposition: form-data; name="{f["key"]}"; filename="{archive.name}"\r\n'
                    f"Content-Type: {ctype}\r\n\r\n").encode()
            out += archive.read_bytes() + b"\r\n"
        else:
            out += f'Content-Disposition: form-data; name="{f["key"]}"\r\n\r\n'.encode()
            out += substitute(f["value"], variables).encode() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--skip", action="append", default=["Yeni parola belirle"])
    args = ap.parse_args()

    coll = json.loads(COLLECTION.read_text(encoding="utf-8"))
    variables = {v["key"]: v.get("value", "") for v in coll["variable"]}
    variables.update(baseUrl=args.base_url.rstrip("/"), username=os.environ["API_USERNAME"],
                     password=os.environ["API_PASSWORD"])
    failures = 0
    for item in flatten(coll["item"]):
        if item["name"] in args.skip:
            print(f"ATLANDI  {item['name']}")
            continue
        r = item["request"]
        url = substitute(r["url"]["raw"], variables)
        headers = {h["key"]: substitute(h["value"], variables) for h in r.get("header", [])}
        if r.get("auth", {}).get("type") != "noauth" and variables.get("accessToken"):
            headers["Authorization"] = f"Bearer {variables['accessToken']}"
        data = None
        body = r.get("body")
        if body and body["mode"] == "raw":
            raw = substitute(body["raw"], variables)
            parsed = json.loads(raw)
            for k, v in list(parsed.items()):  # "{{projectId}}" gibi sayısal kimlikleri sayıya çevir
                if isinstance(v, str) and v.isdigit():
                    parsed[k] = int(v)
            data = json.dumps(parsed).encode()
        elif body and body["mode"] == "formdata":
            data, headers["Content-Type"] = multipart(body["formdata"], variables, args.archive)
        req = request.Request(url, data=data, method=r["method"], headers=headers)
        try:
            with request.urlopen(req) as resp:
                code, payload = resp.status, resp.read()
        except error.HTTPError as exc:
            code, payload = exc.code, exc.read()
        script = "\n".join(line for ev in item.get("event", []) for line in ev["script"]["exec"])
        expected = [int(x) for x in STATUS.findall(script)]
        ok = not expected or code in expected
        if ok and payload:
            try:
                doc = json.loads(payload)
            except ValueError:
                doc = None
            for var, field in SET.findall(script):
                variables[var] = doc[field]
        failures += not ok
        print(f"{'TAMAM' if ok else 'HATA '}    {r['method']:6} {r['url']['raw']:55} → {code}"
              + ("" if ok else f" (beklenen {expected})"))
    print(f"\n{'Başarısız istek yok.' if not failures else f'{failures} istek başarısız.'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
