# ModelZoo Architecture & Data Flow

## Overview

ModelZoo content lives in three places. This doc clarifies how they relate.

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ExaMLOps repo (main project)                                            │
│                                                                         │
│   modelzoo/                    ← SOURCE (written by pipeline)           │
│   ├── models/                                                           │
│   │   └── uc_power_model/v1, v2, ...                                    │
│   ├── modelzoo_client.py                                                │
│   ├── validate.py                                                       │
│   ├── .github/workflows/                                                │
│   └── .gitlab-ci.yml                                                    │
└─────────────────────────────────────────────────────────────────────────┘
           │
           │  commit_and_push_modelzoo (when EXAMLOPS_PUSH_MODELZOO_TO_GIT=1)
           │  1. Clone GitHub ModelZoo → .modelzoo_push/ (temp, gitignored)
           │  2. Sync modelzoo/* into clone
           │  3. Commit, push to origin (GitHub)
           │  4. Push to gitlab remote (if EXAMLOPS_MODELZOO_REPO_URL_GITLAB)
           ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│ GitHub: MSKazemi/ModelZoo     │    │ GitLab: ExaMLOps/modelzoo    │
│ (primary mirror)              │    │ (optional mirror)            │
│                               │    │                              │
│ Same structure: models/,      │    │ Same content; CI runs        │
│ validate.py, CI configs       │    │ .gitlab-ci.yml on push       │
└──────────────────────────────┘    └──────────────────────────────┘
```

## Directory Roles

| Location | Role |
|----------|------|
| `ExaMLOps/modelzoo/` | **Source of truth** – updated by `push_to_modelzoo` after each training run |
| `ExaMLOps/.modelzoo_push/` | Temp clone of GitHub ModelZoo; used for sync + push; **gitignored** |
| `github.com/MSKazemi/ModelZoo` | **Primary published mirror** – clone source, first push target |
| `gitlab.com/ExaMLOps/modelzoo` | **Optional mirror** – second push target when `EXAMLOPS_MODELZOO_REPO_URL_GITLAB` is set |

## Pipeline Flow

1. **Training** → model saved to mock_hpc_jobs or Slurm output
2. **push_to_modelzoo** → writes to `ExaMLOps/modelzoo/models/<model>/vN/`
3. **commit_and_push_modelzoo** (if push enabled):
   - Clones GitHub ModelZoo into `.modelzoo_push/`
   - Syncs `modelzoo/*` into clone
   - Commits, pushes to GitHub
   - Optionally pushes same commit to GitLab (warns if auth fails; pipeline still succeeds)

## GitLab Push: Permission Denied

If you see `Permission denied (publickey)` when pushing to GitLab:

1. **Add SSH key to GitLab**: GitLab → Settings → SSH Keys (add the same key you use for GitHub, or a GitLab-specific one)
2. **Or use HTTPS**: `EXAMLOPS_MODELZOO_REPO_URL_GITLAB=https://gitlab.com/ExaMLOps/modelzoo.git` (requires token in URL or credential helper)

The pipeline now treats GitLab push failure as **non-fatal**: GitHub push succeeds, and you get a warning to fix GitLab auth.
