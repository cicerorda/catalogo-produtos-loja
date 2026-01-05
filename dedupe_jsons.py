# dedupe_jsons.py

import json, shutil, argparse, datetime, sys
from pathlib import Path
from collections import Counter

# Arquivos padrão
DEFAULT_FILES = ["imagens.json", "produtos.json", "produtos_filtrados.json"]

# Preferências de chaves por arquivo (ordem de prioridade)
PREFERRED_KEYS = {
    "imagens.json": ["nome", "url", "nome_limpo"],
    "produtos.json": ["referencia", "codigo", "id", "nome"],
    "produtos_filtrados.json": ["referencia", "codigo", "id", "nome"],
    # fallback genérico
    "*": ["nome", "referencia", "codigo", "id", "url", "nome_limpo"]
}

def load_json_list(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "imagens" in data and isinstance(data["imagens"], list):
        # caso raro: { "imagens": [ ... ] }
        data = data["imagens"]
    if not isinstance(data, list):
        raise ValueError(f"{path.name}: esperado uma lista JSON; obtido {type(data).__name__}")
    return data

def backup_file(path: Path):
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_suffix(path.suffix + f".backup-{ts}")
    shutil.copy2(path, backup)
    return backup

def pick_key(filename: str, rows: list, forced: str | None) -> str:
    if forced:
        return forced
    prefs = PREFERRED_KEYS.get(filename, PREFERRED_KEYS["*"])
    # escolha: primeira chave preferida que exista em >80% dos itens
    for k in prefs:
        present = sum(1 for r in rows if isinstance(r, dict) and k in r)
        if present >= max(1, int(0.8 * len(rows))):
            return k
    # fallback: chave mais comum entre strings do primeiro nível
    all_keys = Counter()
    for r in rows:
        if isinstance(r, dict):
            all_keys.update(r.keys())
    if all_keys:
        return all_keys.most_common(1)[0][0]
    raise ValueError("Não há campos consistentes para deduplicar.")

def dedupe_list(rows: list, key: str):
    seen = set()
    cleaned = []
    removed = 0
    for r in rows:
        if not isinstance(r, dict):
            cleaned.append(r)  # não arrisca remover estruturas inesperadas
            continue
        val = r.get(key)
        if val in seen:
            removed += 1
            continue
        seen.add(val)
        cleaned.append(r)
    return cleaned, removed

def process_file(path: Path, forced_key: str | None = None):
    print(f"\n📂 {path.name}")
    rows = load_json_list(path)
    print(f"   registros: {len(rows)}")
    key = pick_key(path.name, rows, forced_key)
    print(f"   chave de deduplicação: '{key}'")
    cleaned, removed = dedupe_list(rows, key)
    if removed == 0:
        print("   ✨ nada a remover (sem duplicados)")
        return
    bk = backup_file(path)
    print(f"   💾 backup: {bk.name}")
    path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"   ➖ removidos: {removed} | ✅ agora: {len(cleaned)}")

def main():
    ap = argparse.ArgumentParser(description="Remove duplicados de JSONs (mantém a primeira ocorrência).")
    ap.add_argument("--dir", default=".", help="Pasta onde estão os JSONs (default: atual).")
    ap.add_argument("--arquivo", action="append", help="Arquivo específico (pode repetir).")
    ap.add_argument("--campo", help="Força a chave de deduplicação (ex.: nome, url, referencia).")
    args = ap.parse_args()

    base = Path(args.dir)
    if not base.exists():
        print(f"❌ Pasta não encontrada: {base}")
        sys.exit(1)

    files = [base / f for f in (args.arquivo or DEFAULT_FILES)]
    found_any = False
    for p in files:
        if p.exists():
            found_any = True
            try:
                process_file(p, args.campo)
            except Exception as e:
                print(f"   ⚠️ erro: {e}")
        else:
            print(f"\n📄 {p.name}: (não encontrado; ignorando)")

    if not found_any:
        print("❌ Nenhum arquivo alvo encontrado.")

if __name__ == "__main__":
    main()
