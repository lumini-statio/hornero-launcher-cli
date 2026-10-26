from pathlib import Path
import shlex
import subprocess


def listar(base):
    versions_path = Path(base) / "versions"
    versiones = {}

    print("\nVersiones Descargadas:\n")
    if not versions_path.exists():
        print("No se encontró la carpeta de versiones.\n")
        return versiones

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
    if not versiones:
        print("No hay versiones disponibles para jugar.\n")
        return

    opt = input("Elegir version indicando su id: ")
    while opt not in versiones.keys():
        opt = input("Version no encontrada, elija una de las versiones listadas: ")

    version_elegida = versiones[opt]
    lanzador = Path(data) / (f"lanzador_{version_elegida}.bat" if so == "win32" else f"lanzador_{version_elegida}")
    if not lanzador.exists() and (Path(data) / version_elegida).exists():
        lanzador = Path(data) / version_elegida

    if so == "win32":
        subprocess.run(str(lanzador), shell=True, check=True)
    elif "linux" in so:
        subprocess.run(["bash", str(lanzador)], check=True)
    else:
        raise OSError("Sistema operativo no compatible")