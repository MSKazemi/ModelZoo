# ExaMLOps Model Zoo

Git-backed model catalog with **MLflow Model Registry version** as the canonical version ID.

## Layout

```
modelzoo/
  models/
    <model_name>/
      v1/
        model.pkl
        metadata.yaml
        feature_schema.json
      v2/
        ...
      index.yaml    # summary of all versions for this model
  modelzoo_client.py
  README.md
```

- **Version directories are immutable**: once `vN/` is created, it is never modified.
- **Version ID** matches MLflow Model Registry (`uc_power_model` version 2 → `v2/`).

## Dependencies

`modelzoo_client.py` requires `pyyaml`. Install with: `pip install pyyaml`

## Usage

From the repo root (so `modelzoo` is importable):

```python
from modelzoo.modelzoo_client import get_model_path, load_model_metadata

# Latest production model
model_path = get_model_path("uc_power_model", version="latest")
metadata = load_model_metadata("uc_power_model", version="latest")

# Specific version
model_path = get_model_path("uc_power_model", version=2)
```

## Validation & CI

Run schema validation locally:

```bash
python validate.py          # metadata, feature_schema, index
python validate.py --strict # also load model.pkl with joblib
```

**GitHub Actions** (`.github/workflows/validate-modelzoo.yml`) runs on every push/PR: validates metadata schema, feature_schema.json, index.yaml consistency, and optionally model load.

## Populated by MLOps Pipeline

The `push_to_modelzoo` Prefect task (in `flow_uc_power_training`) creates new version directories after each successful training run. Only the pipeline is allowed to write to the modelzoo.

**Separate repo:** The pipeline can push the modelzoo to a dedicated GitHub repo (Option B). Set `EXAMLOPS_MODELZOO_REPO_URL=git@github.com:user/ModelZoo.git` and `EXAMLOPS_PUSH_MODELZOO_TO_GIT=1`, then run `make pipeline-push`. See [UC Power Prediction docs](../docs/40-pipelines/uc-power-prediction.md).
