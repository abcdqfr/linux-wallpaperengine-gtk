# Semantic Release Setup Documentation

## References & Best Practices

### Official Documentation

- **semantic-release**: https://github.com/semantic-release/semantic-release
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/

### Key Resources

1. **GitHub Actions Integration**: https://github.com/semantic-release/semantic-release/blob/master/docs/recipes/ci-configurations/github-actions.md
2. **Python Projects**: https://github.com/semantic-release/semantic-release/blob/master/docs/recipes/ci-configurations/python.md
3. **Configuration Options**: https://github.com/semantic-release/semantic-release/blob/master/docs/usage/configuration.md

## How It Works

### Commit Message Format

semantic-release analyzes commit messages using Conventional Commits:

- `fix:` → PATCH version (1.2.1 → 1.2.2)
- `feat:` → MINOR version (1.2.1 → 1.3.0)
- `BREAKING CHANGE:` or `!` → MAJOR version (1.2.1 → 2.0.0)
- `docs:`, `chore:`, `style:`, `refactor:`, `test:` → No version bump (unless breaking)

### Release Process (Automated)

1. Push commits to `main` branch
2. GitHub Actions triggers semantic-release
3. semantic-release:
   - Analyzes commits since last release
   - Determines next version (patch/minor/major)
   - Generates changelog
   - Creates git tag
   - Creates GitHub release
   - Updates CHANGELOG.md
   - Updates version in pyproject.toml (if configured)

### Configuration Files

#### `.releaserc.json`

- Defines branches to release from
- Configures plugins (analyzer, notes generator, changelog, GitHub, git)
- Sets up assets to commit back (CHANGELOG.md, pyproject.toml)

#### `.github/workflows/semantic-release.yml`

- Triggers on push to main
- Sets up Node.js environment
- Installs semantic-release
- Runs semantic-release with GITHUB_TOKEN

## Benefits

1. **Fully Automated**: No manual versioning or release creation
2. **Consistent**: Follows SemVer strictly
3. **Professional**: Auto-generated changelogs
4. **Safe**: Only releases when commits warrant it
5. **Traceable**: Every release tied to specific commits

## Migration from Manual Releases

**Before (Manual):**

```bash
git tag v1.2.2
git push origin v1.2.2
gh release create v1.2.2 --notes "..."
```

**After (Automated):**

```bash
git commit -m "fix: something"
git push origin main
# semantic-release automatically creates v1.2.2 release!
```

## Next Steps

1. ✅ Configuration files created
2. ⏭️ Test with a commit to verify it works
3. ⏭️ Monitor first automated release
4. ⏭️ Adjust configuration if needed
