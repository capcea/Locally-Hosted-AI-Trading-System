"""Versioned implementation roadmap; planned services are never reported as connected."""

from packages.domain.contracts import Phase, ServiceHealth, ServiceStatus

ROADMAP = [
    Phase(
        number=0,
        title="Fundație & securitate",
        status="CURRENT",
        acceptance=("Fundație implementată; acceptarea completă depinde de dovezi CI/browser."),
    ),
    Phase(
        number=1,
        title="Identitate & audit",
        status="CURRENT",
        acceptance=(
            "Identitate, MFA și audit persistente implementate; verificarea browser este necesară."
        ),
    ),
    Phase(
        number=2,
        title="Date & corectitudine temporală",
        status="CURRENT",
        acceptance=("Importuri versionate și teste UTC/DST; acceptarea browser este necesară."),
    ),
    Phase(
        number=3,
        title="Simulare & brokeri demo",
        status="CURRENT",
        acceptance=(
            "Simulator și jurnal implementate; conectarea externă și browserul necesită dovezi."
        ),
    ),
    Phase(
        number=4,
        title="Risc & politici prop",
        status="CURRENT",
        acceptance=(
            "Gateway SIMULATED, rezervări atomice și politici; acceptarea browser necesită dovezi."
        ),
    ),
    Phase(
        number=5,
        title="Motor de backtesting",
        status="CURRENT",
        acceptance="Replay determinist, costuri, OOS, walk-forward și incertitudine.",
    ),
    Phase(
        number=6,
        title="Gateway AI & agenți",
        status="PLANNED",
        acceptance="Ollama privat, scheme validate, cote și execuție izolată.",
    ),
    Phase(
        number=7,
        title="Cercetare autonomă & ML",
        status="PLANNED",
        acceptance="Experiment reproductibil, comparații cu baseline și teste de leakage.",
    ),
    Phase(
        number=8,
        title="Paper trading",
        status="PLANNED",
        acceptance="Observație adaptivă, gate-uri statistice și aprobări imuabile.",
    ),
    Phase(
        number=9,
        title="Operațiuni & alerte",
        status="PLANNED",
        acceptance="Control mobil securizat, notificări, recuperare și backup verificat.",
    ),
    Phase(
        number=10,
        title="Cloud → local",
        status="PLANNED",
        acceptance="Migrare reversibilă și revizuire manuală înainte de orice activare live.",
    ),
]

PLANNED_SERVICES = [
    ServiceHealth(
        id="mt5",
        name="MetaTrader 5",
        status=ServiceStatus.PENDING_IMPLEMENTATION,
        detail="Adaptor Windows read-only implementat; conectarea reală nu este verificată.",
    ),
    ServiceHealth(
        id="ctrader",
        name="cTrader Open API",
        status=ServiceStatus.PENDING_IMPLEMENTATION,
        detail="Adaptor Linux read-only implementat; conectarea reală nu este verificată.",
    ),
    ServiceHealth(
        id="ollama",
        name="Ollama · Qwen",
        status=ServiceStatus.NOT_CONFIGURED,
        detail="Gateway privat planificat în faza 6. Nicio inferență activă.",
    ),
    ServiceHealth(
        id="executor",
        name="Executor de ordine",
        status=ServiceStatus.DISABLED,
        detail="DENY_ALL. Trimiterea ordinelor este refuzată în cod.",
    ),
]
