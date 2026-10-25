from pathlib import Path
import shlex
import subprocess


def listar(base):
    versions_path = Path(base) / "versions"
    versiones = {}

    print("\nVersiones Descargadas:\n")
    i = 1
    for archivo in versions_path.iterdir():
        if archivo.is_file():
            continue
        
        print(f"id: {i} - version: {archivo.name}")
        versiones[f"{i}"] = archivo.name
        i += 1
    print("\n")
    return versiones

def elegir_y_jugar(data, so, base):
    versiones = listar(base)

    opt = input("Elegir version indicando su id: ")
    while opt not in versiones.keys():
        opt = input("vVersion no encontrada, elija una de las versiones listadas: ")

    if so == "win32":
        subprocess.run(f"data/{versiones[opt]}", shell=True, check=True)
    elif "linux" in so:
        subprocess.run(["bash", f"data/{versiones[opt]}"], check=True)
    else:
        raise OSError("Sistema operativo no compatible")