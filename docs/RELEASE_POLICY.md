## Release policy (written in stone)

### Reality

This GTK frontend cannot be end-to-end validated in CI without access to the maintainer’s real GPU / desktop environment.

### Therefore

- **Forgejo is the release authority.** All official release tags and release artifacts are minted via the **Forgejo** release workflow on the LAN instance.
- **GitHub is not a release authority.** GitHub CI exists for public-facing core quality gates only.

### Scope

- GitHub Actions may run `scripts/ci-core.sh` and other non-secret checks.
- Release credentials/tokens and release publication actions are **Forgejo-only**.

