import json
import os

import requests


def actualizar_datos_versiones(versiones_path):
    manifest = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    res: requests.Response = requests.get(manifest)
    res.raise_for_status()
    res = res.json()

    json_versiones = f"{versiones_path}/versiones.json" 

    with open(json_versiones, "r+") as f:
        if res != json.load(f): 
            f.seek(0)
            json.dump(res, f, indent=2)
            f.truncate()
        else: print("Nada para actualizar")
        
        f.close()