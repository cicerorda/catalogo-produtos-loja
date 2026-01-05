import json
from pathlib import Path

# Caminhos dos arquivos
json_antigo_path = Path(r"C:\Users\Administrator\Desktop\script_imagens\atualizar_produtos\New folder\produtos.json")
json_novos_path = Path(r"C:\Users\Administrator\Desktop\script_imagens\atualizar_produtos\produtos_novos.json")
json_saida_path = Path(r"C:\Users\Administrator\Desktop\script_imagens\atualizar_produtos\New folder\produtos.json")

# Carrega os dados antigos
with open(json_antigo_path, "r", encoding="utf-8") as f:
    antigos = json.load(f)

# Carrega os dados novos
with open(json_novos_path, "r", encoding="utf-8") as f:
    novos = json.load(f)

# Cria um dicionário para mapear prefixo da classificação para categoria
mapa_classificacao_categoria = {}
for item in antigos:
    if "Classificacao" in item and "Categoria" in item:
        prefixo = item["Classificacao"][:7]
        if prefixo not in mapa_classificacao_categoria:
            mapa_classificacao_categoria[prefixo] = item["Categoria"]

# Converte os novos itens para o formato do JSON antigo
novos_convertidos = []
for item in novos:
    prefixo = item["CLASSIFICACAO"][:7]
    categoria = mapa_classificacao_categoria.get(prefixo)
    
    if categoria:  # Só adiciona se encontrou uma categoria correspondente
        novos_convertidos.append({
            "Referencia": item["ITEM"],
            "Descricao": item["DESCRICAO"],
            "Categoria": categoria,
            "Classificacao": item["CLASSIFICACAO"]
        })

# Junta os antigos com os novos (pode adicionar lógica para evitar duplicatas se quiser)
atualizado = antigos + novos_convertidos

# Salva o novo JSON unificado
with open(json_saida_path, "w", encoding="utf-8") as f:
    json.dump(atualizado, f, ensure_ascii=False, indent=2)

print(f"✅ Arquivo mesclado salvo como {json_saida_path}")
print(f"🧮 Itens novos adicionados: {len(novos_convertidos)}")
