"""
ExaMLOps Model Zoo client.

Provides a simple API to load models and metadata from the Git-backed model catalog.
Version IDs match MLflow Model Registry (v1, v2, v3, ...).
"""

from pathlib import Path

MODELZOO_ROOT = Path(__file__).resolve().parent / "models"


def get_model_dir(model_name: str, version: int | str = "latest") -> Path:
    """
    Return the directory path for a model version.

    Args:
        model_name: e.g. "uc_power_model"
        version: Integer version or "latest" to use latest from index.yaml

    Returns:
        Path to the version directory (e.g. modelzoo/models/uc_power_model/v2/)
    """
    import yaml

    model_root = MODELZOO_ROOT / model_name
    model_root = model_root.resolve()

    if isinstance(version, str) and version == "latest":
        index_path = model_root / "index.yaml"
        if not index_path.exists():
            raise FileNotFoundError(f"No index.yaml at {index_path}")
        with index_path.open() as f:
            index = yaml.safe_load(f)
        version = index["latest"]["version"]

    return model_root / f"v{version}"


def load_model_metadata(model_name: str, version: int | str = "latest") -> dict:
    """Load metadata.yaml for a model version."""
    import yaml

    model_dir = get_model_dir(model_name, version)
    meta_path = model_dir / "metadata.yaml"
    if not meta_path.exists():
        raise FileNotFoundError(f"No metadata.yaml at {meta_path}")
    with meta_path.open() as f:
        return yaml.safe_load(f)


def get_model_path(model_name: str, version: int | str = "latest") -> Path:
    """Return the path to the model artifact (model.pkl)."""
    model_dir = get_model_dir(model_name, version)
    return model_dir / "model.pkl"
