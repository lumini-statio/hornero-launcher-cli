import json
import re
import shlex
import stat
import subprocess
import sys
from pathlib import Path


# ---------- Reglas ----------

def _ver(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))

def _os_coincide(r_os, os_name, os_arch, os_version):
    if "name" in r_os and r_os["name"] != os_name:
        return False
    if "arch" in r_os and r_os["arch"] != os_arch:
        return False
    if "version" in r_os and not re.search(r_os["version"], os_version):
        return False
    if "versionRange" in r_os:          # extensión de tu manifiesto
        rng = r_os["versionRange"]
        v = _ver(os_version or "0")
        if "min" in rng and v < _ver(rng["min"]):
            return False
        if "max" in rng and v >= _ver(rng["max"]):   # max exclusivo
            return False
    return True

def permitido(rules, os_name, os_arch, os_version, features):
    if not rules:
        return True
    ok = False
    for r in rules:
        coincide = True
        if "os" in r:
            coincide = _os_coincide(r["os"], os_name, os_arch, os_version)
        if coincide and "features" in r:
            coincide = all(features.get(k, False) == v for k, v in r["features"].items())
        if coincide:
            ok = (r["action"] == "allow")
    return ok

# ---------- Argumentos ----------

def _expandir(lista, ctx, vars_):
    """Filtra por reglas, aplana valores y sustituye ${variables}."""
    out = []
    for e in lista:
        if isinstance(e, str):
            valores = [e]
        elif permitido(e.get("rules"), **ctx):
            v = e["value"]
            valores = [v] if isinstance(v, str) else v
        else:
            continue
        out += [re.sub(r"\$\{(\w+)\}", lambda m: str(vars_.get(m.group(1), "")), x)
                for x in valores]
    return out

def _limpiar_vacios(args):
    """Quita pares '--flag valor' cuando el valor quedó vacío (ej: --xuid, --clientId)."""
    res, i = [], 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args) and args[i + 1] == "":
            i += 2
            continue
        res.append(args[i])
        i += 1
    return res

# ---------- Comando completo ----------

def construir_comando(data, os_name, *, game_dir, libraries_dir, assets_dir,
                      natives_dir, client_jar, username="Player",
                      uuid="00000000-0000-0000-0000-000000000000",
                      access_token="0", java_path=None, os_arch="x86_64",
                      os_version="", features=None, incluir_default_user_jvm=True,
                      launcher_name="mi-launcher", launcher_version="1.0"):
    """
    os_name: 'linux' | 'windows' | 'osx'
    Devuelve la lista de argumentos lista para subprocess.run().
    """
    features = features or {}
    ctx = dict(os_name=os_name, os_arch=os_arch,
               os_version=os_version, features=features)

    # Classpath (librerías que aplican al SO + librerías Maven de Fabric + client.jar)
    sep = ";" if os_name == "windows" else ":"
    libs = []
    for l in data["libraries"]:
        if not permitido(l.get("rules"), **ctx):
            continue
        if "downloads" in l and "artifact" in l["downloads"]:
            libs.append(str(Path(libraries_dir) / l["downloads"]["artifact"]["path"]))
        elif "name" in l:
            # Formato Maven (ej: librerías de Fabric Loader / Intermediary / Mixin)
            partes = l["name"].split(":")
            if len(partes) >= 3:
                group, artifact, version = partes[0], partes[1], partes[2]
                classifier = f"-{partes[3]}" if len(partes) >= 4 else ""
                group_path = group.replace(".", "/")
                jar_name = f"{artifact}-{version}{classifier}.jar"
                p = Path(libraries_dir) / group_path / artifact / version / jar_name
                libs.append(str(p))

    classpath = sep.join(libs + [str(client_jar)])

    asset_index = data.get("assetIndex", {})
    asset_index_id = asset_index.get("id", "") if isinstance(asset_index, dict) else ""

    vars_ = {
        "auth_player_name": username, "version_name": data.get("id", ""),
        "game_directory": str(game_dir), "assets_root": str(assets_dir),
        "assets_index_name": asset_index_id,
        "auth_uuid": uuid, "auth_access_token": access_token,
        "clientid": "", "auth_xuid": "", "version_type": data.get("type", "release"),
        "natives_directory": str(natives_dir), "launcher_name": launcher_name,
        "launcher_version": launcher_version, "classpath": classpath,
        "path": "",  # ruta del log4j xml si lo descargaste
    }

    args = data.get("arguments", {})
    jvm_usuario = _expandir(args.get("default-user-jvm", []), ctx, vars_) \
        if incluir_default_user_jvm else []
    jvm = _expandir(args.get("jvm", []), ctx, vars_)
    game = _limpiar_vacios(_expandir(args.get("game", []), ctx, vars_))

    tiene_cp = any(arg in ("-cp", "-classpath", "--class-path") for arg in jvm)
    if not tiene_cp:
        jvm = [*jvm, "-cp", classpath]

    if java_path is None:
        java_path = "java.exe" if os_name == "windows" else "java"

    return [java_path, *jvm_usuario, *jvm, data["mainClass"], *game]


def construir_ejecutable(data, so, mc_path_str, version, lanzador):
    version_id = version["version"] if isinstance(version, dict) else str(version)
    mc_path = Path(mc_path_str)
    os_name = "windows" if "win32" in so else ("osx" if "darwin" in so else "linux")

    # Si es un perfil que hereda de una versión base (como Fabric)
    if "inheritsFrom" in data:
        inherits_from = data["inheritsFrom"]
        parent_json_path = mc_path / "versions" / inherits_from / f"{inherits_from}.json"
        if parent_json_path.exists():
            with open(parent_json_path, "r", encoding="utf-8") as f:
                parent_data = json.load(f)

            # Combinar datos de la versión base con los de Fabric
            merged_data = dict(parent_data)
            merged_data["id"] = data.get("id", version_id)
            if "mainClass" in data:
                merged_data["mainClass"] = data["mainClass"]
            if "type" in data:
                merged_data["type"] = data["type"]

            merged_data["libraries"] = list(parent_data.get("libraries", [])) + list(data.get("libraries", []))

            parent_args = parent_data.get("arguments", {})
            child_args = data.get("arguments", {})
            merged_args = {
                "jvm": list(parent_args.get("jvm", [])) + list(child_args.get("jvm", [])),
                "game": list(parent_args.get("game", [])) + list(child_args.get("game", [])),
                "default-user-jvm": list(parent_args.get("default-user-jvm", [])) + list(child_args.get("default-user-jvm", []))
            }
            merged_data["arguments"] = merged_args
            data = merged_data

        client_jar = mc_path / f"versions/{inherits_from}/{inherits_from}.jar"
    else:
        client_jar = mc_path / f"versions/{version_id}/{version_id}.jar"

    cmd = construir_comando(
        data, os_name,
        game_dir=mc_path, libraries_dir=mc_path / "libraries",
        assets_dir=mc_path / "assets", natives_dir=mc_path / "natives",
        client_jar=client_jar,
        os_version="10.0.19045" if "win32" in so else "",
        )
    
    print(f"\n=== {so} ===")
    if "win32" in so:
        with open(f"{lanzador}.bat", "w", encoding="utf-8") as f:
            f.write(subprocess.list2cmdline(cmd))
    else:
        import os
        with open(lanzador, "w", encoding="utf-8") as f:
            f.write(shlex.join(cmd))

        os.chmod(lanzador, os.stat(lanzador).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)