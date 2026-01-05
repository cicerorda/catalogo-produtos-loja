import os
import io
import random
import requests
from PIL import Image
from dotenv import load_dotenv
from imagekitio import ImageKit
import base64

load_dotenv()

IMAGEKIT_FOLDER = "/imagens"
TEST_LIMIT = 5  # quantidade para testar

PUB = os.getenv("IMAGEKIT_PUBLIC_KEY")
PRV = os.getenv("IMAGEKIT_PRIVATE_KEY")
URL = os.getenv("IMAGEKIT_URL_ENDPOINT")

ik = ImageKit(
    public_key=PUB,
    private_key=PRV,
    url_endpoint=URL
)

def list_all_files():
    out = []
    base = "https://api.imagekit.io/v1/files"
    limit = 1000
    skip = 0

    while True:
        params = {"path": IMAGEKIT_FOLDER, "limit": limit, "skip": skip}
        r = requests.get(base, params=params, auth=(PRV, ""))

        batch = r.json()
        if not batch:
            break

        out.extend(batch)
        skip += len(batch)

    return out


def convert_image_to_webp(url, max_width=1200):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    img = Image.open(io.BytesIO(response.content))

    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=80)
    output.seek(0)

    return output, len(response.content), len(output.getvalue())

def upload_converted(base_name, file_bytes):
    filename = f"{base_name}.webp"
    upload_url = "https://upload.imagekit.io/api/v1/files/upload"

    # Conteúdo em base64
    file_base64 = base64.b64encode(file_bytes.getvalue()).decode()

    payload = {
        "file": file_base64,
        "fileName": filename,
        "folder": IMAGEKIT_FOLDER
    }

    response = requests.post(
        upload_url,
        auth=(PUB, PRV),  # <-- AUTENTICAÇÃO CORRETA
        data=payload
    )

    if response.status_code not in (200, 201):
        print(response.text)
        raise Exception(f"Erro no upload: {response.status_code} {response.text}")

    return True

def main():
    print("🔎 Listando imagens no ImageKit…")
    files = list_all_files()

    selected = random.sample(files, TEST_LIMIT)
    print(f"📸 Selecionadas {TEST_LIMIT} imagens para teste.")

    for f in selected:
        name = f["name"]
        url = f["url"]

        print("\n-----------------------------")
        print(f"📌 Imagem: {name}")
        print(f"🌐 URL: {url}")

        base_name = name.split(".")[0]

        try:
            webp_file, original_size, webp_size = convert_image_to_webp(url)

            reduction = 100 - (webp_size * 100 / original_size)
            print(f"📦 Tamanho original: {original_size/1024:.2f} KB")
            print(f"📦 Tamanho WebP:     {webp_size/1024:.2f} KB")
            print(f"📉 Redução:          {reduction:.1f}%")

            print("⬆️  Enviando versão WebP para ImageKit…")
            upload_converted(base_name, webp_file)
            print("✅ Upload concluído!")

        except Exception as e:
            print(f"❌ Erro ao processar {name}: {e}")

    print("\n🎉 Teste concluído! Verifique as 5 imagens no painel do ImageKit.")


if __name__ == "__main__":
    main()
