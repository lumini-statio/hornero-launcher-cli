import hashlib
import json
from pathlib import Path
from .ensablar_comando import construir_ejecutable
import requests


def encontrar_version_coincidente(version_buscada: str):
    import json
    with open("./data/versiones.json", "r", encoding="utf-8") as f:
        data: dict[str, dict] = json.load(f)

    versiones_parecidas = {}
    for id, version in enumerate(data["versions"], 1):
        if not (version_buscada in version["id"]):
            continue

        print(f"{id}: version: {version['id']} - tipo: {version['type']}")
        
        versiones_parecidas[str(id)] = \
            {
                "version": version["id"],
                "tipo": version["type"],
                "url": version["url"],
                "sha1": version["sha1"]
            }

    return versiones_parecidas


def descargar_version(json_version: str, version: dict, base):
    res = requests.get(version["url"])
    
    sha1 = hashlib.sha1()

    with open(json_version, "w", encoding="utf-8") as f:
        data = res.json()
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    with open(json_version, "r") as f:
        data = json.load(f)
        cliente = data["downloads"]["client"]["url"]
        servidor = data["downloads"]["server"]["url"]
    
    with requests.get(cliente, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(f"{base}/versions/{version['version']}/{version['version']}.jar", "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                f.write(chunk)
                sha1.update(chunk)


def buscar_y_descargar(base, so):
    import os
    ver: str = input("> version del juego a buscar: ")
    versiones = encontrar_version_coincidente(ver)
    
    print("="*50)
    print(" ")
    print("="*50)
    print("\n")

    id: str = input("seleccione el id de la version a descargar: ")
    version = versiones[id]
    
    lanzador = f"data/lanzador_{version['version']}"
    direc = Path(base) / f"versions/{version['version']}"
    direc.mkdir(exist_ok=True)

    json_version = f"{base}/versions/{version['version']}/{version['version']}.json"
    descargar_version(json_version, version, base)

    with open(json_version, "r", encoding="utf-8") as f:
        data = json.load(f)    
        construir_ejecutable(data,so,base,version,lanzador)