# Broker adapter contracts — Phase 3

Updated 2026-10-27. External execution is DENY_ALL. This document describes implemented source,
not certification of external brokers. Actual MT5/cTrader connections are BLOCKED: no authorized
Windows terminal, registered cTrader application or demo credentials were supplied or used.

## Shared contract and trust boundary

`packages/brokers/contracts.py` defines BrokerAdapter, BrokerSymbol, BrokerSnapshot, SnapshotRequest
and SignedObservation. `packages/execution/contracts.py` defines exact symbol/order/position/fill
and future risk contracts. These depend on shared data contracts, never a venue SDK or API identity
module. SDK code exists only in the optional `services/broker_bridge` deployment. The primary
application image excludes that directory and does not install MetaTrader5. No broker credentials
are accepted by the primary API or UI. No generated strategy source is executed.

ReadOnlyAdapter's submit/cancel/modify operations raise ExternalExecutionDenied. This applies to
SimulatorAdapter's external interface too; synthetic state changes use separate journaled engine
commands. MT5 exposes only explicitly coded SDK reads; cTrader transmits a fixed read-message
allowlist to a fixed demo endpoint. Neither bridge HTTP service exposes order routes. Both primary
legacy order/live routes and connection-specific external order routes refuse execution.

Only SIMULATED and DEMO_READ_ONLY are accepted modes. DEMO_EXECUTION/LIVE are unavailable in schema,
configuration, API and UI. Future risk results/reservations/execution results have false authority
fields. No environment variable authorizes trading and no placeholder grants risk approval.

## Metadata and observed truth

BrokerRuntime extends the existing BrokerConnection by its owned ID, rather than duplicating the
account registry. Owner plus recent MFA pins provider, external account, server and Ed25519 public
key. Identity fields are immutable in PostgreSQL. Snapshot import requires owner MFA, matching
identity/signature, bounded age and increasing source sequence. Exact duplicate packets deduplicate;
conflicting repeats, gaps or changed order/position truth produce explicit uncertainty/incidents.
Read-only reconciliation never submits an order or invents fills. History is bounded and explicitly
incomplete. Capability fields that were not retrieved remain null/empty, tradability_verified=false.

The central integration currently accepts an owner-uploaded signed observation JSON packet; it does
not automatically poll the external bridge. `/snapshot` performs a bounded read only when invoked
on an independently configured bridge. Continuous central synchronization is NOT IMPLEMENTED.
Fixtures retain CONTRACT_FIXTURE/FIXTURE_ONLY status; they cannot establish a successful demo link.
Balances shown as observed require BROKER_OBSERVED provenance. Source timestamps, age, latency,
reconnect and authorization restrictions are exposed to the Romanian Broker Control Center.

## MT5

`services/broker_bridge/mt5.py` imports the official MetaTrader5 module only on Windows. It requires
explicit authorized demo reads, the exact pinned login/server, demo trade mode, investor/read-only
account authorization and terminal API trading disabled. Identity is checked before and after the
read. Reads cover account/terminal, requested symbol metadata/ticks, orders, positions and at most
seven days/500 history records. SDK floating values are converted through Decimal(str(value)); this
preserves the SDK's reported precision, not precision the SDK did not provide. Unknown sessions,
margin and unsupported metadata are not synthesized. Shutdown runs in finally.

`services/windows/service.py` supplies an optional SCM host with a dedicated Python environment,
kill-on-close process Job and memory limits. The parent bridge terminates a read child after 30s.
Windows installation, terminal interaction, NTFS ACLs and Job behavior are NOT TESTED on Windows.
Contract tests inject a fake SDK and explicitly mark their source CONTRACT_FIXTURE.

## cTrader

`services/broker_bridge/ctrader.py` implements official Open API JSON envelopes over TLS WebSocket
at `wss://demo.ctraderapi.com:5036`. It does not accept arbitrary endpoints or live endpoints. Scope
must be verified SCOPE_VIEW (integer 0 or exact name); an absent scope, bool, float or trading scope
is refused. The selected account must explicitly report isLive=false and match the pinned identity.
Typed client-message correlation, duplicate old replies, bounded frames/event buffering, scoped
account responses, revocation/errors and malformed messages fail safely. Integer prices and volume
units are converted exactly. Quote snapshots require dated two-sided data.

The transport sends heartbeat messages every ten idle seconds, limits ordinary/history requests
separately and retries read connections at most three times with bounded backoff. Permission failure
is not retried. Whole-read process timeout remains authoritative. OAuth requests the accounts scope,
uses one-use expiring random state and the official token endpoint; token refresh is implemented.
OAuth exchanges in tests use MockTransport, not actual account authorization.

`security.py` stores access/refresh tokens only in an encrypted private atomic file on the connector
host, with a separate key and private-file checks (0600 on POSIX; explicit ACL verification on Windows).
HTTP client logging is suppressed during token exchange because the official token flow uses query
parameters. Credentials never appear in central responses or observation packets.

## Private transport and bounds

`app.py` serves loopback-only HTTPS with required client certificates plus an independent bearer
service identity. Health/public-key/snapshot/OAuth-start require the bearer. The OAuth callback uses
mTLS plus one-use OAuth state instead of a bearer header, as a browser redirect. All POST bodies are
bounded to 16KiB; one read/OAuth exchange runs at a time. SDK reads run in spawned children with a
30s deadline. Linux CPU/memory limits and Windows service Job limits bound resources. This is trusted
fixed adapter code, not a hostile-code sandbox. Signed packets are bounded again by the primary API.

Local real TLS tests exercise the actual bridge server, reject a missing client certificate, reject
certificate-only requests without bearer, accept authenticated health and find no order endpoint.
These tests prove local service authentication, not an actual broker connection.

See [capability matrix](BROKER_CAPABILITIES.json), [simulator](EXECUTION_SIMULATOR.md),
[state machine](ORDER_STATE_MACHINE.md) and [controlled setup/runbook](BROKER_RUNBOOK.md).
