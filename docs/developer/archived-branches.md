# Archived branches

_Last updated: 2026-10-16. See also [remaining-branches.md](remaining-branches.md) for branches not yet reviewed._

Old branches are removed from the repository to keep the branch list manageable. Before a branch is deleted, a
**tag with the same name** is created at its last commit, so nothing is lost and existing links keep working.

## Restoring an archived branch

```bash
git fetch --tags
git checkout -b <name> <name>        # work on it again as a normal branch
git push origin <name>               # optional: put the branch back on GitHub
```

Links of the form `https://github.com/architecture-building-systems/CityEnergyAnalyst/tree/<name>` and
`git clone -b <name>` also resolve to the tag, but leave you in a detached HEAD.

If you have an old local branch with the same name as a tag, Git warns that the name is ambiguous. Delete the local
branch (`git branch -D <name>`) or use the full ref (`refs/heads/<name>` / `refs/tags/<name>`).

## Archived (branch deleted, tag kept)

| Tag | Last commit | Last author | Commits ahead of master at archive time |
|---|---|---|---|
| `sg-sle-database` | 2024-02-29 | Reynold Mok | 6 |
| `release-4.0` | 2025-06-10 | Zhongming Shi | 0 (fully merged) |
| `CEA-for-DUCT` | 2024-09-11 | Mathias Niffeler | 385 |
| `CEA-for-DUCT-EnEff-module` | 2024-08-20 | Yi-Kai Tsai | 37 |
| `CEA-for-DUCT-DC-module` | 2024-10-08 | Mathias Niffeler | 113 |
| `microclimate_study_2020` | 2020-08-12 | Martín Mosteiro Romero | 109 |
| `microclimate_study` | 2020-08-12 | Martín Mosteiro Romero | 109 (same commit as `microclimate_study_2020`) |
| `microclimate_paper_2020` | 2020-08-12 | Martín Mosteiro Romero | 178 |
| `microclimate_master_2021` | 2021-03-16 | Martín Mosteiro Romero | 112 |
| `muses-cisbat-2019` | 2019-04-23 | Bhargava Krishna Sreepathi | 4 |

## Tagged, branch still present

These have a tag but the branch has not been deleted because their status is unknown.

| Tag | Last commit | Last author |
|---|---|---|
| `CEA-Borlange` | 2024-04-04 | Jimeno A. Fonseca |
| `CEA-Superurbana` | 2024-04-04 | Jimeno A. Fonseca |
| `CEA-Zurich-2024` | 2024-04-04 | Jimeno A. Fonseca |
| `CEA-pro-zurich-2024` | 2024-10-02 | Jimeno A. Fonseca |

`CEA-Borlange`, `CEA-Superurbana` and `CEA-Zurich-2024` point at the same commit.
