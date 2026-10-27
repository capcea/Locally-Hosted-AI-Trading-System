# Phase 5.5A — Romanian product language

> Phase 5.5B implementation update (2026-10-27): this approved design is now the migration basis.
> See [implementation/acceptance report](PHASE55B_COMPLETION_REPORT.md) and
> [S01–S42 / U01–U24 traceability](docs/ux-migration-coverage.md). Source/native implementation is
> present; browser, visual-baseline and manual accessibility acceptance remain BLOCKED.
> Descriptions below remain the approved design targets; they are not evidence of rendered acceptance.

PROPOSED COPY, not application changes ·2026-10-27. Primary product locale:ro-RO.
Engineering documentation, API enums, exports, identifiers and diagnostic contracts remain exact.
Use copy keys rather than scattering strings across components. Preserve real source names and codes.
All braced terms below are runtime slots, not actual results. Never display unresolved template text.

## Voice and interpretation rules

Use short active sentences: what happened → why it matters → what happens next. Explain a technical
term once when needed; keep exact terminology in “Detalii tehnice”. Avoid promises such as “sigur”,
“profitabil”, “AI inteligent”, “se îmbunătățește singur” or “șansă garantată de câștig”.
A proposed design default is not an applied account policy. A successful simulation is not trading
permission. “Verified” must always say what was verified, for which scope and until when.

The “ten-year-old clarity” goal describes comprehension, not the audience or eligibility to trade.
Do not use childish badges, game rewards, simplified finance promises or a novice live-activation CTA.

## Navigation and screen titles

- nav.home: **Acasă** — “Starea platformei, testele tale și următorul pas.”
- nav.test: **Testează** — “Alege o strategie și verifică ce ar fi făcut pe datele selectate.”
- nav.results: **Rezultate** — “Vezi ce s-a întâmplat în testele finalizate.”
- nav.accounts: **Conturi și siguranță**; compact visual label **Conturi**, same full accessible name.
- nav.settings: **Setări** — “Securitate, surse de date și detalii despre platformă.”
- research.title: **Testează strategii**; historical wizard **Testează pe date istorice**.
- research.syntheticTitle: **Testează pe date sintetice** when that is the actual input source.
- progress.title: **Progresul testului**; activity.title: **Activitatea testelor**.
- result.title: **Rezultatul testului**; comparison.title: **Compară două teste**.
- data.title: **Date pentru teste**; data.origin: **De unde provin datele**.
- safety.title: **Siguranța contului**; risk.title: **Limitele aplicate în simulare**.
- audit.title: **Istoric verificabil**; diagnostics.title: **Starea serviciilor**.
- advanced.title: **Setări avansate**; raw.title: **Date tehnice originale**.

Do not rename a public API path or enum as part of copy migration. Current labels remain searchable in
technical help during transition, without hidden duplicate forms or contradictory accessible names.

## Home: purpose, state and next action

- home.available: “Platforma este disponibilă pentru funcțiile verificate mai jos.”
- home.running: “Testul «{nume}» este în lucru.”
- home.idle: “Nu rulează niciun test în acest moment.”
- home.unknown: “Nu putem verifica acum ce se întâmplă.”
- home.waiting: “Testul așteaptă un loc de calcul.” Only for a real queued job.
- home.attention: “Ai {număr} elemente de verificat.” Count actual authorized issues, not invented alerts.
- home.noIssues: “Nu sunt raportate probleme în datele verificate.” Not “Totul este sigur”.
- home.first: “Pregătește primul test”; body: “Ai nevoie de date admise și de limite revizuite.”
- home.ready: “Poți pregăti un test nou.” Eligibility is checked again before and during execution.
- home.recent: “Rezultate recente”; CTA “Vezi rezultatul”. Never aggregate unrelated backtests as wealth.
- home.stale: “Ultima verificare: {moment}. Informațiile pot fi depășite.”
- home.noHeartbeat: “Starea procesului de calcul nu este disponibilă.” Do not infer worker health.

Status vocabulary:
- Working/healthy → **Disponibil** for verified capability; actual job RUNNING → **În lucru**.
- Waiting → **În așteptare** plus actual reason.
- Needs attention → **Necesită atenție** plus consequence and next action.
- Unavailable → **Indisponibil**; unknown/unverified → **Nu putem verifica**.
- Not configured → **Nu este configurat**; not implemented → **Nu este disponibil în această versiune**.
- Disabled → **Dezactivat** only when it really is disabled, not an unknown connection.
- RETRY → **Se reia după întrerupere**; explain actual attempt without promising recovery.
- SUCCEEDED → **Test finalizat**; FAILED → **Test oprit din cauza unei probleme**; CANCELLED → **Test anulat**.

Execution mode, always separate from health:
**“SIMULARE · ordinele către brokeri externi sunt blocate.”**
Expanded: “Această versiune testează strategii. Nu trimite ordine reale sau demo către brokeri.”
Technical detail retains `SIMULATED`, `DENY_ALL`, `paper_eligible=false`.

## Data/source language: two axes, never one misleading badge

- SYNTHETIC_TEST_FIXTURE: **Date sintetice** — “Prețuri create pentru verificarea software-ului.
  Nu descriu evoluția reală a pieței.”
- USER_SUPPLIED: **Fișier furnizat de tine** — “Istoric declarat de sursă; originea și limitările
  sunt păstrate. Validarea fișierului nu certifică independent autenticitatea pieței.”
- PUBLIC_PROVIDER: **Date de la {furnizor}** — “Tip și interval: {detalii reale}. Drepturile și sursa
  sunt păstrate.” Do not call daily reference data tradable bid/ask observations.
- Demo-observed evidence: **Observație din cont demo · numai citire** — “Ultima observație semnată:
  {moment}. Aceasta nu permite trimiterea ordinelor.” Show signature/age status separately.
- Live-observed evidence: **Observație live · numai citire**, only if a future actual authorized
  read contract supplies it. **Unavailable now**; no live activation, balances or rows invented.
- Every backtest output: **Execuție simulată**, even when input history came from a real source.

Quality wording:
- VALID → “Date admise pentru utilizările permise.” Add actual coverage and required test eligibility.
- DEGRADED → “Date care necesită verificare. Le poți inspecta, dar nu le poți folosi pentru cercetare.”
- Rejected/quarantined → “Date blocate pentru utilizare”, using the real server status/reason.
- Pending validation → “Verificăm fișierul. Datele nu sunt încă disponibile pentru teste.”
- Unknown tick completeness → “Nu putem stabili dacă lipsesc tick-uri.” Never present100% completeness.
- Gaps → “Lipsesc observații în {interval confirmat}. Nu am completat prețuri lipsă.”
- Truncated preview → “Vezi un eșantion de {n} observații, nu întregul interval.”
- Coverage → “Interval observat: {început}–{sfârșit}. Istoricul dorit nu este presupus disponibil.”
- ECB → “Cursuri zilnice de referință. Nu includ bid/ask sau lichiditate pentru execuția ordinelor.”
- Seal restriction → “Această perioadă este rezervată evaluării finale. Accesul obișnuit este blocat.”

## Guided test: steps, help and confirmation

1. **Alege piața** — “Sunt afișate numai datele la care ai acces. Unele piețe pot necesita un import.”
2. **Alege strategia** — “Aceste strategii sunt etaloane experimentale, nu recomandări de investiții.”
3. **Alege perioada** — “Vom folosi numai informațiile disponibile la momentul fiecărei decizii.”
4. **Alege limitele revizuite** — “Limitele și regulile trebuie să fie valabile pentru cont și perioadă.”
5. **Verifică testul** — “Datele, costurile, riscul și regulile de evaluare vor fi fixate pentru acest test.”
6. CTA **Pornește testul în simulare**; after actual202: “Testul a fost înregistrat. Vezi starea lui în Activitate.”

Prerequisite help:
- No profile: “Contul nu are încă limite revizuite. Configurează-le înainte să pornești testul.”
- No reviewed default: “Nu există o configurație implicită revizuită pentru acest cont.”
- Missing contract/context: “Lipsesc informații despre contract, marjă sau calendar. Nu le presupunem.”
- Unsupported range/quota: “Intervalul poate depăși limita motorului. Verifică limita și restrânge
  perioada dacă este nevoie.” Use an exact refusal only after server confirmation, not an uncertain estimate.
- Costs: “Spread: {observat/modelat}; comision: {valoare declarată}; derapaj: {ipoteză}; finanțare: {stare}.”
- Screening: “Explorare rapidă. Acest model aproximativ nu verifică toate regulile de execuție și risc.
  Rezultatul trebuie verificat în motorul cu evenimente.”
- OHLC: “Execuția folosește bare de preț și ipoteze explicite despre mișcarea din interiorul barei.
  Ordinea exactă a prețurilor nu este cunoscută.”
- Random filter: “Păstrăm un procent din semnalele de intrare printr-o regulă aleatorie reproductibilă.
  Acesta este un control de comparație, nu o judecată AI.”

Review acknowledgement text must reflect the actual API acknowledgements, including isolated account/
policy clone, research-only scope and cost/bar assumptions. Suggested plain wording:
“Confirm folosirea configurației revizuite într-un cont separat de simulare.”
“Înțeleg costurile și ipotezele afișate. Testul nu permite ordine externe sau promovare automată.”
Do not precheck, combine away a mandatory acknowledgement or replace server validation with this text.

Strategy display names, keeping exact IDs/version in details:
- EMA_TREND → **Urmărirea tendinței cu media exponențială**: “Testează intrări când prețul și media
  indică aceeași direcție, pe observațiile deja disponibile.”
- MA_CROSS → **Încrucișarea mediilor**: “Testează schimbări de direcție între o medie rapidă și una lentă.”
- DONCHIAN → **Depășirea intervalului recent**: “Compară închiderea cu limitele observate anterior.”
- BOLLINGER → **Revenire spre media prețului**: “Testează reveniri după abateri față de intervalul anterior.”
- RSI → **Revenire după mișcări accentuate**: “Folosește un indicator al variațiilor recente, nu o predicție sigură.”
- ATR_BREAKOUT → **Mișcare peste variația recentă**: “Testează depășiri raportate la variația observată anterior.”
- OPENING_RANGE → **Depășirea intervalului de deschidere**: “Testează ieșiri din intervalul observat la începutul sesiunii.”
- SESSION_MOMENTUM → **Direcția prețului în sesiune**: “Compară prețul cu observația de la începutul ferestrei declarate.”

## Results and statistics

- Positive stored net: **Câștig net al simulării**; negative: **Pierdere netă a simulării**.
- Neutral heading: **Modificarea netă a capitalului simulat**. Unknown: “Nu poate fi stabilită”, not zero.
- **Cea mai mare scădere** — “Cea mai mare coborâre a capitalului simulat de la un vârf anterior,
  în acest test. Nu este o limită a pierderilor viitoare.”
- **Tranzacții încheiate** — distinguish round trips from orders, fills and open positions.
- **Costuri declarate** — “Rezultatul include {componente confirmate}. {cost necunoscut} nu este verificat.”
- **Perioadă de descoperire** — “Date folosite pentru explorarea ideii.”
- **Perioadă de calibrare** — “Date folosite la alegerea setărilor.”
- **Validare pe o perioadă ulterioară** — “Evaluare după perioada de pregătire, conform împărțirii fixate.”
- **Evaluare finală autorizată** — separate controlled release, not a synonym for any OOS run.
- **Ce știm din acest test** / **Ce nu putem concluziona** — replace an unimplemented “passed” verdict.
- Small sample: “Sunt prea puține observații pentru acest indicator. Rezultatul afișat nu demonstrează
  că strategia va funcționa în viitor.” Use the stored reason/sample, not a universal invented threshold.
- Irregular days: “Lipsesc zile din seria observată. Indicatorii anualizați nu sunt afișați.”
- Undefined denominator: “Indicatorul nu poate fi calculat pentru acest eșantion.” No infinity badge.
- Bootstrap: “Interval obținut prin reeșantionarea tranzacțiilor observate, cu ipotezele afișate.
  Nu reprezintă probabilitatea de a câștiga bani în viitor.” Preserve actual level/method/seed in details.
- Multiple testing: “Au fost încercate {n} configurații, inclusiv cele eșuate sau anulate. Configurațiile
  asemănătoare nu sunt automat observații independente.”
- DSR: “Ajustare avansată pentru selecție repetată și distribuția randamentelor. Depinde de ipotezele
  declarate despre independență; nu conferă eligibilitate pentru tranzacționare.”
- Comparison mismatch: “Aceste teste nu au condițiile necesare pentru o comparație directă. Vezi
  datele, perioada, costurile, riscul și versiunea software.” Only name a specific mismatch if supplied.
- No AI: “Filtrele ML/LLM nu sunt disponibile în această versiune.” No empty simulated AI series.
- Result footer: “Rezultat istoric simulat. Nu este o promisiune, un sold real sau o aprobare de tranzacționare.”

## Progress, empty and cancellation states

- Loading: “Încărcăm {datele/starea/rezultatul}…”; retain unknown until response, not0/green defaults.
- No experiments: “Nu ai încă teste înregistrate.” CTA “Pregătește primul test”.
- No completed results: “Nu există încă rezultate finalizate. Vezi testele în lucru.”
- Filtered-empty: “Niciun rezultat nu corespunde filtrelor.” CTA “Șterge filtrele”.
- Missing data: “Nu există date admise pentru această alegere.” CTA “Vezi datele sau adaugă un import”.
- Empty comparison: “Alege două teste finalizate cu condiții compatibile.”
- Empty audit: “Nu există evenimente în intervalul la care ai acces.” Do not infer global inactivity.
- Cancel CTA: “Solicită anularea”; acknowledgement: “Anularea a fost cerută. Așteptăm confirmarea.”
- Confirmed cancellation: “Test anulat. Nu există un rezultat complet publicat pentru acest test.”
  Show this only if no result exists; a completion race displays the actual completed state instead.
- Retry after crash: “Procesul a fost întrerupt. Se reia aceeași configurație fixată, încercarea {n}.”
- Ambiguous create: “Nu putem confirma răspunsul. Verifică Activitatea înainte de a trimite un test nou.”
- Duplicate acknowledged: “Acest test era deja înregistrat. Am deschis starea lui.” Only after same-ID response.

## Risk and emergency wording

- **Capital declarat pentru simulare** — “Nu este soldul unui cont de broker.”
- **Limită pe tranzacție** — “Limita pentru riscul estimat al unei propuneri; calculul exact include
  condițiile declarate. Golurile de preț și execuția pot produce rezultate diferite.” No guaranteed cap.
- **Limită zilnică** / **Limită totală** — always show currency, exact basis/static/trailing and reset zone/time.
- **Risc deja alocat** — “Include poziții, ordine în așteptare și expunerea care nu este încă lămurită.”
- **Intrări oprite** — “Nu se acceptă intrări noi în simulare. Pozițiile existente nu sunt închise automat.”
- **Stare necunoscută** — “Nu putem verifica acum limitele sau expunerea. Nu presupunem că există capacitate.”
- **Document verificat** — “Sursa a fost revizuită pentru contul, programul și perioada afișate.”
- **Politică aplicată în simulare** — show its actual version and exact scope, not brand-wide permission.
- **Înregistrare descriptivă** — “Această înregistrare nu aplică limite la teste.” For legacy metadata.
- What-if ALLOW → “Propunerea respectă aceste verificări de simulare. Nu a fost trimis niciun ordin.”
- DENY → “Propunerea nu este permisă de limitele verificate.” Show actual reason.
- INDETERMINATE → “Nu avem suficiente informații verificate pentru a permite propunerea.”

STOP review: “Oprești intrările noi pentru {cont}. Pozițiile simulate existente nu se închid prin
această comandă.” CTA **Oprește intrările**. Success only after response: “Intrările noi sunt oprite
pentru {cont}.” Failed/unknown: “Oprirea nu a fost confirmată. Nu presupune că starea s-a schimbat.”

CLEAR review: **Revizuiește înainte de deblocare** — “Datele, limitele și politica trebuie verificate
înainte de a permite din nou intrări simulate.” CTA after checks/MFA: **Confirmă deblocarea intrărilor**.
No automatic clearing, acknowledgement by silence or suggestion to loosen a cap.

FLATTEN review: **Închide pozițiile simulate** — “Solicitarea se aplică numai contului {cont}.
Închiderea poate rămâne incompletă dacă lipsesc cotații sau lichiditate. Nu închide poziții reale.”
Acknowledgement: “Confirm că solicit închiderea pozițiilor simulate ale acestui cont.”
Partial outcome: “Închidere incompletă: {n} poziții simulate rămân deschise. Vezi motivele verificate.”
No message “totul închis” from an accepted request alone. MONITOR → **Actualizează starea riscului**.

## Identity, security and final evaluation

- Login password step: “Autentifică-te”; MFA step: “Introdu codul din aplicația de autentificare.”
- Recent MFA: “Confirmă din nou identitatea pentru această acțiune sensibilă. Setările neconfidențiale
  rămân în draft. Acțiunea nu este trimisă automat după confirmare.”
- Enrollment: “Adaugă acest cont în aplicația de autentificare. Scanează codul QR sau folosește cheia manuală.”
  QR is a proposed local rendering, not currently claimed implemented.
- Recovery: “Păstrează codurile într-un loc sigur. Fiecare poate fi folosit o singură dată împreună cu parola.”
- Session revoke: “Vei fi deconectat de pe toate sesiunile, inclusiv aceasta.”
- Role/access change: “Verifică persoana, rolul și sesiunile afectate înainte să confirmi.”
- Audit integrity success: “Lanțul de evenimente verificat este intact până la secvența {n}.”
- Audit limit: “Verificarea nu elimină încrederea acordată gazdei și administratorilor care dețin cheia.”
- Final seal: **Rezervă o perioadă pentru evaluarea finală** — “Accesul obișnuit la perioada protejată
  va fi restricționat, inclusiv prin seturi suprapuse ale aceluiași proprietar.”
- Prior exposure: **Expunere anterioară necunoscută** — “Nu putem certifica faptul că datele nu au fost văzute.”
- Final release: **Autorizează o singură evaluare finală** — “Strategia, datele, setările și regulile
  afișate vor fi fixate. Nu poți repeta evaluarea pentru a regla strategia și a pretinde independență.”
- No post-release eligibility: “Evaluarea rămâne simulată și nu permite promovarea automată.”

## Error catalog: what happened / why it matters / next step

Use these mappings only for known safe codes/conditions. Keep exact original code and correlation in
advanced diagnostics; never concatenate arbitrary server messages, DSNs, tokens or uploaded contents.
Messages are proposed UI translations, not new API enums. Unknown errors stay generic and actionable.

- 401: “Sesiunea nu mai este valabilă. Datele protejate nu pot fi reîncărcate. Autentifică-te din nou.”
- 403: “Acțiunea nu este permisă în starea curentă. Verifică rolul și confirmarea identității.” Do not
  assert MFA is the only cause; backend RBAC/CSRF/ownership still decides.
- 404: “Nu putem afișa această înregistrare. Verifică legătura și contul selectat.” No other-owner leak.
- 409 generic: “Datele sau condițiile s-au schimbat. Reîncarcă informațiile și revizuiește acțiunea.”
- 413: “Fișierul depășește limita permisă. Vezi limita afișată și pregătește un fișier admis.”
- 422: “Unele date introduse nu sunt valide. Verifică câmpurile indicate în detalii.” Indicate actual
  safe field errors only if available; otherwise say “Verifică datele introduse”.
- 429: “Au fost prea multe cereri. Reîncearcă după intervalul indicat.” If absent, “Reîncearcă mai târziu”; no invented timer.
- 503 on a read: “Serviciul necesar nu răspunde. Păstrează draftul și încearcă să reîncarci informațiile.”
  On an uncertain submission: “Nu putem confirma dacă solicitarea a fost înregistrată. Verifică
  activitatea înainte de a trimite din nou.” Reconcile using the actual endpoint's submission identity;
  do not encourage a new financial mutation merely because the response was unavailable.
- DATASET_ACCOUNT_SCOPE_MISMATCH: “Datele și configurația nu aparțin aceluiași cont permis. Alege date compatibile.”
- DATASET_NOT_VALID_OR_PIN_CHANGED: “Datele nu mai corespund versiunii admise. Verifică setul și versiunea.”
- DATASET_MANIFEST_REGISTRY_MISMATCH: “Integritatea datelor nu poate fi confirmată. Testul nu poate continua.”
- FUTURE_OR_UNAVAILABLE_MARKET_OBSERVATION / BAR_HIGH_LOW_NOT_YET_AVAILABLE: “Datele conțin informații
  indisponibile la momentul deciziei. Nu le folosim pentru a produce un rezultat favorabil.”
- INSUFFICIENT_ADMITTED_WARMUP: “Lipsesc observații anterioare necesare strategiei. Alege o perioadă cu pregătire suficientă.”
- RESEARCH_MARGIN_UNVERIFIED: “Marja necesară nu este verificată. Revizuiește configurația contului; nu o presupunem.”
- REPLAY_SYMBOL_OR_CALENDAR_UNVERIFIED: “Simbolul sau calendarul nu corespunde datelor admise. Revizuiește sursa și contractul.”
- AUTOMATED_RESEARCH_REQUIRES_EXPLICIT_VERIFIED_POLICY_PERMISSION: “Politica verificată nu permite
  explicit această strategie automatizată. Nu o putem declara manuală pentru a continua.”
- SOURCE_POLICY_VERSION_CHANGED / SOURCE_RISK_PROFILES_CHANGED / SOURCE_RISK_APPROVAL_REVOKED:
  “Regulile revizuite s-au schimbat. Testul nu mai poate folosi aprobarea veche. Verifică noua configurație.”
- RESEARCH_SOFTWARE_VERSION_CHANGED: “Versiunea software nu mai este cea fixată pentru test. Revizuiește o rulare nouă.”
- FINAL_HOLDOUT_ACCESS_DENIED: “Perioada este protejată pentru evaluarea finală. Folosește fluxul separat de autorizare.”
- ENTRY_RISK_INDETERMINATE with known safe reason: “Riscul nu poate fi verificat complet. Testul se oprește
  fără rezultat acceptat. Vezi informația lipsă.” Do not reveal an unvalidated arbitrary suffix.
- Generic failed job: “Testul s-a oprit. Nu publicăm rezultate incomplete. Vezi motivul și următorul pas.”

## Terminology glossary — beginner label → exact technical meaning

- Backtest → Test pe date istorice; execution is still simulated, regardless of data source.
- Strategy Lab → Testează strategii; reviewed fixed registry, not AI code generation.
- Dataset → Set de date; immutable version with owned scope, manifest and availability facts.
- Provenance → De unde provin datele; provider/source, rights, hashes, transformations and dates.
- Instrument → Piață/instrument, with exact symbol/class in details; not a tradability claim.
- SymbolSpec → Specificația instrumentului; exact tick/grid/contract/currency and validity evidence.
- Tick → Cotație individuală; not a guessed price between bars.
- OHLC → Bară de preț; opening/high/low/close at declared availability, with intrabar uncertainty.
- Timeframe → Interval al observațiilor; M1=1minut, H1=1oră; tick stream is not a fixed interval.
- Available at → Disponibil pentru decizie la; distinct from event/observation timestamps.
- UTC/IANA/DST fold → Ora exactă și fusul sursei; advanced conversion must remain unambiguous.
- Spread → Diferența dintre prețul de cumpărare și vânzare; observed or explicitly modeled.
- Slippage → Diferență de preț la execuție; declared model, not assumed historical observation.
- Funding/swap → Cost sau ajustare de finanțare; unknown is not zero.
- Simulation template → Configurație revizuită de simulare; cannot create policy approval by itself.
- Risk profile → Limite aplicate în simulare only for enforced versions; legacy metadata is descriptive.
- Risk Gateway → Verificarea independentă a riscului; final deterministic authority, not an AI opinion.
- Risk reservation → Risc deja alocat; includes pending and unresolved commitments.
- Headroom → Marjă disponibilă până la limită; unknown is not available capacity.
- Margin → Marjă cerută pentru poziție; distinguish from remaining risk headroom.
- Max Drawdown → Cea mai mare scădere; peak-to-subsequent-equity decline, not future worst-case loss.
- Net expectancy → Rezultat mediu net pe tranzacție; descriptive sample average.
- Profit factor → Raport câștiguri/pierderi din eșantion; undefined without an appropriate denominator.
- Sharpe/Sortino/Calmar → exact metric name + short assumption/sample explanation; no marketing rename.
- Bootstrap/block bootstrap → Reeșantionare / reeșantionare în blocuri; uncertainty under declared assumptions.
- Monte Carlo trade sequence → Reordonarea tranzacțiilor observate; no new independent market history.
- In-sample → Date folosite la pregătire; not an independent future test.
- Out-of-sample → Perioadă ulterioară de evaluare conform protocolului; not automatically untouched.
- Walk-forward → Pregătire și evaluare pe ferestre succesive; preserve real train/OOS boundaries.
- Purge/embargo → Separare pentru a evita suprapunerea informației; exact intervals remain visible.
- Holdout → Perioadă rezervată evaluării finale; UNKNOWN prior exposure remains explicit.
- Trial → Configurație încercată; not necessarily statistically independent.
- Job/run → Rulare înregistrată; attempt → Reluare după întrerupere of the same frozen scope.
- Idempotency key → Identificator pentru evitarea duplicării; generated internally, inspectable in details.
- ALLOW/DENY/INDETERMINATE → Permis / refuzat / nu poate fi stabilit for this simulated proposal.
- Fill/partial fill → Execuție simulată / execuție parțială; a permission or order is not yet a fill.
- UNKNOWN → Stare nelămurită; retain exposure until actual reconciliation, not optimistic cancellation.
- STOP_NEW_ENTRIES → Oprește intrările noi; does not close existing positions.
- FLATTEN → Închide pozițiile simulate; separate scope, MFA and possible incomplete outcome.
- CLEAR_STOP → Deblochează după revizuire; not automatic recovery.
- DENY_ALL → Ordine externe blocate; not a toggle or temporary lack of broker credentials.
- MFA → Confirmarea identității în doi pași; do not simplify away a factor.
- RBAC → Drepturi în funcție de rol; ownership isolation is an additional independent boundary.
- HMAC/audit chain → Istoric verificabil; trusted-host/key limitations still apply.
- Immutable → Păstrat fără rescriere; reruns and revisions create separate evidence, not edited history.

## Content acceptance

Review glossary with the owner and representative adult novice/advanced users later. Test whether they
can distinguish result from permission, decline from future-loss cap, source quality from authenticity,
ALLOW from fill, STOP from FLATTEN and OOS from untouched final evaluation. No such study is claimed now.
Copy changes may intentionally change Playwright locators; preserve the behavior assertions and exact
accessible-name tests instead of loosening assertions to tolerate contradictory labels.

## Applied copy migration

copy/ro.ts centralizes primary source/job/phase/strategy/error dictionaries; exact API terms stay in
advanced contracts. Intentional selector migrations: Cont sursă verificat → Contul testului;
Configurează backtest → Configurează testul istoric; accessible research region → Testează strategii;
Capital de referință → Capital declarat pentru simulare. These changes do not attest an account merely
because it appears in a selector. Original behavioral assertions are retained under the new names.
