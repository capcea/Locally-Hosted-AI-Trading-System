# Phase 3 command evidence — 2026-10-27

Local records include UTC start, child exit code, duration, exact argv and sanitized output SHA-256.
The recorder `.cache/phase3/capture.py` itself exits0 after writing a failure; **the JSON child
exit_code is authoritative**, never the recorder wrapper exit. All commands ran from repository
root. It sets project-local UV/pip/npm caches and PLAYWRIGHT_BROWSERS_PATH=.cache/ms-playwright.
P0_CACHED_IMAGES=1 permits only already cached exact digest-pinned test images. No secrets are in
these outputs. Disposable service credentials/DSNs and development secrets are redacted.

## Acceptance interpretation

Current `make check`: 148 Python tests plus16 frontend. Installed-Python/npm audits pass; Windows
optional SDK/container vulnerability scans are NOT RUN. Current full integration: 1 readiness case,
35 actual service cases per write/restart stage and strict ready smoke200. Repeated stages/runs
are not distinct test scenarios. The main services are healthy, revision0004 and DENY_ALL.

Focused broker desktop and full default browser commands fail at actual Chromium macOS launch
(Permission denied1100), after native stages pass. Full default first group: 3 desktop page launch
failures/1 HTTP-only pass; later8 cases NOT RUN. All12 collect with explicit Playwright config.
No managed restriction was bypassed. Owner-reported earlier local passes are separate evidence.

Development failures are retained: missing imported market fixture; later old parent/new crash-child
receipt mismatch during ongoing edits; lint errors; connector image importing an absent API module;
pip-audit attempting a forbidden global cache; and an E2E collection invocation lacking --config.
Stable-source reruns/fixed packaging/local cache/explicit config resolve those failures. Initial
secret scan flagged a synthetic business idempotency identifier twice, not actual credentials.
The test retains identical semantics with a constructed identifier; one failed traceback identifier
was redacted. Its JSON retains the pre-sanitization hash and reason. No scanner rule was excluded.

The early private pg_dump predates owner enrollment. Preservation output distinguishes 17 matching
legacy table fingerprints from8 owner-bootstrap/MFA tables changed BEFORE migration. All25 current
post-migration fingerprints match during final rebuild/verification. Data-container IDs/mounts are
unchanged; current3-event HMAC audit verifies. Restore of the private dump was NOT TESTED.

External MT5/cTrader tests use fake SDK/protocol fixtures/OAuth MockTransport. Local bridge mTLS
and container CLI are real local tests only. No actual external account, Windows service or broker
execution was tested. `source-changes.json` records source/document hashes against the private
starting snapshot, excluding evidence/report to avoid recursive fingerprints. No Git commit exists.

## Commands and outcomes

### engine-first

UTC `2026-10-26T22:03:42.426956+00:00` · child exit **0** · 1.733s.

```sh
.venv/bin/python -m pytest tests/test_execution_engine.py -q
```

[Command record](engine-first.json), [output](engine-first.txt); SHA-256 `6f0fdb302387494059fe391e31e17f13d159d78cade8438e68bf5d3364b94f48`.

### first-portable

UTC `2026-10-26T22:12:59.028884+00:00` · child exit **0** · 3.791s.

```sh
.venv/bin/python -m pytest -m 'not infrastructure and not isolated_services'
```

[Command record](first-portable.json), [output](first-portable.txt); SHA-256 `b39d8af739b89b4efaea5445e65bdc31c98693b84328cf2aa003ffac9412aceb`.

### first-native

UTC `2026-10-26T22:15:31.725779+00:00` · child exit **2** · 49.757s.

```sh
env P0_CACHED_IMAGES=1 make integration-services
```

[Command record](first-native.json), [output](first-native.txt); SHA-256 `6c4c392b33a359a2bb4cee3cc05b4bec9b55b7ab755e8225ed01625d956d9c8e`.

### second-native

UTC `2026-10-26T22:19:14.611228+00:00` · child exit **0** · 95.219s.

```sh
env P0_CACHED_IMAGES=1 make integration-services
```

[Command record](second-native.json), [output](second-native.txt); SHA-256 `77494f1fabb851003a5c761cb8ddb38983ffb240a5a726546c3cccc9d51f3d12`.

### broker-contracts

UTC `2026-10-26T22:22:26.982154+00:00` · child exit **0** · 2.337s.

```sh
.venv/bin/python -m pytest tests/test_broker_contracts.py -q
```

[Command record](broker-contracts.json), [output](broker-contracts.txt); SHA-256 `8dc5666f6eb46299a0a92d4304240819230fc20fe066a35bdd885ae97444ed99`.

### quality-candidate

UTC `2026-10-26T22:31:34.454949+00:00` · child exit **2** · 2.356s.

```sh
make check
```

[Command record](quality-candidate.json), [output](quality-candidate.txt); SHA-256 `8577acf45a78b887461acecd81ab73d83a185fea94d610b70ec82ebb38d4f494`.

### broker-browser

UTC `2026-10-26T22:32:48.895790+00:00` · child exit **2** · 94.911s.

```sh
env P0_CACHED_IMAGES=1 E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=broker make browser-integration
```

[Command record](broker-browser.json), [output](broker-browser.txt); SHA-256 `fed505bceb5b5b223634c792b1e10ec43b7332998c0fdc20eb2f036c782accb9`.

### quality-with-ui

UTC `2026-10-26T22:32:49.739606+00:00` · child exit **0** · 13.447s.

```sh
make check
```

[Command record](quality-with-ui.json), [output](quality-with-ui.txt); SHA-256 `ef4b83c86b88d4199f64c32b95329444408947cf8fd09f8e1fb7876abb369773`.

### native-stable-receipts

UTC `2026-10-26T22:36:26.005571+00:00` · child exit **0** · 98.23s.

```sh
env P0_CACHED_IMAGES=1 make integration-services
```

[Command record](native-stable-receipts.json), [output](native-stable-receipts.txt); SHA-256 `f399a792c33fd8a9fccc9cb5484056b3e87dfa46c2f5fb8bed0e3749f758074e`.

### broker-browser-stable

UTC `2026-10-26T22:39:39.611150+00:00` · child exit **2** · 107.55s.

```sh
env P0_CACHED_IMAGES=1 E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=broker make browser-integration
```

[Command record](broker-browser-stable.json), [output](broker-browser-stable.txt); SHA-256 `84449984ec09451729f2b4f6ea7e03fb61248baa97a3e207e24198c6fb12e440`.

### images

UTC `2026-10-26T22:39:40.703440+00:00` · child exit **0** · 16.165s.

```sh
env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker
```

[Command record](images.json), [output](images.txt); SHA-256 `4e4eafcaf7d7928d0291efaeacb698e495250201fb5bd9c4b12ab8c81d0e175e`.

### local-mtls

UTC `2026-10-26T22:40:51.424530+00:00` · child exit **0** · 2.037s.

```sh
.venv/bin/python -m pytest tests/test_bridge_tls.py -q
```

[Command record](local-mtls.json), [output](local-mtls.txt); SHA-256 `ba74344cc5ae76fe8de2487020c81bb23e31d0f9fc3759533ef6690ea5ff3f14`.

### bridge-real-mtls

UTC `2026-10-26T22:41:48.354463+00:00` · child exit **0** · 2.143s.

```sh
.venv/bin/python -m pytest tests/test_bridge_tls.py -q
```

[Command record](bridge-real-mtls.json), [output](bridge-real-mtls.txt); SHA-256 `6d7c1113cc81a3b04e4b41ed4bfbec3aab3b91bb8233e18848e0eff5cf5c3ddd`.

### full-browser

UTC `2026-10-26T22:48:02.431030+00:00` · child exit **2** · 108.635s.

```sh
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO P0_CACHED_IMAGES=1 make browser-integration
```

[Command record](full-browser.json), [output](full-browser.txt); SHA-256 `455d9101d64b7397534f9171168b11a73bcffb489ce9865d3e99d29c6454dbe3`.

### broker-extended

UTC `2026-10-26T22:52:13.606506+00:00` · child exit **0** · 2.307s.

```sh
.venv/bin/python -m pytest tests/test_broker_contracts.py tests/test_bridge_tls.py -q
```

[Command record](broker-extended.json), [output](broker-extended.txt); SHA-256 `c0c6df0702da434814205a104f31dc6ebf20614d883da0b453a29c14e7e1fb8c`.

### pre-migration-backup

UTC `2026-10-26T22:54:15.037329+00:00` · child exit **0** · 3.591s.

```sh
Exact multiline argv is retained in pre-migration-backup.json (diagnostic source, not abbreviated in the record).
```

[Command record](pre-migration-backup.json), [output](pre-migration-backup.txt); SHA-256 `2f2fbd100b4b4707ca2219c69df725bc038de0e17f05e94e7af000e8afa0ad0b`.

### final-quality

UTC `2026-10-26T22:56:57.446522+00:00` · child exit **2** · 0.056s.

```sh
make check
```

[Command record](final-quality.json), [output](final-quality.txt); SHA-256 `0b26b733497e5f369f73c5948e6b7fde1edda5e47a7c457244507fe18e571293`.

### quality-final

UTC `2026-10-27T01:27:59.564351+00:00` · child exit **0** · 15.052s.

```sh
make check
```

[Command record](quality-final.json), [output](quality-final.txt); SHA-256 `7a0cb67f4b6921c122a09203313fd2b5572430688d2a139fddfe65fb7d34171a`.

### final-images

UTC `2026-10-27T01:28:03.951780+00:00` · child exit **0** · 3.518s.

```sh
env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker
```

[Command record](final-images.json), [output](final-images.txt); SHA-256 `2e0c9b84a8caf6c5395f6567215b402620619365494dcf2d2de7dde9351fdb25`.

### bridge-image

UTC `2026-10-27T01:28:10.115666+00:00` · child exit **0** · 16.871s.

```sh
env BUILDX_CONFIG=.cache/buildx docker build -f services/broker_bridge/Dockerfile -t ai-trading-readonly-bridge:phase3 .
```

[Command record](bridge-image.json), [output](bridge-image.txt); SHA-256 `cbca2a44232661255be8a7f980cadebc94822894fdcc637f752f2c02fa49f91b`.

### local-stack

UTC `2026-10-27T01:28:18.603680+00:00` · child exit **0** · 25.42s.

```sh
docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker
```

[Command record](local-stack.json), [output](local-stack.txt); SHA-256 `b57f80e8f4db8a52f3b7062b4c2a7f06ce5353c5d48588058fe61a68c7458079`.

### contracts

UTC `2026-10-27T01:29:04.770564+00:00` · child exit **0** · 2.717s.

```sh
make contracts-check
```

[Command record](contracts.json), [output](contracts.txt); SHA-256 `e83d04e653a779df6e6af2458ffebf921acfcd52f98ac175a710837cb3fb472b`.

### frontend-audit

UTC `2026-10-27T01:29:05.887470+00:00` · child exit **0** · 1.12s.

```sh
npm --prefix apps/web audit --audit-level=high
```

[Command record](frontend-audit.json), [output](frontend-audit.txt); SHA-256 `6d8c5c8f3d7684adb070417bd608d01ae90aa3dc26a65af03ffda4955f38d9a3`.

### python-audit

UTC `2026-10-27T01:29:07.044502+00:00` · child exit **1** · 0.832s.

```sh
env UV_CACHE_DIR=.cache/uv .tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --progress-spinner off
```

[Command record](python-audit.json), [output](python-audit.txt); SHA-256 `f9b7ad6e4080852847ff3bdf99a32d1ba4a2c928476b5b0d72cd77a97b0c5811`.

### python-audit-cache

UTC `2026-10-27T01:29:14.462210+00:00` · child exit **0** · 4.426s.

```sh
env UV_CACHE_DIR=.cache/uv .tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off
```

[Command record](python-audit-cache.json), [output](python-audit-cache.txt); SHA-256 `15950a68a7ed99c59779717acefdceb3f69cfd31bde67d2c954f2a3cea4d7955`.

### integration-final

UTC `2026-10-27T01:29:20.493222+00:00` · child exit **0** · 106.163s.

```sh
env P0_CACHED_IMAGES=1 make integration
```

[Command record](integration-final.json), [output](integration-final.txt); SHA-256 `91bdf0cc043537b7cbb3a61535ea4c988c5741732959b829272f8d870a4d2017`.

### preservation

UTC `2026-10-27T01:29:21.660426+00:00` · child exit **1** · 1.251s.

```sh
env PYTHONPATH=. .venv/bin/python .cache/phase3/preservation.py
```

[Command record](preservation.json), [output](preservation.txt); SHA-256 `5e71aeaa95714d8e540d83e8ed5c0a5146d3bad0c8e7684fea1e103619500ce5`.

### bridge-help

UTC `2026-10-27T01:29:22.847971+00:00` · child exit **1** · 1.653s.

```sh
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 768m --pids-limit 64 ai-trading-readonly-bridge:phase3 --help
```

[Command record](bridge-help.json), [output](bridge-help.txt); SHA-256 `0e66e5e60e92fc15e20e61b1c011932a52d7d7ba89f29ca1a464a5bc7d8deb9c`.

### e2e-collection

UTC `2026-10-27T01:29:24.004850+00:00` · child exit **1** · 1.886s.

```sh
npm --prefix apps/web exec -- playwright test --list
```

[Command record](e2e-collection.json), [output](e2e-collection.txt); SHA-256 `8d452d904ddce0409c7ba15331efd169c22c882633ea70daa63b90e3e84095a2`.

### bridge-image-fixed

UTC `2026-10-27T01:30:29.879561+00:00` · child exit **0** · 2.492s.

```sh
env BUILDX_CONFIG=.cache/buildx docker build -f services/broker_bridge/Dockerfile -t ai-trading-readonly-bridge:phase3 .
```

[Command record](bridge-image-fixed.json), [output](bridge-image-fixed.txt); SHA-256 `eacd2b69969d543fded9c0ee33e0647f98a69f0379ba96fd5ef3fa0f276ce22d`.

### e2e-collection-correct

UTC `2026-10-27T01:30:30.861894+00:00` · child exit **0** · 1.794s.

```sh
npm --prefix apps/web exec -- playwright test --config apps/web/playwright.config.ts --list
```

[Command record](e2e-collection-correct.json), [output](e2e-collection-correct.txt); SHA-256 `c19bc55efcc43b90b1b1c58e0c13a69d367c52c3c915c6737654cac8a7a79a78`.

### quality-packaging-fixed

UTC `2026-10-27T01:30:39.382302+00:00` · child exit **0** · 15.599s.

```sh
make check
```

[Command record](quality-packaging-fixed.json), [output](quality-packaging-fixed.txt); SHA-256 `cd15ee9302805861b0797ab4db4ed81020eae06e08c33a88c5d77d329bb2f8b0`.

### bridge-help-fixed

UTC `2026-10-27T01:31:11.185218+00:00` · child exit **0** · 1.371s.

```sh
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 768m --pids-limit 64 ai-trading-readonly-bridge:phase3 --help
```

[Command record](bridge-help-fixed.json), [output](bridge-help-fixed.txt); SHA-256 `af1352a308280059da5b4ff566975e14884f98a7cfe811fa36239fe4073effe4`.

### images-packaging-fixed

UTC `2026-10-27T01:31:12.356945+00:00` · child exit **0** · 3.64s.

```sh
env BUILDX_CONFIG=.cache/buildx docker compose build api migrate web market-worker
```

[Command record](images-packaging-fixed.json), [output](images-packaging-fixed.txt); SHA-256 `e29b29214f46e21f4b03d5918cef4e7587c449debe27ad7ecca1462a67337de3`.

### contracts-packaging-fixed

UTC `2026-10-27T01:31:13.517360+00:00` · child exit **0** · 3.233s.

```sh
make contracts-check
```

[Command record](contracts-packaging-fixed.json), [output](contracts-packaging-fixed.txt); SHA-256 `3c9cbd0505ccb45dfa1037abe10e1f6eed7634994ea78a5126d6ead2f0e936b2`.

### local-stack-packaging-fixed

UTC `2026-10-27T01:33:49.736926+00:00` · child exit **0** · 24.775s.

```sh
docker compose up --pull never --no-build -d --wait --wait-timeout 180 api web market-worker
```

[Command record](local-stack-packaging-fixed.json), [output](local-stack-packaging-fixed.txt); SHA-256 `172d1ad0e8e1a362115cbe88535afc37e612e0ff5cb691f23410cd6364fa05ea`.

### preservation-verified

UTC `2026-10-27T01:34:57.320200+00:00` · child exit **0** · 10.876s.

```sh
env PYTHONPATH=. .venv/bin/python .cache/phase3/preservation.py
```

[Command record](preservation-verified.json), [output](preservation-verified.txt); SHA-256 `fc577df321e5ecc3ec2ba9f3d3dcfa76ea2647115c42a6b7871d17a9d0f1928b`.

### integration-packaging-fixed

UTC `2026-10-27T01:34:58.463351+00:00` · child exit **0** · 102.703s.

```sh
env P0_CACHED_IMAGES=1 make integration
```

[Command record](integration-packaging-fixed.json), [output](integration-packaging-fixed.txt); SHA-256 `98409e152d456f08af80ae46a1c7cfb688c52c5b8355fdbf7c5512923ba6a844`.

### smoke

UTC `2026-10-27T01:34:59.630123+00:00` · child exit **0** · 0.316s.

```sh
make smoke-demo
```

[Command record](smoke.json), [output](smoke.txt); SHA-256 `be6147870901b36d75a5d3cf6104437dc132e4a59a3d36d799f9421326191a8c`.

### local-config

UTC `2026-10-27T01:35:00.040365+00:00` · child exit **0** · 0.16s.

```sh
.venv/bin/python -c 'import subprocess; subprocess.run(["docker","compose","config","--quiet"],check=True); subprocess.run([".tools/bin/actionlint"],check=True); print("PASSED: Compose configuration and pinned Actions syntax; remote CI not run.")'
```

[Command record](local-config.json), [output](local-config.txt); SHA-256 `199e5d3bc7fe6cf5bcc6ca960a9d768b4c2ccb47de14e826868f1f65e985c107`.

### desktop-browser-final

UTC `2026-10-27T01:37:26.436334+00:00` · child exit **2** · 122.394s.

```sh
env P0_CACHED_IMAGES=1 E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=broker make browser-integration
```

[Command record](desktop-browser-final.json), [output](desktop-browser-final.txt); SHA-256 `effb12ebb862295a7f685212e335d6168e627af38df7498ccd82d9cb66cbbd28`.

### local-config-final

UTC `2026-10-27T01:37:27.549409+00:00` · child exit **0** · 0.143s.

```sh
.venv/bin/python -c 'import subprocess; subprocess.run(["docker","compose","config","--quiet"],check=True); subprocess.run([".tools/bin/actionlint"],check=True); print("PASSED: Compose and Actions syntax, including independent connector image check. Remote CI NOT RUN.")'
```

[Command record](local-config-final.json), [output](local-config-final.txt); SHA-256 `c1c2277f3aef16fa2fbe0db61a3b8cf8a6bf89da2c713adefea5f8929134a1d2`.

### secret-scan

UTC `2026-10-27T01:37:27.777096+00:00` · child exit **2** · 1.164s.

```sh
make secret-scan
```

[Command record](secret-scan.json), [output](secret-scan.txt); SHA-256 `dc6e04d0aca62098ae5115c3ff7cfa15234060ef178436957b85694e92f70e35`.

### full-browser-final

UTC `2026-10-27T01:39:50.474091+00:00` · child exit **2** · 227.638s.

```sh
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO P0_CACHED_IMAGES=1 make browser-integration
```

[Command record](full-browser-final.json), [output](full-browser-final.txt); SHA-256 `2d57d3858078f96b8838c07efcb42ff40241ecc3c7fbbd6cf2215d1c40dbe9ad`.

### secret-scan-fixed

UTC `2026-10-27T01:39:52.854724+00:00` · child exit **0** · 4.097s.

```sh
make secret-scan
```

[Command record](secret-scan-fixed.json), [output](secret-scan-fixed.txt); SHA-256 `6fb96ebc4694f9c1472e36e69be43eaa308741c1f8be001bf210522d9c7b6b0a`.

### quality-release

UTC `2026-10-27T01:40:13.556719+00:00` · child exit **0** · 37.463s.

```sh
make check
```

[Command record](quality-release.json), [output](quality-release.txt); SHA-256 `5b409946f5b1665a4b36e5c0b127f63db116ed91b3d3a253386fed836a71938b`.

### repository-final

UTC `2026-10-27T01:41:25.301544+00:00` · child exit **0** · 0.173s.

```sh
make repository-check
```

[Command record](repository-final.json), [output](repository-final.txt); SHA-256 `5f2c6bd078e60cf2bbca371cd454ddee48f63c86958c7ac02dc70ff12075460b`.

### resource-cleanup

UTC `2026-10-27T01:42:00.414110+00:00` · child exit **0** · 0.204s.

```sh
.venv/bin/python -c 'import re,subprocess; from pathlib import Path; owned=set(); [owned.update(re.findall(r"phase0-test-[a-f0-9]{32}",p.read_text())) for p in Path("docs/phase3-evidence/2026-10-27").glob("*.txt")]; outputs=[subprocess.check_output(args,text=True) for args in (["docker","ps","-a","--format","{{.Labels}}"],["docker","volume","ls","--format","{{.Labels}}"],["docker","network","ls","--format","{{.Labels}}"] )]; left=set().union(*(set(re.findall(r"phase0-test-[a-f0-9]{32}",s)) for s in outputs)) & owned; assert not left,sorted(left); print("PASSED: no containers, volumes or networks remain for",len(owned),"finished Phase3 UUID test projects; no development resources removed.")'
```

[Command record](resource-cleanup.json), [output](resource-cleanup.txt); SHA-256 `1439745fea605a5d8acfda4394f050015b76f81f7598b6969a993862e7d2a6b7`.

### preservation-final

UTC `2026-10-27T01:42:28.472589+00:00` · child exit **0** · 44.094s.

```sh
env PYTHONPATH=. .venv/bin/python .cache/phase3/preservation.py
```

[Command record](preservation-final.json), [output](preservation-final.txt); SHA-256 `fc577df321e5ecc3ec2ba9f3d3dcfa76ea2647115c42a6b7871d17a9d0f1928b`.

### repository-secret-final

UTC `2026-10-27T01:42:29.989865+00:00` · child exit **0** · 10.746s.

```sh
.venv/bin/python -c 'import subprocess; subprocess.run(["make","repository-check"],check=True); subprocess.run(["make","secret-scan"],check=True)'
```

[Command record](repository-secret-final.json), [output](repository-secret-final.txt); SHA-256 `a077fd245eb491cdde864e0c94c56a3af7a921c6b9718dc84f0c58ef2095b8ba`.

### cleanup-final

UTC `2026-10-27T01:43:58.541650+00:00` · child exit **0** · 0.172s.

```sh
.venv/bin/python -c 'import re,subprocess;from pathlib import Path; owned=set(); [owned.update(re.findall(r"phase0-test-[a-f0-9]{32}",p.read_text())) for p in Path("docs/phase3-evidence/2026-10-27").glob("*.txt")]; actual=set(); [actual.update(re.findall(r"phase0-test-[a-f0-9]{32}",subprocess.check_output(args,text=True))) for args in (["docker","ps","-a","--format","{{.Labels}}"],["docker","volume","ls","--format","{{.Labels}}"],["docker","network","ls","--format","{{.Labels}}"] )]; assert not owned.intersection(actual); print("PASSED: all",len(owned),"completed Phase3 disposable projects have no remaining containers/volumes/networks; development resources untouched.")'
```

[Command record](cleanup-final.json), [output](cleanup-final.txt); SHA-256 `e4c1abf426b5b610080fd19423d4b2f3e1234682e06f0b52c7303ed67c5a2417`.

### source-scan-release

UTC `2026-10-27T01:44:27.195819+00:00` · child exit **0** · 1.218s.

```sh
make secret-scan
```

[Command record](source-scan-release.json), [output](source-scan-release.txt); SHA-256 `8a2a6e737b7f10c9c9d1149709844f7a8d8bb717610d72f93b20a5a82916ea73`.

