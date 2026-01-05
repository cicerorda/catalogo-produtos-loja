import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Caminhos dos arquivos
json_antigo_path = Path(r"C:\Users\Usuario\Desktop\BACKUP\Documents\codigos faculdade\Nova pasta\scripts atualizar\Nova pasta\catalogo-produtos\produtos.json")
json_novos_path = Path(r"C:\Users\Usuario\Desktop\BACKUP\Documents\codigos faculdade\Nova pasta\scripts atualizar\Nova pasta\catalogo-produtos\produtos_novos.json")
json_saida_path = Path(r"C:\Users\Usuario\Desktop\BACKUP\Documents\codigos faculdade\Nova pasta\scripts atualizar\Nova pasta\catalogo-produtos\produtos.json")

# ===== Filtro de prefixos permitidos (4 primeiros dígitos da CLASSIFICACAO) =====
ALLOWED_PREFIXES_4 = {"4040", "4020", "3090", "3040", "3050", "3060", "3075", "3080"}

# ===== Utils =====
def safe_str(v, default=""):
    return v if isinstance(v, str) else default

def class_prefix(cls, n=7):
    cls = safe_str(cls)
    return cls[:n] if len(cls) >= n else cls

def extrair_blocos_aa_bb_ccc(cls: str):
    cls = safe_str(cls)
    aa = cls[0:2] if len(cls) >= 2 else ""
    bb = cls[2:4] if len(cls) >= 4 else ""
    ccc = cls[4:7] if len(cls) >= 7 else ""
    return aa, bb, ccc

def gerar_categoria_prefixo7_mais_descricao(cls: str, descricao: str) -> str:
    """Monta 'AA_BB_CCC_<DESCRICAO>'."""
    aa, bb, ccc = extrair_blocos_aa_bb_ccc(cls)
    return f"{aa}_{bb}_{ccc}_{descricao.strip()}"

def dedup_por_referencia(lista):
    """
    Remove duplicados por 'Referencia'.
    Mantém o primeiro que aparecer para cada Referencia.
    Retorna (dict {ref: item}, qtd_duplicados_removidos).
    """
    by_ref = {}
    duplicados = 0
    for it in lista:
        ref = safe_str(it.get("Referencia"))
        if not ref:
            # se não tem referência, simplesmente ignora (não consegue deduplicar)
            continue
        if ref in by_ref:
            duplicados += 1
            continue
        by_ref[ref] = it
    return by_ref, duplicados

# ===== Carregamento =====
with open(json_antigo_path, "r", encoding="utf-8") as f:
    antigos = json.load(f)

with open(json_novos_path, "r", encoding="utf-8") as f:
    novos = json.load(f)

# ===== Backup =====
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_path = json_antigo_path.with_name(
    f"{json_antigo_path.stem}.backup-{timestamp}{json_antigo_path.suffix}"
)
shutil.copy(json_antigo_path, backup_path)

# ===== Deduplica antigos (ANTES do merge) =====
antigos_by_ref, duplicados_antes = dedup_por_referencia(antigos)

# ===== Mapa prefixo(7) -> Categoria (usando apenas itens já deduplicados) =====
por_prefixo7 = defaultdict(list)
for it in antigos_by_ref.values():
    cls_ant = safe_str(it.get("Classificacao"))
    cat_ant = safe_str(it.get("Categoria"))
    if cls_ant and cat_ant:
        por_prefixo7[class_prefix(cls_ant, 7)].append(cat_ant)

mapa_classificacao_categoria = {
    pref7: Counter(cats).most_common(1)[0][0]
    for pref7, cats in por_prefixo7.items()
}

# ===== Processa novos =====
novos_adicionados = 0
skip_sem_campos = 0
skip_prefixo_nao_permitido = 0
skip_duplicado_sem_mudanca = 0
atualizados = 0
categorias_criadas = set()

for raw in novos:
    cls = safe_str(raw.get("CLASSIFICACAO"))
    ref = safe_str(raw.get("ITEM"))
    desc = safe_str(raw.get("DESCRICAO"))

    # validações básicas
    if not (cls and ref and desc):
        skip_sem_campos += 1
        continue

    # filtro por prefixo da CLASSIFICACAO
    if cls[:4] not in ALLOWED_PREFIXES_4:
        skip_prefixo_nao_permitido += 1
        continue

    # definição de categoria: tenta achar pelo prefixo7, senão cria
    pref7 = class_prefix(cls, 7)
    categoria = mapa_classificacao_categoria.get(pref7)
    if not categoria:
        categoria = gerar_categoria_prefixo7_mais_descricao(cls, desc)
        mapa_classificacao_categoria[pref7] = categoria
        categorias_criadas.add(categoria)

    convertido = {
        "Referencia": ref,
        "Descricao": desc,
        "Categoria": categoria,
        "Classificacao": cls,
    }

    if ref in antigos_by_ref:
        # já existe, tenta atualizar
        base = antigos_by_ref[ref]
        changed = False

        if desc and desc != safe_str(base.get("Descricao")):
            base["Descricao"] = desc
            changed = True
        if cls and cls != safe_str(base.get("Classificacao")):
            base["Classificacao"] = cls
            changed = True
        if categoria and categoria != safe_str(base.get("Categoria")):
            base["Categoria"] = categoria
            changed = True

        if changed:
            atualizados += 1
        else:
            skip_duplicado_sem_mudanca += 1
    else:
        # item realmente novo
        antigos_by_ref[ref] = convertido
        novos_adicionados += 1

# ===== Monta lista final e deduplica DE NOVO (pós-merge) =====
lista_final = list(antigos_by_ref.values())
final_by_ref, duplicados_depois = dedup_por_referencia(lista_final)
atualizado = list(final_by_ref.values())

# ===== Salva =====
with open(json_saida_path, "w", encoding="utf-8") as f:
    json.dump(atualizado, f, ensure_ascii=False, indent=2)

# ===== Relatório =====
print(f"✅ Arquivo mesclado salvo em: {json_saida_path}")
print(f"💾 Backup criado: {backup_path}")
print(f"🧹 Duplicados removidos do antigo (ANTES do merge): {duplicados_antes}")
print(f"➕ Itens novos adicionados (após filtro de classificação): {novos_adicionados}")
print(f"♻️  Itens existentes atualizados: {atualizados}")
print(f"🔁 Novos ignorados por serem iguais aos existentes: {skip_duplicado_sem_mudanca}")
print(f"🚫 Ignorados por prefixo não permitido: {skip_prefixo_nao_permitido}")
print(f"⚠️  Ignorados por falta de campos: {skip_sem_campos}")
print(f"🆕 Categorias criadas (prefixo7 + descrição): {len(categorias_criadas)}")
if categorias_criadas:
    print("   →", ", ".join(sorted(categorias_criadas)))
print(f"🧹 Duplicados removidos no resultado final (DEPOIS do merge): {duplicados_depois}")
print(f"📊 Total final (sem duplicados por Referencia): {len(atualizado)} itens")