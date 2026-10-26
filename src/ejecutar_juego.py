from pathlib import Path
import shlex
import subprocess


def listar(mc_path, solo_fabric=False):
    versions_path = Path(mc_path) / "versions"
    versiones = {}

    titulo = "Versiones de Fabric (con mods) disponibles:" if solo_fabric else "Versiones descargadas:"
    print(f"\n{titulo}\n")
    if not versions_path.exists():
        print("No se encontró la carpeta de versiones.\n")
        return versiones

    i = 1
    for archivo in sorted(versions_path.iterdir()):
        if archivo.is_file():
            continue
        
        es_fabric = "fabric" in archivo.name.lower()
        if solo_fabric and not es_fabric:
            continue
        if not solo_fabric and es_fabric:
            continue

        tag = " [Fabric / Mods]" if es_fabric else ""
        print(f"id: {i} - version: {archivo.name}{tag}")
        versiones[f"{i}"] = archivo.name
        i += 1
    print("\n")
    return versiones

def elegir_y_jugar(data, so, mc_path, solo_fabric=False):
    if solo_fabric:
        mods_path = Path(mc_path) / "mods"
        mods_path.mkdir(parents=True, exist_ok=True)
        print(f"[*] Directorio de mods: {mods_path}")

    versiones = listar(mc_path, solo_fabric=solo_fabric)
    if not versiones:
        if solo_fabric:
            print("No se encontraron versiones de Fabric instaladas.\n")
        else:
            print("No hay versiones disponibles para jugar.\n")
        return

    opt = input("Elegir version indicando su id: ")
    while opt not in versiones.keys():
        opt = input("Version no encontrada, elija una de las versiones listadas: ")

    version_elegida = versiones[opt]
    lanzador = Path(data) / (f"lanzador_{version_elegida}.bat" if so == "win32" else f"lanzador_{version_elegida}")
    if not lanzador.exists() and (Path(data) / version_elegida).exists():
        lanzador = Path(data) / version_elegida

    # Si aún no existe el lanzador, intentar crearlo
    if not lanzador.exists():
        json_version = Path(mc_path) / "versions" / version_elegida / f"{version_elegida}.json"
        if json_version.exists():
            print(f"Creando ejecutable para {version_elegida}...")
            import json
            from src.ensamblar_comando import construir_ejecutable
            with open(json_version, "r", encoding="utf-8") as f:
                v_data = json.load(f)
            lanzador_base = str(Path(data) / f"lanzador_{version_elegida}")
            construir_ejecutable(v_data, so, mc_path, {"version": version_elegida}, lanzador_base)

    if not lanzador.exists():
        print(f"Error: No se encontró el ejecutable {lanzador.name}.\n")
        return

    if solo_fabric or "fabric" in version_elegida.lower():
        from src.descargar_librerías import descargar_mod_menu
        json_version = Path(mc_path) / "versions" / version_elegida / f"{version_elegida}.json"
        game_ver = ""
        if json_version.exists():
            import json
            try:
                with open(json_version, "r", encoding="utf-8") as f:
                    game_ver = json.load(f).get("inheritsFrom", "")
            except Exception:
                pass
        if not game_ver:
            game_ver = version_elegida.split("-")[-1]
        descargar_mod_menu(mc_path, game_ver)

    if so == "win32":
        subprocess.run(str(lanzador), shell=True, check=True)
    elif "linux" in so:
        subprocess.run(["bash", str(lanzador)], check=True)
    else:
        raise OSError("Sistema operativo no compatible")