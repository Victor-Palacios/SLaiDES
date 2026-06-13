# CI definitions

## `verify.yml` — Phase 6 render-drift harness (CI only)

This is the GitHub Actions workflow for the Phase 6 verification harness: it
renders the example decks through LibreOffice + poppler and runs cheap pixel
heuristics against the geometry the layout engine computed, catching drift
between our math and a real renderer. It is **not** part of deck generation.

### Why it lives here instead of `.github/workflows/`

The project is built by an unattended nightly GitHub App bot whose token does not
carry the `workflows` permission, so it cannot create or update files under
`.github/workflows/`. The workflow is therefore committed here, ready to install.

### Install (one-time, by an operator)

```bash
cp ci/verify.yml .github/workflows/verify.yml
git add .github/workflows/verify.yml
git commit -m "ci: install render-drift verification workflow"
git push
```

Once installed it triggers on pushes/PRs that touch `src/slidekit/layout`,
`src/slidekit/metrics`, `src/slidekit/emit`, `src/slidekit/verify`, `examples/`,
or `pyproject.toml`.

### Run locally

```bash
sudo apt-get install -y libreoffice-impress poppler-utils
pip install -e ".[dev]"
pytest tests/test_verify -q          # full harness over every example deck
slidekit verify examples/*.yaml      # ad-hoc JSON report, exit 1 on drift
```
