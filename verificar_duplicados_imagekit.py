# contar_duplicados.py
import os, re, requests
from dotenv import load_dotenv
load_dotenv()

IMAGEKIT_FOLDER = "/imagens"
PRV = os.getenv("IMAGEKIT_PRIVATE_KEY")

def base_name_without_random_suffix(filename: str) -> str:
    name = filename
    if "." in name:
        name = ".".join(name.split(".")[:-1])
    if "_" in name:
        head, tail = name.rsplit("_", 1)
        if re.fullmatch(r"[A-Za-z0-9-]{6,}", tail):
            return head
    return name

def to_clean(nome: str) -> str:
    return re.sub(r"[^a-z0-9]", "", nome.lower())

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

def main():
    print("📄 Coletando relatório…")
    files = list_all_files()
    total = len(files)

    map_base = {}

    for f in files:
        name = f["name"]
        base = base_name_without_random_suffix(name)
        map_base.setdefault(base, []).append(f)

    grupos_duplicados = 0
    arquivos_duplicados = 0

    for base, itens in map_base.items():
        if len(itens) > 1:
            grupos_duplicados += 1
            arquivos_duplicados += (len(itens) - 1)

    print("\n=============================")
    print("📊 RESUMO DE DUPLICADOS")
    print("=============================")
    print(f"Total de arquivos:            {total}")
    print(f"Grupos duplicados (bases):    {grupos_duplicados}")
    print(f"Arquivos duplicados totais:   {arquivos_duplicados}")
    print("=============================\n")

if __name__ == "__main__":
    main()
