import os
import sys
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

# ======== CONFIG =========
SOURCE_DIR =    "Nova Pasta"    # r"\\192.168.0.250\New\New2\New"
IMAGEKIT_FOLDER = "/imagens"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
LOOKBACK_HOURS = 99999   # 24
DRY_RUN = False
# =========================

# CREDENCIAIS
PUB = os.getenv("IMAGEKIT_PUBLIC_KEY")
PRV = os.getenv("IMAGEKIT_PRIVATE_KEY")
URL = os.getenv("IMAGEKIT_URL_ENDPOINT")

if not (PUB and PRV and URL):
    print("❌ Defina IMAGEKIT_PUBLIC_KEY, IMAGEKIT_PRIVATE_KEY, IMAGEKIT_URL_ENDPOINT no ambiente.")
    sys.exit(1)

def files_modified_last_hours(base: str | Path, hours: int):
    base = Path(base)
    cutoff = time.time() - hours * 3600
    for p in base.rglob("*"):
        if p.is_file() and p.suffix.lower() in EXTS:
            try:
                stat = p.stat()
                if max(stat.st_mtime, stat.st_ctime) >= cutoff:
                    yield p
            except Exception:
                continue

def upload_to_imagekit(path: Path):
    url = "https://upload.imagekit.io/api/v1/files/upload"
    with open(path, "rb") as file:
        files = {"file": file}
        data = {
            "fileName": path.name,
            "folder": IMAGEKIT_FOLDER,
            "useUniqueFileName": "false"
        }
        auth = (PRV, "")
        response = requests.post(url, files=files, data=data, auth=auth)
        return response

def main():
    upload_candidates = list(files_modified_last_hours(SOURCE_DIR, LOOKBACK_HOURS))
    print("DEBUG - Candidatos a envio:")
    for c in upload_candidates:
        print(" →", c)

    print(f"🕒 Arquivos nas últimas {LOOKBACK_HOURS}h: {len(upload_candidates)}")
    sent, failed = 0, 0

    for path in upload_candidates:
        print(f"⬆️  Enviando: {path.name} → {IMAGEKIT_FOLDER}")
        if DRY_RUN:
            sent += 1
            continue

        try:
            res = upload_to_imagekit(path)
            if res.status_code == 200:
                print(f"✅ Sucesso: {path.name}")
                sent += 1
            else:
                print(f"❌ Falha: {path.name}")
                print("↳ Código:", res.status_code)
                print("↳ Erro:", res.json())
                failed += 1
        except Exception as e:
            print(f"❌ Erro inesperado ao enviar {path.name}: {e}")
            failed += 1

    print("\n📊 Resumo")
    print(f"   Enviados: {sent}")
    print(f"   Falhas: {failed}")

if __name__ == "__main__":
    main()
