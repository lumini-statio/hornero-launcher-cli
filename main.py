import json
import os
from pathlib import Path
import sys

from src.descarga_versiones import buscar_y_descargar
from src.actualizar_data_versiones import actualizar_datos_versiones
from src.ejecutar_juego import elegir_y_jugar
from src.ensamblar_comando import construir_ejecutable
from src.construir_ejecutables_faltantes import construct
from src.descargar_librerías import instalar_librerias_todos_los_fabric

so = sys.platform

if "linux" in so:
    mc_txt = Path("./data/mc_path.txt")
    if not mc_txt.exists():
        mc_path = input("ingrese la dirección de su carpeta de minecraft: ")
        with open(mc_txt, "w", encoding="utf-8") as f:
            f.write(mc_path)
        mc_path = Path(mc_path).expanduser()
    else:
        with open(mc_txt, "r", encoding="utf-8") as f:
            mc_path = f.readline().strip()
            mc_path = Path(mc_path).expanduser()
if "win32" in so:
    mc_path = Path(os.environ["APPDATA"]) / ".minecraft"

data = "./data"

if __name__ == "__main__":
    instalar_librerias_todos_los_fabric(mc_path)
    construct(data, mc_path, so)


    while True:
        print("Elegir una de las opciones disponibles: ")
        print("="*50)
        print("1: Jugar Vanilla")
        print("2: Jugar con Fabric (Mods)")
        print("3: Descargar version")
        print("4: Actualizar datos de versiones globales")
        print("="*50)

        op = ""
        opciones = ("1", "2", "3", "4")
        while op not in opciones:
            op = input("Elegir una de las opciones disponibles: ")

        match op:
            case "1":
                elegir_y_jugar(data, so, mc_path, solo_fabric=False)
            case "2":
                elegir_y_jugar(data, so, mc_path, solo_fabric=True)
            case "3":
                buscar_y_descargar(mc_path, so)
                print("<*> Listo!\n\n")
            case "4":
                actualizar_datos_versiones(data)
                print("<*> Listo!\n\n")