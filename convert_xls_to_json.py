import pandas as pd
import json
import os
import unicodedata

# Definir a pasta onde estão os arquivos XLS/XLSX
pasta_arquivos = "produtos metalburgo"

# Verificar se a pasta existe
if not os.path.exists(pasta_arquivos):
    print(f"❌ Erro: A pasta '{pasta_arquivos}' não existe.")
    exit()

# Lista todos os arquivos XLS/XLSX na pasta
arquivos_encontrados = [
    f for f in os.listdir(pasta_arquivos)
    if f.endswith(".xls") or f.endswith(".xlsx")
]

if not arquivos_encontrados:
    print("❌ Nenhum arquivo Excel encontrado na pasta.")
    exit()

print("📂 Arquivos encontrados:", arquivos_encontrados)

# Lista para armazenar os dados de todos os arquivos
produtos = []

def normalizar_coluna(nome):
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
    return (
        nome.strip()
        .lower()
        .replace(" ", "_")
        .replace(".", "")
        .replace("/", "_")
    )

mapeamento_colunas = {
    "referencia": "Referencia",
    "descricao": "Descricao",
    "categoria": "Categoria",
    "classificacao": "Classificacao",
    "tipo_produto": "Tipo_Produto",
}

for arquivo in arquivos_encontrados:
    caminho_arquivo = os.path.join(pasta_arquivos, arquivo)
    engine = "xlrd" if arquivo.endswith(".xls") else "openpyxl"

    try:
        df = pd.read_excel(caminho_arquivo, engine=engine)

        print(f"\n📄 Colunas originais do arquivo {arquivo}:")
        print(df.columns.tolist())

        df.columns = [normalizar_coluna(col) for col in df.columns]

        print("\n🔍 Colunas normalizadas do arquivo:", arquivo)
        print(df.columns.tolist())

        if "referencia" not in df.columns:
            print(f"⚠️ A coluna 'referencia' não foi encontrada no arquivo {arquivo}. Pulando este arquivo.")
            continue

        colunas_validas = {}
        for col in df.columns:
            for chave, valor in mapeamento_colunas.items():
                if col.startswith(chave.lower()):
                    colunas_validas[col] = valor

        if not colunas_validas:
            print(f"⚠️ Nenhuma coluna relevante encontrada em {arquivo}. Pulando este arquivo.")
            continue

        df = df[list(colunas_validas.keys())]
        df = df.rename(columns=colunas_validas)

        categoria_arquivo = os.path.splitext(arquivo)[0]
        df["Categoria"] = categoria_arquivo

        print(f"\n🔍 Amostra de dados do arquivo {arquivo}:")
        print(df.head())

        print(f"\n🔍 Verificando valores nulos no arquivo {arquivo}:")
        print(df.isnull().sum())

        print(f"📊 Antes de remover valores nulos, temos {len(df)} linhas.")

        df = df.dropna(subset=["Referencia", "Descricao", "Categoria"], how="all")

        print(f"📊 Depois de remover valores nulos, temos {len(df)} linhas.")

        if "Classificacao" in df.columns:
            df["Classificacao"] = df["Classificacao"].astype(str).str.zfill(10)

        if "Referencia" in df.columns:
            df["Referencia"] = df["Referencia"].astype(str).str.strip()

        if "Categoria" in df.columns:
            df["Categoria"] = df["Categoria"].astype(str).str.strip()

        df = df.where(pd.notna(df), None)

        produtos_extraidos = df.to_dict(orient="records")
        produtos.extend(produtos_extraidos)

        print(f"✅ {len(produtos_extraidos)} produtos extraídos de {arquivo}.")

    except Exception as e:
        print(f"❌ Erro ao processar {arquivo}: {e}")

print(f"\n✅ Total de {len(produtos)} produtos extraídos.")

# 🔥 Truncagem para categorias especiais
categorias_truncar = ["CONJ. FIV COM PINO", "CONJ FIV OUTROS COMP"]
for produto in produtos:
    cat = produto.get("Categoria", "").strip().upper()
    if any(cat_especial in cat for cat_especial in categorias_truncar):
        ref = produto.get("Referencia", "")
        if ref:
            ref_truncada = ".".join(ref.split(".")[:2])
            produto["Referencia"] = ref_truncada

# 🔥 Deduplicação
referencias_unicas = {}
for p in produtos:
    ref = p.get("Referencia") or ""
    if ref not in referencias_unicas:
        referencias_unicas[ref] = p
    else:
        cat_antiga = referencias_unicas[ref].get("Categoria", "")
        cat_nova = p.get("Categoria", "")
        todas = list(filter(None, cat_antiga.split(", ") + cat_nova.split(", ")))
        categorias_unidas = sorted(set(todas))
        referencias_unicas[ref]["Categoria"] = ", ".join(categorias_unidas)

produtos = list(referencias_unicas.values())
print(f"✅ Produtos únicos após deduplicação: {len(produtos)}")

# 🔽 Exportar somente as referências para CSV
referencias = [{"Referencia": p["Referencia"]} for p in produtos if "Referencia" in p]
df_ref = pd.DataFrame(referencias)
df_ref.to_csv("referencias.csv", index=False, sep=";", encoding="utf-8")
print("✅ Arquivo 'referencias.csv' criado com sucesso.")

# Ordenar produtos
produtos.sort(
    key=lambda p: (
        str(p.get("Categoria") or "").upper(),
        str(p.get("Referencia") or "").upper()
    )
)
print("✅ Produtos ordenados por Categoria e Referencia.")

# Exportar JSON
if produtos:
    with open("produtos.json", "w", encoding="utf-8") as json_file:
        json.dump(produtos, json_file, ensure_ascii=False, indent=4)
    print("\n✅ Conversão concluída! Arquivo 'produtos.json' criado com sucesso.")
else:
    print("\n⚠️ Nenhum dado válido foi extraído dos arquivos.")
