from pathlib import Path

pasta = Path(r"\\192.168.0.250\New\New2\New")

if not pasta.exists():
    print("❌ Pasta de rede inacessível")
else:
    print("✅ Pasta acessível!")
    for arq in pasta.rglob("*"):
        if arq.is_file():
            print("→", arq)
