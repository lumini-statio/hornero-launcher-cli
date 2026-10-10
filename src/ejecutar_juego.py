from pathlib import Path
import shlex
import subprocess


def listar(data):
    data_path = Path(data)
    versiones = {}

    print("\nVersiones Descargadas:\n")
    i = 1
    for archivo in data_path.iterdir():
        if not archivo.is_file():
            continue
        if archivo.name.split(".")[1] == "json":
            continue
        
        print(f"id: {i} - version: {archivo.name.split("_")[1]}")
        versiones[f"{i}"] = archivo.name
        i += 1
    print("\n")
    return versiones

def elegir_y_jugar(data, so):
    versiones = listar(data)

    opt = input("Elegir version indicando su id: ")
    while opt not in versiones.keys():
        opt = input("vVersion no encontrada, elija una de las versiones listadas: ")

    if so == "win32":
        subprocess.run(f"data/{versiones[opt]}", shell=True, check=True)
    elif "linux" in so:
        subprocess.run(["bash", f"data/{versiones[opt]}"], check=True)
    else:
        raise OSError("Sistema operativo no compatible")