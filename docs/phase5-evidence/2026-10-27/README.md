# Phase 5 execution evidence — 2026-10-27

Exact recorded child commands, exits, timing and sanitized logs. No remote CI or browser pass is
inferred from collection, owner statements or recorder exit0. JSON exit_code is authoritative.
Failure logs are retained; only a synthetic idempotency identifier triggered narrow redaction with
original SHA/private0600 original retained. No credentials, auth-page snapshots or raw private dumps.

Focused helpers are private diagnostic copies of scripts/integration_services.py with only the named
research module selected. Public reproducible acceptance is make check, make integration and
make browser-integration; those run the complete configured suites. All actual services are disposable,
UUID-scoped, temporary-credential, loopback/TCP-verified; cleanup never targets development volumes.
Runtime/preservation helpers compare private backups, table hashes, schema and Docker configuration.
Their exact behavior and limitations are described in the completion report; private dumps stay ignored.

- **baseline-check** — exit `2`, 2.325s, UTC `2026-10-27T09:10:41.958459+00:00`.
  Command: `make check`. [record](baseline-check.json), [log](baseline-check.txt).
  Sanitized log SHA-256: `441257c8a853e5df0a1ce3209314680494a8c07aa21a6154e814fcd6719f2719`.
- **migrations** — exit `0`, 1.268s, UTC `2026-10-27T09:20:05.925967+00:00`.
  Command: `.venv/bin/python -m pytest tests/test_migrations.py -q`. [record](migrations.json), [log](migrations.txt).
  Sanitized log SHA-256: `d5f60becc5883b79166632ee14484ea7bbe789669ca6d929bdb8a13436f01e9a`.
- **research-math-first** — exit `0`, 1.452s, UTC `2026-10-27T09:21:53.696151+00:00`.
  Command: `.venv/bin/python -m pytest tests/test_research_math.py -q`. [record](research-math-first.json), [log](research-math-first.txt).
  Sanitized log SHA-256: `126dc8397d2694036da980639cecc19248d90d079073215858b5d6ded280c381`.
- **native-research-first** — exit `1`, 11.521s, UTC `2026-10-27T09:25:11.867693+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/focused_services.py`. [record](native-research-first.json), [log](native-research-first.txt).
  Sanitized log SHA-256: `b045681e3bc245db35058270d4b2e5b952262cca8e695f4a86bdcba3321cdb27`.
- **native-research-context** — exit `1`, 10.997s, UTC `2026-10-27T09:26:18.098512+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/focused_services.py`. [record](native-research-context.json), [log](native-research-context.txt).
  Sanitized log SHA-256: `0eb1679fe93566f105940356dceb6d8c0315c21d76601c50a5348d47229b5faa`.
- **contracts-initial** — exit `0`, 2.035s, UTC `2026-10-27T09:26:19.123413+00:00`.
  Command: `make contracts`. [record](contracts-initial.json), [log](contracts-initial.txt).
  Sanitized log SHA-256: `97d978035acce61d6c234961073e0dfeb199e0005610cafc2653d432c9d82db1`.
- **native-research-symbol** — exit `0`, 43.534s, UTC `2026-10-27T09:28:57.590785+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/focused_services.py`. [record](native-research-symbol.json), [log](native-research-symbol.txt).
  Sanitized log SHA-256: `7a01b0cbc3caf6539255f38fcdf9470a26109f70709e1b713dc9e35a9a63dce4`.
- **native-research-audit-faults** — exit `0`, 56.38s, UTC `2026-10-27T09:39:28.897129+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/focused_services.py`. [record](native-research-audit-faults.json), [log](native-research-audit-faults.txt).
  Sanitized log SHA-256: `91350e6191cad6ea7cf9ef22e839377fe73a724894b7ffb4efdfc9a7fec3fa23`.
- **native-research-extended** — exit `1`, 43.069s, UTC `2026-10-27T11:23:14.697170+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/focused_services.py`. [record](native-research-extended.json), [log](native-research-extended.txt).
  Sanitized log SHA-256: `dd7283735ee6d9872b426563db841fd5f76f76579ee32a10208ff0401d3b04bb`.
- **contracts-pending** — exit `0`, 1.831s, UTC `2026-10-27T11:29:40.529962+00:00`.
  Command: `make contracts`. [record](contracts-pending.json), [log](contracts-pending.txt).
  Sanitized log SHA-256: `60cc142bb7808cacf6288a4637c25fe676deadce31709dc5920af8810b739b54`.
- **native-research-pending-funding** — exit `0`, 87.216s, UTC `2026-10-27T11:30:55.333990+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/focused_services.py`. [record](native-research-pending-funding.json), [log](native-research-pending-funding.txt).
  Sanitized log SHA-256: `9313b20d793a70b4acba3e98f8d5484a5c2ab34950cc87c9fb442cc95681c8b3`.
- **research-math-money** — exit `0`, 1.364s, UTC `2026-10-27T12:03:30.618401+00:00`.
  Command: `.venv/bin/python -m pytest tests/test_research_math.py -q`. [record](research-math-money.json), [log](research-math-money.txt).
  Sanitized log SHA-256: `180f562c2148d3564eb5a8ac37c75f7d1cc529175847b0a2fe9950837831c83e`.
- **native-research-causality** — exit `0`, 85.065s, UTC `2026-10-27T12:03:32.009000+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/focused_services.py`. [record](native-research-causality.json), [log](native-research-causality.txt).
  Sanitized log SHA-256: `461451e49cb9ac3e0ece2c65709cc904437a88696e56605afd8250a625e0388c`.
- **contracts-causal** — exit `0`, 1.809s, UTC `2026-10-27T12:05:03.199708+00:00`.
  Command: `make contracts`. [record](contracts-causal.json), [log](contracts-causal.txt).
  Sanitized log SHA-256: `d53054a2d44dc97840f45c91dac496237c1c3ffe238d742781cb26958830d13c`.
- **research-math-final** — exit `0`, 1.959s, UTC `2026-10-27T12:20:20.935666+00:00`.
  Command: `.venv/bin/pytest tests/test_research_math.py -q`. [record](research-math-final.json), [log](research-math-final.txt).
  Sanitized log SHA-256: `b52602c3a6aaf37e9c8ef7965b9fe97425aa7f05048c984af907cbde7f4c03d1`.
- **contracts-final** — exit `0`, 1.757s, UTC `2026-10-27T12:20:21.984299+00:00`.
  Command: `make contracts`. [record](contracts-final.json), [log](contracts-final.txt).
  Sanitized log SHA-256: `9c92deea0f704348eb39d925c20ee473262ebee6ac44008efeeda824f7e6e99c`.
- **check-first** — exit `2`, 2.281s, UTC `2026-10-27T12:21:19.308722+00:00`.
  Command: `make check`. [record](check-first.json), [log](check-first.txt).
  Sanitized log SHA-256: `86f5837d932c60f88610fae311b28cc835240e5201e598384aa4a790eec4d51d`.
- **native-current** — exit `0`, 136.481s, UTC `2026-10-27T12:21:23.731029+00:00`.
  Command: `.venv/bin/python .cache/phase5/focused_services.py`. [record](native-current.json), [log](native-current.txt).
  Sanitized log SHA-256: `6fcb63a2a1392747b008c2ecc09e64d9650c88ba39663440d072b205dd11d16f`.
- **check-formatted** — exit `2`, 5.347s, UTC `2026-10-27T12:21:31.966117+00:00`.
  Command: `make check`. [record](check-formatted.json), [log](check-formatted.txt).
  Sanitized log SHA-256: `a33d91ed8a0a7a4c91fa76a40810c86695c5f70c09ccf9b3eb45bc4e78f82067`.
- **development-preservation-before** — exit `0`, 5.633s, UTC `2026-10-27T12:21:33.005315+00:00`.
  Command: `.venv/bin/python .cache/phase5/preserve.py before`. [record](development-preservation-before.json), [log](development-preservation-before.txt).
  Sanitized log SHA-256: `fa3d372e09651f998a236ffad1805ac6f0711565d7bcc885de6ec17bce0c9831`.
- **check-typed** — exit `0`, 13.163s, UTC `2026-10-27T12:22:02.579737+00:00`.
  Command: `make check`. [record](check-typed.json), [log](check-typed.txt).
  Sanitized log SHA-256: `bd373f3ac01cccf39130f8ea314efebab5ae1576e11dd3a76bfcc45eef25d05e`.
- **build-local** — exit `0`, 7.207s, UTC `2026-10-27T12:22:28.394120+00:00`.
  Command: `env BUILDX_CONFIG=.cache/buildx docker compose build api web market-worker risk-monitor research-worker`. [record](build-local.json), [log](build-local.txt).
  Sanitized log SHA-256: `573fd228cc7a908bfa2dfd7821db1fcc66cd9b10258c33e28934e58aece3a022`.
- **contracts-check** — exit `0`, 2.264s, UTC `2026-10-27T12:22:29.515446+00:00`.
  Command: `make contracts-check`. [record](contracts-check.json), [log](contracts-check.txt).
  Sanitized log SHA-256: `62f97ad3507f6d507baba75eae13852c86a256314d7a543f1062ce6435949a8d`.
- **start-local** — exit `1`, 86.928s, UTC `2026-10-27T12:23:03.289589+00:00`.
  Command: `docker compose up --pull never --no-build -d --wait --wait-timeout 180`. [record](start-local.json), [log](start-local.txt).
  Sanitized log SHA-256: `591d2caba068f2e0bfa9beacae33127a4f6f488361d896233c29739a9b4b8f44`.
- **dependencies-python** — exit `0`, 3.919s, UTC `2026-10-27T12:23:04.454037+00:00`.
  Command: `.tools/bin/uv run --with pip-audit==2.10.1 python -m pip_audit --cache-dir .cache/pip-audit --progress-spinner off`. [record](dependencies-python.json), [log](dependencies-python.txt).
  Sanitized log SHA-256: `15950a68a7ed99c59779717acefdceb3f69cfd31bde67d2c954f2a3cea4d7955`.
- **dependencies-node** — exit `0`, 0.815s, UTC `2026-10-27T12:23:05.605721+00:00`.
  Command: `npm --prefix apps/web audit --audit-level=high`. [record](dependencies-node.json), [log](dependencies-node.txt).
  Sanitized log SHA-256: `6d8c5c8f3d7684adb070417bd608d01ae90aa3dc26a65af03ffda4955f38d9a3`.
- **build-migrator** — exit `0`, 1.809s, UTC `2026-10-27T12:24:06.706194+00:00`.
  Command: `env BUILDX_CONFIG=.cache/buildx docker compose build migrate`. [record](build-migrator.json), [log](build-migrator.txt).
  Sanitized log SHA-256: `f3a7048869e32e4e1900b7219e895ee4cfd1b58947868d18b25a2caf5c20205c`.
- **integration-services** — exit `0`, 322.184s, UTC `2026-10-27T12:24:07.850653+00:00`.
  Command: `make integration-services`. [record](integration-services.json), [log](integration-services.txt).
  Sanitized log SHA-256: `08c0c4c0f37953c0c4992a512542973670387ef6ee4eaa24496b3d935de7775f`.
- **migrate-local** — exit `0`, 1.866s, UTC `2026-10-27T12:24:22.646845+00:00`.
  Command: `docker compose run --rm --no-deps migrate`. [record](migrate-local.json), [log](migrate-local.txt).
  Sanitized log SHA-256: `170fa3c6a40b5662692a650de4d2244293c057c25c96e7aa672f7c47b1bd4b50`.
- **browser-research-desktop** — exit `2`, 328.864s, UTC `2026-10-27T12:24:23.795005+00:00`.
  Command: `env E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=research make browser-integration`. [record](browser-research-desktop.json), [log](browser-research-desktop.txt).
  Sanitized log SHA-256: `1d61dd3dc2ac0c370c7ad0a4c5c9ea750c2ea4a37cac292286c1827612518112`.
- **start-local-migrated** — exit `0`, 25.168s, UTC `2026-10-27T12:26:59.602171+00:00`.
  Command: `docker compose up --pull never --no-build -d --wait --wait-timeout 180`. [record](start-local-migrated.json), [log](start-local-migrated.txt).
  Sanitized log SHA-256: `3f4c6e9fa300f146bbd4892a4178d6d340b07dc6fe23e14e3b2e9505b1c9d942`.
- **development-preservation-after** — exit `0`, 10.249s, UTC `2026-10-27T12:27:00.814928+00:00`.
  Command: `.venv/bin/python .cache/phase5/preserve.py after`. [record](development-preservation-after.json), [log](development-preservation-after.txt).
  Sanitized log SHA-256: `f42cb0e1b72c799b8469417f6452456f24c0d0f7d3bf61e5c84824690a6c871a`.
- **runtime-verification** — exit `1`, 0.717s, UTC `2026-10-27T12:27:40.827299+00:00`.
  Command: `.venv/bin/python .cache/phase5/validate_runtime.py`. [record](runtime-verification.json), [log](runtime-verification.txt).
  Sanitized log SHA-256: `c14ac9aa1b309c6a88ea886e2af32ce786e0b66fdf0b79b285b1a47e5945c3a8`.
- **runtime-verified** — exit `0`, 11.059s, UTC `2026-10-27T12:28:02.774821+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/validate_runtime.py`. [record](runtime-verified.json), [log](runtime-verified.txt).
  Sanitized log SHA-256: `29e0d28412ec9e96b93ee0707afc2c55ebedb3d008cc90a36794c377c9ade051`.
- **native-fx** — exit `1`, 14.928s, UTC `2026-10-27T12:28:55.622551+00:00`.
  Command: `.venv/bin/python .cache/phase5/focused_fx.py`. [record](native-fx.json), [log](native-fx.txt).
  Sanitized log SHA-256: `70b7220d15e277289f5218a2ffabb239cf8f41374206468025dd2344676e95c9`.
- **smoke** — exit `0`, 0.341s, UTC `2026-10-27T12:29:34.594513+00:00`.
  Command: `make smoke-demo`. [record](smoke.json), [log](smoke.txt).
  Sanitized log SHA-256: `be6147870901b36d75a5d3cf6104437dc132e4a59a3d36d799f9421326191a8c`.
- **native-fx-venue** — exit `1`, 7.948s, UTC `2026-10-27T12:29:56.214935+00:00`.
  Command: `.venv/bin/python .cache/phase5/focused_fx.py`. [record](native-fx-venue.json), [log](native-fx-venue.txt).
  Sanitized log SHA-256: `3ef1a6cf81be88c892ce2ff3d4204efe455f262e01202c6bdac1eb14038d3c3c`.
- **math-precision** — exit `0`, 1.499s, UTC `2026-10-27T12:29:57.253532+00:00`.
  Command: `.venv/bin/pytest tests/test_research_math.py -q`. [record](math-precision.json), [log](math-precision.txt).
  Sanitized log SHA-256: `662e60dd1d1f784146743de9f6a9ac68a45f3517d446fd2bcb7e02407322832a`.
- **validation-config** — exit `0`, 0.019s, UTC `2026-10-27T12:30:04.469548+00:00`.
  Command: `.tools/bin/actionlint`. [record](validation-config.json), [log](validation-config.txt).
  Sanitized log SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- **compose-development** — exit `0`, 0.059s, UTC `2026-10-27T12:30:04.519837+00:00`.
  Command: `docker compose config --quiet`. [record](compose-development.json), [log](compose-development.txt).
  Sanitized log SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- **native-fx-diagnostic** — exit `1`, 8.38s, UTC `2026-10-27T12:30:20.853543+00:00`.
  Command: `.venv/bin/python .cache/phase5/focused_fx.py`. [record](native-fx-diagnostic.json), [log](native-fx-diagnostic.txt).
  Sanitized log SHA-256: `90a86011d699857ebfa5758239ee86914f011eea034e208b2fa808935b67bfdc`.
- **secrets-review** — exit `2`, 0.831s, UTC `2026-10-27T12:30:37.364658+00:00`.
  Command: `make secret-scan`. [record](secrets-review.json), [log](secrets-review.txt).
  Sanitized log SHA-256: `b6cb0f9fa2daa7d0d22605161416977d2b3893cad77e3cf57625a148ab9f8bcc`.
- **browser-collection** — exit `0`, 0.76s, UTC `2026-10-27T12:30:38.251990+00:00`.
  Command: `npm --prefix apps/web run test:e2e -- --list`. [record](browser-collection.json), [log](browser-collection.txt).
  Sanitized log SHA-256: `7ea23e94bd80ca11982801f619a9309eb83c18cb52879d2754eccd3f2d02f992`.
- **native-fx-error** — exit `1`, 8.204s, UTC `2026-10-27T12:30:56.530955+00:00`.
  Command: `.venv/bin/python .cache/phase5/focused_fx.py`. [record](native-fx-error.json), [log](native-fx-error.txt).
  Sanitized log SHA-256: `709148d94148930081e41cd9c66277af29f6bc5c9b0f59191e53184e505315e1`.
- **native-fx-authorized** — exit `0`, 18.391s, UTC `2026-10-27T12:31:31.754789+00:00`.
  Command: `.venv/bin/python .cache/phase5/focused_fx.py`. [record](native-fx-authorized.json), [log](native-fx-authorized.txt).
  Sanitized log SHA-256: `46cda8d4e07c57d88d5ebaef52f2df11547496434f738d1485ead314efd58e66`.
- **integration-final** — exit `0`, 323.448s, UTC `2026-10-27T12:31:57.990959+00:00`.
  Command: `make integration`. [record](integration-final.json), [log](integration-final.txt).
  Sanitized log SHA-256: `14e5b742b0712715d099990cf79aa7225f6ffcedd461db9ea8d575822a7ff810`.
- **browser-full** — exit `2`, 331.531s, UTC `2026-10-27T12:31:59.104670+00:00`.
  Command: `make browser-integration`. [record](browser-full.json), [log](browser-full.txt).
  Sanitized log SHA-256: `a5f5e0b5a89abb72365b90e8f3817884f52851ba08a81ba6f85abf69734ac48b`.
- **check-final** — exit `0`, 11.114s, UTC `2026-10-27T12:32:00.271555+00:00`.
  Command: `make check`. [record](check-final.json), [log](check-final.txt).
  Sanitized log SHA-256: `66db67a1ec069c2ffd7d84c5b123e01d9857ba8a244cfd95cc1da95b748a5b5c`.
- **secrets-final** — exit `0`, 1.579s, UTC `2026-10-27T12:36:58.339214+00:00`.
  Command: `make secret-scan`. [record](secrets-final.json), [log](secrets-final.txt).
  Sanitized log SHA-256: `1aa271774a771c0f4376c70fd93563460666e6cdf7c62d785b1e6ed5ba476a5e`.
- **repository-final** — exit `0`, 0.13s, UTC `2026-10-27T12:36:59.982775+00:00`.
  Command: `make repository-check`. [record](repository-final.json), [log](repository-final.txt).
  Sanitized log SHA-256: `e3e80f312051ad53dbae6fd95524540c0a55fb6b7bd99d6ef6c5d828f6528b0d`.
- **readiness-strict** — exit `0`, 0.054s, UTC `2026-10-27T12:39:44.271698+00:00`.
  Command: `curl --fail --silent http://127.0.0.1:18000/health/ready`. [record](readiness-strict.json), [log](readiness-strict.txt).
  Sanitized log SHA-256: `195fc4a14f71acbdc141abf706918868a703da314046c383eda9015fffea6333`.
- **preservation-final** — exit `0`, 3.443s, UTC `2026-10-27T12:39:44.353117+00:00`.
  Command: `.venv/bin/python .cache/phase5/preserve.py after`. [record](preservation-final.json), [log](preservation-final.txt).
  Sanitized log SHA-256: `f42cb0e1b72c799b8469417f6452456f24c0d0f7d3bf61e5c84824690a6c871a`.
- **secrets-release** — exit `0`, 0.924s, UTC `2026-10-27T12:40:35.462564+00:00`.
  Command: `make secret-scan`. [record](secrets-release.json), [log](secrets-release.txt).
  Sanitized log SHA-256: `b2eec982ceff98071475e21a4e1a42687b79b112729d778ffa8cf128f3312286`.
- **repository-release** — exit `0`, 0.054s, UTC `2026-10-27T12:40:36.417008+00:00`.
  Command: `make repository-check`. [record](repository-release.json), [log](repository-release.txt).
  Sanitized log SHA-256: `818b4e33d417b924a1a3eb21a2a88ceb65f18173b93aafeeb6c94162488c36e9`.
- **contracts-release** — exit `0`, 1.952s, UTC `2026-10-27T12:40:36.498656+00:00`.
  Command: `make contracts-check`. [record](contracts-release.json), [log](contracts-release.txt).
  Sanitized log SHA-256: `31789735c2be79f51d7e1ce79535b0c2bdedb26abbe41fe91858373b364c0326`.
- **whitespace-final** — exit `0`, 0.017s, UTC `2026-10-27T12:40:38.478406+00:00`.
  Command: `git diff --check`. [record](whitespace-final.json), [log](whitespace-final.txt).
  Sanitized log SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- **label-focused-desktop** — exit `2`, 273.99s, UTC `2026-10-27T14:36:28.446772+00:00`.
  Command: `env E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=research make browser-integration`. [record](label-focused-desktop.json), [log](label-focused-desktop.txt).
  Sanitized log SHA-256: `0bd6ed49106ae299d7e4b26dd2ecfa6d161227f8b1dd2720e3db7c27bd51d368`.
- **label-check** — exit `0`, 10.517s, UTC `2026-10-27T14:36:51.190435+00:00`.
  Command: `make check`. [record](label-check.json), [log](label-check.txt).
  Sanitized log SHA-256: `e476fb257aa3e78382531c0c7c99ba877c6de9e8e15510658790f1911a6fbfa8`.
- **label-integration** — exit `0`, 271.41s, UTC `2026-10-27T14:36:52.364731+00:00`.
  Command: `make integration`. [record](label-integration.json), [log](label-integration.txt).
  Sanitized log SHA-256: `6590293e999d9076ded7454696f56528a84ccef877f9f5d1c6eef21f7cd0ec71`.
- **label-contracts** — exit `0`, 2.176s, UTC `2026-10-27T14:37:37.488455+00:00`.
  Command: `make contracts-check`. [record](label-contracts.json), [log](label-contracts.txt).
  Sanitized log SHA-256: `6dbd944268ccdf0f9006c90fc49d524dce3b0668eb96cdad65a52e4877cf9c75`.
- **label-smoke** — exit `0`, 0.193s, UTC `2026-10-27T14:37:39.697100+00:00`.
  Command: `make smoke-demo`. [record](label-smoke.json), [log](label-smoke.txt).
  Sanitized log SHA-256: `be6147870901b36d75a5d3cf6104437dc132e4a59a3d36d799f9421326191a8c`.
- **label-web-build** — exit `0`, 5.556s, UTC `2026-10-27T14:38:43.429749+00:00`.
  Command: `env BUILDX_CONFIG=.cache/buildx docker compose build web`. [record](label-web-build.json), [log](label-web-build.txt).
  Sanitized log SHA-256: `36725d58ae158bcaf49ba410abb0e96832caa7229030842452999a6e89c14a4d`.
- **label-check-final** — exit `0`, 12.523s, UTC `2026-10-27T14:38:44.579651+00:00`.
  Command: `make check`. [record](label-check-final.json), [log](label-check-final.txt).
  Sanitized log SHA-256: `ddf69629ec1bd9ad1d1410cf8b8698439d6f37d48f61307ca49abc45f2a23da9`.
- **label-web-start** — exit `0`, 11.123s, UTC `2026-10-27T14:40:23.727602+00:00`.
  Command: `docker compose up --no-deps --no-build -d --wait --wait-timeout 60 web`. [record](label-web-start.json), [log](label-web-start.txt).
  Sanitized log SHA-256: `544a20d9b209692a1f37f50dcb440e60cd747fea0448f706d8b075f83f16fbf4`.
- **label-browser-collection** — exit `0`, 0.815s, UTC `2026-10-27T14:40:24.882915+00:00`.
  Command: `npm --prefix apps/web run test:e2e -- --list`. [record](label-browser-collection.json), [log](label-browser-collection.txt).
  Sanitized log SHA-256: `7ea23e94bd80ca11982801f619a9309eb83c18cb52879d2754eccd3f2d02f992`.
- **label-runtime** — exit `1`, 0.198s, UTC `2026-10-27T14:40:51.110660+00:00`.
  Command: `.venv/bin/python .cache/phase5/verify_label_bundle.py`. [record](label-runtime.json), [log](label-runtime.txt).
  Sanitized log SHA-256: `e090baca8c7b9ba288d93dea50e895ad837301232574ef3ee448477aea5c5a18`.
- **label-runtime-verified** — exit `0`, 0.308s, UTC `2026-10-27T14:41:06.838251+00:00`.
  Command: `.venv/bin/python .cache/phase5/verify_label_bundle.py`. [record](label-runtime-verified.json), [log](label-runtime-verified.txt).
  Sanitized log SHA-256: `6c65dc13563951d918139dde4ccc2e32a2d800db422d880ae6d625dff6b28894`.
- **label-preservation** — exit `1`, 4.39s, UTC `2026-10-27T14:41:07.183766+00:00`.
  Command: `.venv/bin/python .cache/phase5/preserve.py after`. [record](label-preservation.json), [log](label-preservation.txt).
  Sanitized log SHA-256: `8c7ba7889d541ed5fef5f57b5928727eba6274c4f9e8ed95017a26a2415222df`.
- **label-preservation-details** — exit `0`, 1.204s, UTC `2026-10-27T14:43:27.096352+00:00`.
  Command: `env PYTHONPATH=. .venv/bin/python .cache/phase5/label_preservation_details.py`. [record](label-preservation-details.json), [log](label-preservation-details.txt).
  Sanitized log SHA-256: `3ccfe0f01db35b682c33c768e47eefee4643ff4ee1b908579dee339589b32972`.
- **label-auth-history** — exit `0`, 0.164s, UTC `2026-10-27T14:44:06.961441+00:00`.
  Command: `docker compose exec -T postgres psql -U research -d research -Atqc 'SELECT event_type,timestamp FROM audit_events WHERE sequence > 5 ORDER BY sequence'`. [record](label-auth-history.json), [log](label-auth-history.txt).
  Sanitized log SHA-256: `6612ced9cbecffd6fb8be44f6a51660f2793f876b07f5cb97b7d982ba1aeddff`.
- **label-secrets** — exit `0`, 0.935s, UTC `2026-10-27T14:46:30.243646+00:00`.
  Command: `make secret-scan`. [record](label-secrets.json), [log](label-secrets.txt).
  Sanitized log SHA-256: `9512a08547cdbb5d978376019b4a76e59430750b6ae5580a7022fe7ed0dbcc46`.
- **label-repository** — exit `0`, 0.053s, UTC `2026-10-27T14:46:31.207347+00:00`.
  Command: `make repository-check`. [record](label-repository.json), [log](label-repository.txt).
  Sanitized log SHA-256: `d2320e85ae4a4178ffbc04155f02b9316a9d41c40e5f948d6fb6e5e4e75b8a9c`.
- **label-whitespace** — exit `0`, 0.029s, UTC `2026-10-27T14:46:31.288255+00:00`.
  Command: `git diff --check`. [record](label-whitespace.json), [log](label-whitespace.txt).
  Sanitized log SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
