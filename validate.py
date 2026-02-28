#!/usr/bin/env python3
"""
Validate modelzoo structure and schemas.

Run from ModelZoo repo root:
  python validate.py
  python validate.py --strict  # also load model.pkl with joblib

Exit 0 if valid, 1 if invalid. Used by CI (GitHub Actions).
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. pip install pyyaml")
    sys.exit(1)

# Required fields for metadata.yaml
METADATA_REQUIRED = {"model_name", "version", "mlflow", "git", "status", "metrics", "features"}
MLFLOW_REQUIRED = {"registered_model_name", "model_version", "run_id"}
GIT_REQUIRED = {"created_at"}
METADATA_STATUS_VALID = {"staging", "production", "archived", "none"}
INDEX_REQUIRED = {"model_name", "versions", "latest"}
FEATURE_SCHEMA_REQUIRED = {"features", "target"}


def validate_metadata(path: Path) -> list[str]:
    """Validate metadata.yaml. Returns list of error messages."""
    errors = []
    try:
        with path.open() as f:
            meta = yaml.safe_load(f)
    except Exception as e:
        return [f"Could not parse {path}: {e}"]

    if not isinstance(meta, dict):
        return [f"{path}: root must be a mapping"]

    missing = METADATA_REQUIRED - set(meta.keys())
    if missing:
        errors.append(f"{path}: missing required keys: {sorted(missing)}")

    if "version" in meta and not isinstance(meta["version"], (int, float)):
        errors.append(f"{path}: version must be numeric, got {type(meta['version'])}")

    if "mlflow" in meta:
        mlf = meta["mlflow"]
        if not isinstance(mlf, dict):
            errors.append(f"{path}: mlflow must be a mapping")
        else:
            missing_mlf = MLFLOW_REQUIRED - set(mlf.keys())
            if missing_mlf:
                errors.append(f"{path}: mlflow missing: {sorted(missing_mlf)}")
            if "model_version" in mlf and "version" in meta:
                if int(mlf.get("model_version", 0)) != int(meta["version"]):
                    errors.append(
                        f"{path}: mlflow.model_version ({mlf.get('model_version')}) "
                        f"!= version ({meta['version']})"
                    )

    if "git" in meta:
        g = meta["git"]
        if not isinstance(g, dict):
            errors.append(f"{path}: git must be a mapping")
        elif "created_at" not in g:
            errors.append(f"{path}: git.created_at required")

    if "status" in meta:
        s = str(meta["status"]).lower()
        if s not in METADATA_STATUS_VALID:
            errors.append(f"{path}: status must be one of {METADATA_STATUS_VALID}, got '{meta['status']}'")

    if "features" in meta:
        f = meta["features"]
        if not isinstance(f, list):
            errors.append(f"{path}: features must be a list")
        elif f and not all(isinstance(x, str) for x in f):
            errors.append(f"{path}: features must be list of strings")

    return errors


def validate_feature_schema(path: Path) -> list[str]:
    """Validate feature_schema.json."""
    errors = []
    try:
        with path.open() as f:
            schema = json.load(f)
    except Exception as e:
        return [f"Could not parse {path}: {e}"]

    if not isinstance(schema, dict):
        return [f"{path}: root must be an object"]

    missing = FEATURE_SCHEMA_REQUIRED - set(schema.keys())
    if missing:
        errors.append(f"{path}: missing required keys: {sorted(missing)}")

    if "features" in schema and not isinstance(schema["features"], list):
        errors.append(f"{path}: features must be a list")

    return errors


def validate_index(path: Path, model_root: Path) -> list[str]:
    """Validate index.yaml and consistency with version dirs."""
    errors = []
    try:
        with path.open() as f:
            index = yaml.safe_load(f)
    except Exception as e:
        return [f"Could not parse {path}: {e}"]

    if not isinstance(index, dict):
        return [f"{path}: root must be a mapping"]

    missing = INDEX_REQUIRED - set(index.keys())
    if missing:
        errors.append(f"{path}: missing required keys: {sorted(missing)}")

    versions = index.get("versions", [])
    if not isinstance(versions, list):
        errors.append(f"{path}: versions must be a list")
    else:
        for i, v in enumerate(versions):
            if not isinstance(v, dict):
                errors.append(f"{path}: versions[{i}] must be a mapping")
            elif "version" not in v:
                errors.append(f"{path}: versions[{i}] missing 'version'")
            else:
                ver_dir = model_root / f"v{v['version']}"
                if not ver_dir.is_dir():
                    errors.append(f"{path}: version {v['version']} missing dir {ver_dir}")

    latest = index.get("latest", {})
    if isinstance(latest, dict) and "version" in latest:
        lv = latest["version"]
        ver_dir = model_root / f"v{lv}"
        if not ver_dir.is_dir():
            errors.append(f"{path}: latest.version={lv} but dir {ver_dir} missing")

    return errors


def validate_model_load(path: Path) -> list[str]:
    """Optionally validate model.pkl loads with joblib."""
    errors = []
    try:
        import joblib
        joblib.load(path)
    except ImportError:
        errors.append("joblib not installed, cannot validate model load")
    except Exception as e:
        errors.append(f"{path}: failed to load model: {e}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate modelzoo structure")
    ap.add_argument("--strict", action="store_true", help="Also load model.pkl (requires joblib)")
    ap.add_argument("--root", type=Path, default=Path.cwd(), help="Modelzoo repo root (default: cwd)")
    args = ap.parse_args()
    root = args.root.resolve()

    models_dir = root / "models"
    if not models_dir.is_dir():
        print("ERROR: models/ directory not found")
        return 1

    all_errors: list[str] = []

    for model_dir in models_dir.iterdir():
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        index_path = model_dir / "index.yaml"
        if not index_path.exists():
            all_errors.append(f"{model_dir.name}: missing index.yaml")
            continue

        all_errors.extend(validate_index(index_path, model_dir))

        for v_dir in sorted(model_dir.iterdir()):
            if not v_dir.is_dir() or not v_dir.name.startswith("v"):
                continue
            meta_path = v_dir / "metadata.yaml"
            schema_path = v_dir / "feature_schema.json"
            model_path = v_dir / "model.pkl"

            if not meta_path.exists():
                all_errors.append(f"{v_dir}: missing metadata.yaml")
            else:
                all_errors.extend(validate_metadata(meta_path))

            if not schema_path.exists():
                all_errors.append(f"{v_dir}: missing feature_schema.json")
            else:
                all_errors.extend(validate_feature_schema(schema_path))

            if not model_path.exists():
                all_errors.append(f"{v_dir}: missing model.pkl")
            elif args.strict:
                all_errors.extend(validate_model_load(model_path))

    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}")
        return 1
    print("OK: modelzoo validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
