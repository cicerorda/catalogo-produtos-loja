# sync_imagens_json.py

import os, re, json, shutil, datetime, sys
from pathlib import Path
from typing import Dict, List
from imagekitio import ImageKit
from dotenv import load_dotenv
load_dotenv()
import requests


# ====== CONFIG ======
IMAGEKIT_FOLDER = "/imagens"                # pasta no ImageKit
IMAGENS_JSON_PATH = "imagens.json"          # caminho do JSON no repo/projeto
DRY_RUN = False                             
# ====================

PUB = os.getenv("IMAGEKIT_PUBLIC_KEY")
PRV = os.getenv("IMAGEKIT_PRIVATE_KEY")
URL = os.getenv("IMAGEKIT_URL_ENDPOINT")

if not (PUB and PRV and URL):
    print("❌ Defina IMAGEKIT_PUBLIC_KEY, IMAGEKIT_PRIVATE_KEY e IMAGEKIT_URL_ENDPOINT no ambiente.")
    sys.exit(1)

ik = ImageKit(public_key=PUB, private_key=PRV, url_endpoint=URL)

def list_all_files_in_folder(folder_path: str):
    """
    Lista TODOS os arquivos de uma pasta no ImageKit via API REST.
    Usa paginação com limit/skip. Retorna a lista de itens (dicts).
    """
    out = []
    base = "https://api.imagekit.io/v1/files"
    limit = 1000
    skip = 0
    while True:
        params = {
            "path": folder_path,
            "limit": limit,
            "skip": skip
        }
        r = requests.get(base, params=params, auth=(PRV, ""))
        if r.status_code != 200:
            raise RuntimeError(f"Erro ao listar arquivos: {r.status_code} {r.text}")

        batch = r.json() or []
        if not batch:
            break

        out.extend(batch)
        skip += len(batch)

    return out

def base_name_without_random_suffix(filename: str) -> str:
    """
    Remove o sufixo aleatório do ImageKit (após o ÚLTIMO "_") e a extensão.
    Ex.: '136556_F.1577.09_y3z3xYmXq.jpg' -> '136556_F.1577.09'
    Se não houver '_', remove só a extensão.
    """
    name = filename
    # tira extensão
    if "." in name:
        name = ".".join(name.split(".")[:-1])
    # remove o último _<token> se parecer aleatório (>=6 alfanum)
    if "_" in name:
        head, tail = name.rsplit("_", 1)
        if re.fullmatch(r"[A-Za-z0-9-]{6,}", tail):
            return head
    return name

def to_nome_limpo(nome: str) -> str:
    """Lowercase e somente [a-z0-9]."""
    return re.sub(r"[^a-z0-9]", "", nome.lower())

def load_imagens_json(path: str) -> List[Dict]:
    p = Path(path)
    if not p.exists():
        return []
    txt = p.read_text(encoding="utf-8").strip()
    if not txt:
        return []
    try:
        data = json.loads(txt)
        if isinstance(data, list):
            return data
        # caso esteja salvo como { "imagens": [...] }
        if isinstance(data, dict) and "imagens" in data and isinstance(data["imagens"], list):
            return data["imagens"]
        raise ValueError("Formato de imagens.json inesperado.")
    except Exception as e:
        raise RuntimeError(f"Falha ao ler {path}: {e}")

def save_imagens_json(path: str, data: List[Dict]):
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    print("📥 Lendo imagens.json…")
    current = load_imagens_json(IMAGENS_JSON_PATH)
    by_nome = {item.get("nome"): item for item in current if "nome" in item}

    print(f"✅ Entradas atuais no JSON: {len(current)}")

    print(f"🔎 Listando arquivos no ImageKit em {IMAGEKIT_FOLDER}…")
    files = list_all_files_in_folder(IMAGEKIT_FOLDER)
    print(f"✅ Arquivos encontrados no ImageKit: {len(files)}")

    added = 0
    for item in files:
        filename = item.get("name")              
        url = item.get("url")                    
        if not filename or not url:
            continue

        base = base_name_without_random_suffix(filename)  
        nome = base.replace(".","").replace("..",".")     
        nome = base if base else filename

        nome_limpo = to_nome_limpo(nome)

        if nome in by_nome:
            # já existe essa chave no JSON -> pulamos
            continue

        current.append({
            "nome": nome,
            "nome_limpo": nome_limpo,
            "url": url
        })
        by_nome[nome] = True
        added += 1

    print(f"➕ Novos registros a adicionar: {added}")
    if added == 0:
        print("✨ Nada para fazer. JSON já está alinhado com a pasta do ImageKit.")
        return

    if DRY_RUN:
        print("🔎 DRY_RUN=True: não vou gravar alterações.")
        return

    print("💾 Gravando imagens.json (com backup automático)…")
    save_imagens_json(IMAGENS_JSON_PATH, current)
    print("✅ Finalizado!")

if __name__ == "__main__":
    main()
