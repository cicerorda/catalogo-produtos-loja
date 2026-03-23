import json
from pathlib import Path
import math

# =========================
# CONFIG
# =========================
base_path = Path(r"C:\Users\Administrator\Desktop\script_imagens\atualizar_produtos\New Folder")

produtos_dir = base_path / "produtos"
index_path = base_path / "produtos_index.json"
json_novos_path = Path(r"C:\Users\Administrator\Desktop\script_imagens\atualizar_produtos\produtos_novos.json")

itens_por_arquivo = 5000

# =========================
# 1 - CARREGAR PRODUTOS EXISTENTES
# =========================

antigos = []

json_antigo_path = base_path / "produtos.json"

# Caso 1 — novo formato já existe
if index_path.exists():

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    for arquivo in index["arquivos"]:
        caminho = produtos_dir / arquivo

        if caminho.exists():
            with open(caminho, "r", encoding="utf-8") as f:
                antigos.extend(json.load(f))

    print(f"📦 Carregado formato novo ({len(antigos)} produtos)")


# Caso 2 — primeira execução com JSON único
elif json_antigo_path.exists():

    with open(json_antigo_path, "r", encoding="utf-8") as f:
        antigos = json.load(f)

    print(f"📦 Carregado JSON antigo ({len(antigos)} produtos)")

else:

    print("⚠️ Nenhum produto existente encontrado")

# =========================
# 2 - CARREGAR PRODUTOS NOVOS
# =========================

with open(json_novos_path, "r", encoding="utf-8") as f:
    novos = json.load(f)

# =========================
# 3 - MAPEAR CLASSIFICAÇÃO → CATEGORIA
# =========================

mapa_classificacao_categoria = {}

for item in antigos:
    if "Classificacao" in item and "Categoria" in item:
        prefixo = item["Classificacao"][:7]
        if prefixo not in mapa_classificacao_categoria:
            mapa_classificacao_categoria[prefixo] = item["Categoria"]

# =========================
# 4 - CONVERTER NOVOS
# =========================

novos_convertidos = []

for item in novos:

    prefixo = item["CLASSIFICACAO"][:7]
    categoria = mapa_classificacao_categoria.get(prefixo)

    if categoria:
        novos_convertidos.append({
            "Referencia": item["ITEM"],
            "Descricao": item["DESCRICAO"],
            "Categoria": categoria,
            "Classificacao": item["CLASSIFICACAO"]
        })

print(f"🆕 Novos convertidos: {len(novos_convertidos)}")

# =========================
# 5 - UNIR LISTAS (NOVO SOBRESCREVE)
# =========================

mapa_produtos = {}

# adiciona antigos
for item in antigos:
    mapa_produtos[item["Referencia"]] = item

# adiciona novos (sobrescreve se existir)
for item in novos_convertidos:
    mapa_produtos[item["Referencia"]] = item

atualizado = list(mapa_produtos.values())

print(f"📊 Total após atualização: {len(atualizado)}")

# =========================
# 6 - DIVIDIR EM ARQUIVOS
# =========================

produtos_dir.mkdir(exist_ok=True)

arquivos = []
total_arquivos = math.ceil(len(atualizado) / itens_por_arquivo)

for i in range(total_arquivos):

    inicio = i * itens_por_arquivo
    fim = inicio + itens_por_arquivo
    bloco = atualizado[inicio:fim]

    nome_arquivo = f"produtos_{i:03}.json"
    caminho = produtos_dir / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(bloco, f, ensure_ascii=False)

    arquivos.append(nome_arquivo)

print(f"📂 Arquivos gerados: {len(arquivos)}")

# =========================
# 7 - GERAR INDEX
# =========================

index = {
    "arquivos": arquivos
}

with open(index_path, "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print("✅ produtos_index.json atualizado")