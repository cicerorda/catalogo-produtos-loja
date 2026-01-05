import json

# Lê o arquivo produtos.json
with open('produtos.json', 'r', encoding='utf-8') as f:
    produtos = json.load(f)

# Corrigido: usa 'Categoria' com "C" maiúsculo
produtos_filtrados = [
    produto for produto in produtos
    if 'Categoria' in produto and (
        'enfeite' in produto['Categoria'].lower() or 'fivela' in produto['Categoria'].lower()
    )
]

# Salva o novo JSON filtrado
with open('produtos_filtrados.json', 'w', encoding='utf-8') as f:
    json.dump(produtos_filtrados, f, ensure_ascii=False, indent=2)

print(f"✅ {len(produtos_filtrados)} produtos encontrados e salvos em 'produtos_filtrados.json'.")
