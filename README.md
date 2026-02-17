# action-update-release

Create or update a GitHub Release and upload assets.

This action is intended to be used in CI pipelines to update an existing release.

| Name        | Description |
|-------------|-------------|
| `files`     | Files paths to upload as release assets. Required. |
| `repository`| Repository to update the release on (owner/repo). Defaults to the current repository `${{ github.repository }}`. |
| `tag`       | Tag of the release to update (e.g. `v1.2.3`). Required. |
| `token`     | GitHub token for authentication. Defaults to `${{ github.token }}`. |

Example usage

```yaml
name: Update Release
on:
  push:

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create or update release
        uses: zckv/action-update-release@v1
        with:
          tag: ${{ github.ref_name }}
          files: dist/*
          repository: ${{ github.repository }}
          token: ${{ secrets.GITHUB_TOKEN }}
```
