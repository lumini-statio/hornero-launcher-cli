import json
import os
from pathlib import Path

from src.descarga_versiones import buscar_y_descargar
from src.actualizar_data_versiones import actualizar_datos_versiones
import sys

from src.ejecutar_juego import elegir_y_jugar

so = sys.platform

if "linux" in so:
    base = Path("~/.var/app/com.mojang.Minecraft/data/minecraft").expanduser()
if "win32" in so:
    base = Path(os.environ["APPDATA"]) / ".minecraft"

data = "./data"

if __name__ == "__main__":
    while True:
        print("Elegir una de las opciones disponibles: ")
        print("="*50)
        print("1: Jugar")
        print("2: Descargar version")
        print("3: Actualizar datos de versiones globales")
        print("="*50)

        op = ""
        opciones = ("1","2","3")
        while op not in opciones:
            op = input("Elegir una de las opciones disponibles: ")

        match op:
            case "1":
                elegir_y_jugar(data, so, base)
            case "2":
                buscar_y_descargar(base, so)
                print("<*> Listo!\n\n")
            case "3":
                actualizar_datos_versiones(data)
                print("<*> Listo!\n\n")