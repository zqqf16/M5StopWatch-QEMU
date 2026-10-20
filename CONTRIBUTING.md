# Contributing

Thanks for helping! Issues and pull requests are welcome.

* **Bugs**: include the host OS/arch, `./run.sh --headless` log (`run/` is safe to share) and the firmware sha256.
* **QEMU changes** go into `patches/` as `git format-patch` output — see [AGENTS.md](AGENTS.md#patch-workflow).
  Patches are GPL-2.0-or-later; add `Signed-off-by:` (DCO, `git commit -s`).
* **Scripts / web UI / tools** are MIT. Python: stdlib only. Web: no CDN, single file.
* Before a PR: build (`scripts/build-*.sh`), run the headless smoke test and, for UI changes, `./run.sh --web`
  in Chrome and Firefox; attach a screenshot.
* Do not add third-party firmware binaries unless their license explicitly allows redistribution;
  prefer a download script with a sha256 like `scripts/fetch-firmware.sh`.
