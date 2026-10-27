# Broker failure, reconciliation and controlled read-only setup

Phase 3 permits synthetic execution and authorized demo reads only. No credentials were supplied,
no broker account was connected and no real/demo order was sent during implementation. Instructions
below are for a future separately authorized private environment, not actions already performed.

## Synthetic incidents

1. Inspect the owned run's journal, current sequence/digest and original command receipt. Verify
   integrity; a failed chain or snapshot check requires incident investigation, not resetting history.
2. BEFORE_SUBMIT is a known refusal. AFTER_SUBMIT/DELAY_ACK produces UNKNOWN. Do not change the key,
   blindly resubmit or interpret timeout as rejection. New submissions are blocked while UNKNOWN.
3. Restore modeled connectivity, then explicitly reconcile. Only durable synthetic broker truth can
   clear uncertainty. Missing truth remains UNKNOWN. Record an incident; do not edit SQL snapshots.
4. For an interrupted client request, retry the exact same key and payload. Inspect original_receipt
   and the current state, which may include later commands. Different payload with the same key fails.
5. After a process/database restart, load and verify the journal before continuing. Investigate
   duplicate/out-of-order quotes, expired specs, unavailable sessions and stale data as refusals.

No external order reconciliation or flatten is authorized. Existing broker orders are observed only;
use the broker's independently authorized owner interface to manage them outside this platform.

## External observation problems

Reject mismatched account/server/provider/key, stale/future packets and invalid signatures. Exact
signed duplicates deduplicate; conflicting sequence reuse is refused. Sequence gaps and changed
orders/positions raise UNKNOWN/incidents. Reauthorize on the connector host if access is revoked;
never copy tokens into the central API. A stale/unverified/fixture connection is not an execution
permission. History is incomplete, so an absent deal is not proof an order never existed.

## Future controlled MT5 setup — actual acceptance BLOCKED

Use an authorized Windows demo terminal and dedicated service identity. Keep credentials in the
terminal's own private configuration. Require investor/read-only access, terminal API trading disabled,
correct demo trade mode, exact account login and server. Do not use a real-money terminal.

Install the pinned Python environment on that Windows host:

```powershell
uv sync --frozen --no-dev --extra windows-bridge
.venv\Scripts\python.exe -m services.windows.service --help
```

Privately provision `C:\ProgramData\AITradingReadOnlyBridge\bridge.json` and its files according to
`services/broker_bridge/app.py:BridgeConfig`: authorized_demo_reads=true, provider MT5, connection UUID,
pinned account/server, authorization_token_file, Ed25519 signing_key_file, tls_cert, tls_key and
client_ca. Signing key is 32 raw Ed25519 private bytes; bearer identity must have at least 256 bits
of entropy. Restrict config, keys and token files to the service SID, SYSTEM and local administrators;
run `services/windows/verify-private-acl.ps1` as the service identity. Do not paste config into issues.
The service uses this fixed config path; its dedicated .venv must be beside the project source.

Only after private certificate issuance, ACL review and explicit owner read authorization, install
and start the SCM service through `python -m services.windows.service install` / `start` using its
dedicated account. The listener binds 127.0.0.1:18443, requires client certificate and bearer identity.
Use a private authenticated channel/tunnel from the owner-controlled client. Do not expose a public
port or disable certificate verification. Actual Windows SCM/ACL/Job/SDK operation still needs testing.

## Future controlled cTrader setup — actual acceptance BLOCKED

Register an application and HTTPS callback with the official cTrader Open API. Store client ID/secret,
TokenVault file/key and bridge config privately on the independent connector host. Use provider
CTRADER, pinned authorized demo account/server, client_id/client_secret/oauth_redirect/token_file/
token_key_file in addition to the common private transport/signing fields. Keep the account scope
`accounts`; an actual verified SCOPE_VIEW response and isLive=false are mandatory. Do not grant trading
scope, use a live endpoint or loosen scope validation if the response differs.

A local independently built image is available:

```sh
docker build -f services/broker_bridge/Dockerfile -t ai-trading-readonly-bridge:phase3 .
docker run --rm --network none --read-only ai-trading-readonly-bridge:phase3 --help
```

The help command does not configure a service or validate a broker connection. A future actual service
needs private secret-file mounts, validated certificates, scoped egress to official demo/OAuth hosts,
resource limits and an owner-controlled loopback listener/tunnel. No compose service is enabled.
Use authenticated `/oauth/start`, follow its one-use authorization URL and callback over mTLS. The
callback uses mTLS and one-use state (no bearer header); private responses never return OAuth tokens.
Use authenticated `/snapshot` with the pinned identity and strictly increasing sequence. Import the
resulting signed packet through the owner's recent-MFA Broker Control Center. Central continuous
polling/automatic transport is not implemented. Configure supervision for bounded failed reads;
revocation/unsafe scope must stop reads, not trigger permissive retries.

## Required external evidence before marking connectivity PASSED

Record redacted actual service identity/environment, timestamps, read-only authorization scope,
account/server matching, symbol unknowns, quote age, order/position/history observations, reconnect,
revocation, timeout and shutdown behavior. Test certificate rejection and no-order endpoints. Keep
raw credentials/tokens/terminal screenshots private. Simulator, MockTransport and fake SDK evidence
must remain distinct. This procedure never authorizes DEMO_EXECUTION or LIVE.

## Local acceptance and cleanup

```sh
make check
make smoke-demo
make integration
E2E_ONLY_PROJECT=desktop E2E_ONLY_SCENARIO=broker make browser-integration
env -u E2E_ONLY_PROJECT -u E2E_ONLY_SCENARIO make browser-integration
```

Use `P0_CACHED_IMAGES=1` only when exact pinned service images are already cached. Set
PLAYWRIGHT_BROWSERS_PATH to the installed authorized browser cache if required. The harness owns
unique disposable projects, random private credentials and ephemeral 127.0.0.1 ports; it cleans up
only those projects. Never run `docker compose down --volumes` on the development stack. Do not
bypass a managed Chromium denial; move validation to an environment where its administrator permits it.
