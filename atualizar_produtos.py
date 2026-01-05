import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import fdb

# Carrega as variáveis de ambiente do .env
load_dotenv()

# Força o caminho do fbclient.dll
fdb.load_api(r"C:\Users\Administrator\Desktop\script_imagens\atualizar_produtos\fbclient.dll")

# Carrega variáveis do .env (sem valores fixos)
FB_HOST = os.getenv("FIREBIRD_HOST")
FB_PORT = os.getenv("FIREBIRD_PATH")
FB_DATABASE = os.getenv("FIREBIRD_DATABASE")
FB_USER = os.getenv("FIREBIRD_USER")
FB_PASSWORD = os.getenv("FIREBIRD_PASSWORD")
FB_CHARSET = os.getenv("FIREBIRD_CHARSET", "ISO8859_1")

# Validação das variáveis obrigatórias
if not all([FB_HOST, FB_PORT, FB_DATABASE, FB_USER, FB_PASSWORD]):
    print("❌ Erro: Variáveis obrigatórias ausentes no .env.")
    exit(1)

print("🚀 Conectando ao Firebird...")

try:
    con = fdb.connect(
        host=FB_HOST,
        port=int(FB_PORT),
        database=FB_DATABASE,
        user=FB_USER,
        password=FB_PASSWORD,
        charset=FB_CHARSET
    )
    print("✅ Conexão estabelecida com sucesso!")
except Exception as e:
    print("❌ Erro ao conectar:", e)
    exit(1)

# Consulta itens incluídos nas últimas 24 horas
cursor = con.cursor()
ontem = datetime.now() - timedelta(hours=24)
cursor.execute("""
    SELECT *
    FROM CUSTOM_LISTAGEM_DE_ITENS
    WHERE DATA_INCLUSAO >= ?
""", (ontem,))

colunas = [desc[0] for desc in cursor.description]
registros = [dict(zip(colunas, row)) for row in cursor.fetchall()]

print(f"📦 {len(registros)} registros encontrados nas últimas 24h.")

# Salvar em produtos.json
json_path = os.path.join(os.path.dirname(__file__), "produtos_novos.json")

# Converte datetime para string no formato ISO
def serializar(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(registros, f, ensure_ascii=False, indent=2, default=serializar)

print(f"📁 Arquivo salvo em: {json_path}")
print("🔒 Encerrando conexão.")
cursor.close()
con.close()
