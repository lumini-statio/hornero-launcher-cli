import json
import hashlib
from pathlib import Path
from urllib.request import urlopen, Request
import urllib.parse


def descargar_mod_menu(directorio_minecraft: str | Path, game_version: str) -> None:
    """
    Busca y descarga la versión compatible del mod 'Mod Menu' desde Modrinth
    para la versión de Minecraft dada, colocándolo en la carpeta 'mods'.
    """
    mc_dir = Path(directorio_minecraft).expanduser().resolve()
    mods_dir = mc_dir / "mods"
    mods_dir.mkdir(parents=True, exist_ok=True)

    # Verificar si ya existe algún Mod Menu para esta versión de Minecraft
    for archivo_existente in mods_dir.glob("modmenu*.jar"):
        # Si ya existe un jar de modmenu en la carpeta mods
        if game_version in archivo_existente.name:
            print(f"  [OK] Mod Menu ya presente: {archivo_existente.name}")
            return

    print(f"  [MOD MENU] Buscando Mod Menu para Minecraft {game_version} en Modrinth...")
    try:
        query = urllib.parse.urlencode({
            "loaders": json.dumps(["fabric"]),
            "game_versions": json.dumps([game_version])
        })
        api_url = f"https://api.modrinth.com/v2/project/modmenu/version?{query}"
        headers = {"User-Agent": "hornero-launcher-cli (https://github.com/lumini-statio/hornero-launcher-cli)"}
        req = Request(api_url, headers=headers)

        with urlopen(req, timeout=15) as resp:
            versiones = json.loads(resp.read().decode("utf-8"))

        if not versiones:
            print(f"  [AVISO] No se encontró una versión de Mod Menu compatible con {game_version} en Modrinth.")
            return

        version_data = versiones[0]
        archivos = version_data.get("files", [])
        if not archivos:
            return

        archivo_jar = next((f for f in archivos if f.get("primary")), archivos[0])
        dl_url = archivo_jar.get("url")
        filename = archivo_jar.get("filename") or f"modmenu-{game_version}.jar"
        dest_path = mods_dir / filename

        if dest_path.is_file():
            print(f"  [OK] Mod Menu ya existe: {filename}")
            return

        print(f"  [DESCARGANDO MOD] {filename}...")
        req_dl = Request(dl_url, headers=headers)
        with urlopen(req_dl, timeout=30) as dl_resp:
            contenido = dl_resp.read()

        with open(dest_path, "wb") as f_out:
            f_out.write(contenido)
        print(f"  [GUARDADO] Mod Menu colocado en -> {dest_path}")

    except Exception as e:
        print(f"  [FALLO] No se pudo descargar Mod Menu para {game_version}: {e}")


def instalar_librerias_todos_los_fabric(directorio_minecraft: str) -> None:
    """
    Escanea la carpeta 'versions' del directorio de Minecraft, detecta todos los
    perfiles de Fabric Loader, descarga sus librerías a 'libraries' y descarga
    el mod 'Mod Menu' compatible en la carpeta 'mods'.
    """
    mc_dir = Path(directorio_minecraft).expanduser().resolve()
    versions_dir = mc_dir / "versions"
    lib_base_dir = mc_dir / "libraries"

    if not versions_dir.is_dir():
        return

    # Buscar todas las carpetas dentro de 'versions' que comiencen con 'fabric-loader'
    perfiles_fabric = [d for d in versions_dir.iterdir() if d.is_dir() and d.name.startswith("fabric-loader")]

    if not perfiles_fabric:
        print("No se encontraron carpetas de Fabric Loader en el directorio de versiones.")
        return

    print(f"Se encontraron {len(perfiles_fabric)} perfil(es) de Fabric Loader.\n")

    for perfil_dir in perfiles_fabric:
        json_path = perfil_dir / f"{perfil_dir.name}.json"
        
        if not json_path.is_file():
            print(f"[OMITIDO] No se encontró el archivo JSON esperado: {json_path}")
            continue

        print(f"=== Procesando perfil: {perfil_dir.name} ===")

        with open(json_path, "r", encoding="utf-8") as f:
            datos_perfil = json.load(f)

        librerias = datos_perfil.get("libraries", [])
        
        for lib in librerias:
            nombre_maven = lib.get("name")
            url_base = lib.get("url", "https://maven.fabricmc.net/")

            if not nombre_maven:
                continue

            # Parsear notación Maven (groupId:artifactId:version)
            group, artifact, version = nombre_maven.split(":")
            group_path = group.replace(".", "/")
            jar_filename = f"{artifact}-{version}.jar"
            
            rel_path = Path(group_path) / artifact / version / jar_filename
            dest_path = lib_base_dir / rel_path
            download_url = f"{url_base.rstrip('/')}/{rel_path.as_posix()}"

            sha1_esperado = lib.get("sha1")

            # Comprobar si la librería ya existe y es válida
            if dest_path.is_file():
                if sha1_esperado:
                    with open(dest_path, "rb") as f_jar:
                        sha1_local = hashlib.sha1(f_jar.read()).hexdigest()
                    if sha1_local.lower() == sha1_esperado.lower():
                        print(f"  [OK] Válido: {jar_filename}")
                        continue
                else:
                    print(f"  [OK] Existe: {jar_filename}")
                    continue

            # Crear estructura de carpetas local
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"  [DESCARGANDO] {jar_filename}...")
            req = Request(download_url, headers={"User-Agent": "Mozilla/5.0"})

            try:
                with urlopen(req) as response:
                    contenido = response.read()

                if sha1_esperado:
                    sha1_descargado = hashlib.sha1(contenido).hexdigest()
                    if sha1_descargado.lower() != sha1_esperado.lower():
                        print(f"    [ERROR] Hash SHA-1 incorrecto para {jar_filename}.")
                        continue

                with open(dest_path, "wb") as out_file:
                    out_file.write(contenido)
                print(f"    [GUARDADO] -> {dest_path}")
            except Exception as e:
                print(f"    [FALLO] Error al descargar {jar_filename}: {e}")

        # Descargar Mod Menu correspondiente para esta versión de Minecraft
        version_juego = datos_perfil.get("inheritsFrom") or perfil_dir.name.split("-")[-1]
        descargar_mod_menu(mc_dir, version_juego)

        print()

if __name__ == "__main__":
    MINECRAFT_PATH = "~/.var/app/com.mojang.Minecraft/data/minecraft"
    instalar_librerias_todos_los_fabric(MINECRAFT_PATH)