import pandas as pd
import json
import unicodedata

arquivo_excel = "itens.xlsx"
arquivo_categorias = "categorias.txt"
saida_json = "produtos.json"

# =========================
# NORMALIZAR TEXTO
# =========================
def normalizar(texto):
    if not texto:
        return ""

    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')

    return texto

# =========================
# CARREGAR CATEGORIAS
# =========================
def carregar_categorias():
    categorias = []

    with open(arquivo_categorias, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                categorias.append(linha)

    return categorias

# =========================
# ENCONTRAR CATEGORIA COMPLETA
# =========================
def encontrar_categoria(nome_categoria_excel, categorias_txt):
    nome_norm = normalizar(nome_categoria_excel)

    for cat in categorias_txt:
        if nome_norm in normalizar(cat):
            return cat.strip()

    return f"Outros / {nome_categoria_excel}"

def limpar_preco(valor):
    if not valor or str(valor).strip() == "":
        return 0.0

    valor = str(valor)

    # remove R$, espaços
    valor = valor.replace("R$", "").replace(" ", "")

    # troca vírgula por ponto (caso venha assim)
    valor = valor.replace(",", ".")

    try:
        return float(valor)
    except:
        return 0.0
# =========================
# MAIN
# =========================
def main():
    print("📂 Lendo Excel...")
    df = pd.read_excel(arquivo_excel, header=None)

    categorias_txt = carregar_categorias()

    produtos = []
    categoria_atual = ""

    for i in range(len(df)):
        linha = df.iloc[i]

        col_a = str(linha[0]).strip() if pd.notna(linha[0]) else ""
        col_b = str(linha[1]).strip() if pd.notna(linha[1]) else ""

        # 🔹 Detecta linha de categoria
        if "categoria -" in normalizar(col_a):
            categoria_atual = col_a.replace("Categoria -", "").strip()
            continue

        # 🔹 Ignora cabeçalhos
        if normalizar(col_a) == "codigo":
            continue

        # 🔹 Linhas válidas de produto
        if col_a and col_b and col_a != "nan":

            codigo = col_a
            descricao = col_b

            referencia = str(linha[3]).strip() if pd.notna(linha[3]) else ""
            preco = linha[8] if pd.notna(linha[8]) else 0

            categoria_final = encontrar_categoria(categoria_atual, categorias_txt)

            produto = {
                "Referencia": codigo,
                "Descricao": descricao,
                "Categoria": categoria_final,
                "Classificacao": "",  # se quiser depois podemos inferir
                "Tipo_Produto": "",
                "Preco": limpar_preco(preco)
            }

            produtos.append(produto)

    print(f"💾 Gerando JSON com {len(produtos)} itens...")

    with open(saida_json, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

    print("✅ Finalizado!")

# =========================
# EXECUTAR
# =========================
if __name__ == "__main__":
    main()