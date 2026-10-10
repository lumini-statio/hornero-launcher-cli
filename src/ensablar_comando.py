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

    # Classpath (solo librerías que aplican al SO + client.jar)
    sep = ";" if os_name == "windows" else ":"
    libs = [str(Path(libraries_dir) / l["downloads"]["artifact"]["path"])
            for l in data["libraries"]
            if permitido(l.get("rules"), **ctx) and "artifact" in l.get("downloads", {})]
    classpath = sep.join(libs + [str(client_jar)])

    vars_ = {
        "auth_player_name": username, "version_name": data["id"],
        "game_directory": str(game_dir), "assets_root": str(assets_dir),
        "assets_index_name": data["assetIndex"]["id"],
        "auth_uuid": uuid, "auth_access_token": access_token,
        "clientid": "", "auth_xuid": "", "version_type": data["type"],
        "natives_directory": str(natives_dir), "launcher_name": launcher_name,
        "launcher_version": launcher_version, "classpath": classpath,
        "path": "",  # ruta del log4j xml si lo descargaste
    }

    args = data["arguments"]
    jvm_usuario = _expandir(args.get("default-user-jvm", []), ctx, vars_) \
        if incluir_default_user_jvm else []
    jvm = _expandir(args["jvm"], ctx, vars_)
    game = _limpiar_vacios(_expandir(args["game"], ctx, vars_))

    if java_path is None:
        java_path = "java.exe" if os_name == "windows" else "java"

    return [java_path, *jvm_usuario, *jvm, data["mainClass"], *game]


def construir_ejecutable(data, so, base, version, lanzador):
    cmd = construir_comando(
        data, so,
        game_dir=base, libraries_dir=base / "libraries",
        assets_dir=base / "assets", natives_dir=base / "natives",
        client_jar=base / f"versions/{version['version']}/{version['version']}.jar",
        os_version="10.0.19045" if so == "win32" else "",
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