# Comparar ejecutables existentes en data con las versiones en base/versions
import json
from pathlib import Path
from ensablar_comando import construir_ejecutable


def construct(data, base, so):
    data_path = Path(data)
    data_path.mkdir(exist_ok=True)
    versions_path = Path(base) / "versions"

    # Obtener versiones que ya tienen ejecutable en data
    ejecutables_existentes = set()
    for archivo in data_path.iterdir():
        if archivo.is_file() and archivo.name.startswith("lanzador_"):
            nombre = archivo.name[len("lanzador_"):]
            if nombre.endswith(".bat"):
                nombre = nombre[:-4]
            ejecutables_existentes.add(nombre)

    # Comparar y construir ejecutables para las versiones que no tengan uno
    if versions_path.exists():
        for version_dir in versions_path.iterdir():
            if not version_dir.is_dir():
                continue

            version_id = version_dir.name
            if version_id not in ejecutables_existentes:
                json_version = version_dir / f"{version_id}.json"

                if not json_version.exists():
                    manifest_path = data_path / "versiones.json"
                    if manifest_path.exists():
                        try:
                            import requests
                            with open(manifest_path, "r", encoding="utf-8") as mf:
                                manifest_data = json.load(mf)
                            for v in manifest_data.get("versions", []):
                                if v.get("id") == version_id and "url" in v:
                                    print(f"Descargando metadatos para {version_id}...")
                                    res = requests.get(v["url"], timeout=15)
                                    res.raise_for_status()
                                    with open(json_version, "w", encoding="utf-8") as f:
                                        json.dump(res.json(), f, indent=2, ensure_ascii=False)
                                    break
                        except Exception as e:
                            print(f"No se pudo descargar metadatos para {version_id}: {e}")

                if json_version.exists():
                    print(f"Creando ejecutable para la versión {version_id}...")
                    try:
                        with open(json_version, "r", encoding="utf-8") as f:
                            version_data = json.load(f)

                        lanzador = str(data_path / f"lanzador_{version_id}")
                        construir_ejecutable(version_data, so, base, {"version": version_id}, lanzador)
                        print(f"<*> Ejecutable creado para {version_id}\n")
                    except Exception as e:
                        print(f"Error al crear ejecutable para {version_id}: {e}\n")
                else:
                    print(f"No se encontró el archivo JSON para la versión {version_id}\n")
