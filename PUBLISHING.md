# Publishing Guide

This guide explains how to publish the `fiftyone-skills` package to PyPI.

## Prerequisites

- uv package manager installed
- PyPI account with API token
- Appropriate repository permissions

## Build the Package

```bash
# Clean previous builds
rm -rf dist/

# Build using uv
uv build
```

This creates:
- `dist/fiftyone_skills-VERSION.tar.gz` (source distribution)
- `dist/fiftyone_skills-VERSION-py3-none-any.whl` (wheel)

## Verify the Build

```bash
# Check wheel contents
unzip -l dist/fiftyone_skills-*.whl

# Verify skills are included
unzip -l dist/fiftyone_skills-*.whl | grep skills/
```

## Test the Package Locally

```bash
# Install from wheel
pip install dist/fiftyone_skills-*.whl

# Test the CLI
fiftyone-skills --version
fiftyone-skills --help

# Test installation
cd /tmp
fiftyone-skills env=local agent=claude
```

## Publish to TestPyPI (Optional)

Test publishing on TestPyPI first:

```bash
# Using uv
uv publish --index https://test.pypi.org/legacy/

# Or using twine
pip install twine
twine upload --repository testpypi dist/*
```

Install from TestPyPI to verify:

```bash
pip install --index-url https://test.pypi.org/simple/ fiftyone-skills
```

## Publish to PyPI

Once verified, publish to the main PyPI:

```bash
# Using uv
uv publish

# Or using twine
twine upload dist/*
```

You'll be prompted for your PyPI credentials or API token.

## Verify Publication

After publishing:

```bash
# Install from PyPI
pip install fiftyone-skills

# Verify it works
fiftyone-skills --version
```

## Version Management

To release a new version:

1. Update version in `pyproject.toml`
2. Update version in `src/fiftyone_skills/__init__.py` (`__version__`)
3. Create a git tag:
   ```bash
   git tag -a v0.1.1 -m "Release v0.1.1"
   git push origin v0.1.1
   ```
4. Build and publish

## Using GitHub Actions (Recommended)

Create `.github/workflows/publish.yml` for automated publishing:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: pip install uv
      
      - name: Build package
        run: uv build
      
      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: uv publish
```

Add your PyPI API token to repository secrets as `PYPI_TOKEN`.

## Troubleshooting

### Build fails with "skills not found"

Ensure the skills directory exists at the repository root:
```bash
ls -la skills/
```

### Package is too large

The package includes all skill markdown files. This is intentional to allow offline installation.

### Import errors after installation

Make sure the package structure matches:
```
skills/
  fiftyone-*/
    SKILL.md
src/
  fiftyone_skills/
    __init__.py
```

Skills are bundled as wheel data and installed to `sysconfig.get_path("data")/skills/`.

## Notes

- The package uses `uv_build` as the build backend for simplicity
- All skills are included in the wheel for offline use
- The `--update` flag downloads from GitHub for the latest version
- No external dependencies required (uses only standard library)
