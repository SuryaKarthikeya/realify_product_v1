"""Your Category Analyst — typed card-kind contracts + the synthesis SEAM.

Positioning: this is NOT a research tab of data widgets. It's an analyst that did the work overnight
and shows up with a memo + a ranked shortlist of moves. Synthesis leads; data threads are the
drill-down. So every section is modeled as "one-line synthesis + a recommended move + evidence".

This module defines ONLY the contract (dataclasses) and the seam. It computes no metrics itself —
L1 owns the numbers; the analyst service (future) fills these in. The client renders these shapes
verbatim and never fabricates a value. Serialize with `to_public()`.

Provenance is first-class: every reported number carries a Provenance tier. `official` = your own
data / official APIs (Keepa, gov feeds); `scraped` = competitor/marketplace scrape, DIRECTIONAL and
rendered visually distinct so it is never forwarded as fact.

SYNTHESIS SEAM: `synthesize_category_analyst(tenant_id, category, price_band)` is the single function
the future analyst service implements. Today it returns a typed fixture (see analyst_fixture.py).
TODO(analyst-service): replace the fixture body with real synthesis on top of the 1a/1f card
pipeline + the net-new synthesis service; keep reads on the repository/deps path; expose via /api/v1.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# ---- provenance tiers (non-negotiable UI concept) --------------------------
OFFICIAL = "official"          # your own data / official APIs — safe to state as fact
SCRAPED = "scraped"            # competitor/marketplace scrape — directional only, badge it
ESTIMATED = "estimated"        # modelled/estimate — directional, badge it "est."
TIERS = {OFFICIAL, SCRAPED, ESTIMATED}

# ---- per-section DATA STATE (Phase 1 contract — the client never guesses real vs synthetic) -------
# live    = every number in the section is real tenant/L1 data
# partial = section renders, but named sub-fields are unavailable (field_state="coming")
# fixture = synthetic; a REAL tenant must see the coming-state, never fixture numbers (exposure gate)
LIVE, PARTIAL, FIXTURE = "live", "partial", "fixture"
STATES = {LIVE, PARTIAL, FIXTURE}
COMING = "coming"              # a sub-field's field_state when it isn't built yet (not zero, not null)


@dataclass
class Provenance:
    tier: str                  # OFFICIAL | SCRAPED
    source: str                # e.g. "Keepa", "your catalog", "competitor listing"
    note: str = ""             # e.g. "directional" for scraped figures


@dataclass
class Metric:
    """A single number the analyst reports. Pre-formatted server-side (₹/%/rank); the client renders
    `value` as-is and never recomputes. Every metric carries provenance. `field_state="coming"` marks a
    sub-field not built yet (value is a placeholder "—", never a fabricated/zero number). `explain` is
    the shared realify.domain.explain part shape so the metric plugs into the same explain_mode ⓘ."""
    label: str
    value: str
    prov: Provenance
    field_state: str = ""                   # "" = live; "coming" = unavailable this phase
    explain: Optional[dict] = None          # explain.part(...) shape → renderExplain ⓘ


@dataclass
class Move:
    """A recommended play — also the unit of the decision→outcome loop (status/outcome)."""
    id: str
    headline: str
    rationale: str
    effort: str = "medium"                 # low | medium | high
    impact: str = ""                       # pre-formatted, e.g. "₹1.8L/mo"
    status: str = "recommended"            # recommended | acted | dismissed
    outcome: str = ""                      # tracked outcome once acted
    prov: Optional[Provenance] = None


@dataclass
class BrandPosition:
    share: Metric
    rank: Metric
    velocity: Metric


@dataclass
class ScopeBar:
    category: str
    price_band: str
    categories: List[str]                  # selector options
    price_bands: List[str]
    position: BrandPosition                # the brand's own position — operational grounding


@dataclass
class Brief:
    dated: str                             # e.g. "Fri · Jul 3"
    narrative: str                         # short synthesis memo
    moves: List[Move]                      # top 2–3 moves as cards
    caption: str = ""                      # coverage note, e.g. "live sections only; Whitespace/VoC later"


@dataclass
class SignalItem:
    id: str
    materiality: int                       # 0–100 rank score (L1)
    changed: str                           # what changed
    why: str                               # why it matters to this brand
    move: Move                             # suggested play
    evidence: List[Metric] = field(default_factory=list)


@dataclass
class WhitespaceItem:
    id: str
    concept: str                           # SKU / subcategory concept
    thesis: str                            # entry thesis vs the brand's adjacencies
    score: int
    margin: Metric
    adjacency: str
    move: Optional[Move] = None
    prov: Optional[Provenance] = None


@dataclass
class CompetitiveItem:
    id: str
    competitor: str
    moved: str                             # the tracked move
    response: Move                         # recommended response
    evidence: List[Metric] = field(default_factory=list)   # scraped figures live here (badged)
    kind: str = ""                         # L1 classification (price_cut/new_entrant/…) — for logic
    kind_label: str = ""                   # human label for `kind` (rendered; never the raw enum)
    prov: Optional[Provenance] = None      # per-row provenance (official vs scraped·directional)


@dataclass
class VoiceItem:
    attribute: str                         # e.g. "Waterproofing"
    you: Metric
    peer_set: Metric
    gap: str                               # synthesis of the gap
    feeds: str = ""                        # which section this informs (Whitespace/Competitive)


@dataclass
class MarketPulseItem:
    id: str
    headline: str
    so_what: str                           # "so what for you" — the only reason it's shown
    materiality: int
    prov: Provenance


@dataclass
class MovesLoop:
    """The decision→outcome loop. Designed in even if thin today. Counts are live; the outcome
    aggregates (attributed_margin, hit_rate) are coming — Metric(field_state="coming")."""
    recommended: List[Move] = field(default_factory=list)
    acted: List[Move] = field(default_factory=list)
    dismissed: List[Move] = field(default_factory=list)
    attributed_margin: Optional[Metric] = None     # coming
    hit_rate: Optional[Metric] = None              # coming


@dataclass
class AskAnalyst:
    scope: str                             # the category the conversation is scoped to
    prompt: str
    suggested: List[str] = field(default_factory=list)


@dataclass
class SectionState:
    """Per-section data state (frozen public schema). `state` ∈ live|partial|fixture; `provenance`
    aggregates the tiers present in the section; `coming` is the honest-empty copy a real tenant sees
    for a fixture section. The client keys its border/badge treatment off `state`."""
    state: str
    provenance: List[Provenance] = field(default_factory=list)
    coming: str = ""


@dataclass
class AnalystStates:
    scope: SectionState
    brief: SectionState
    signals: SectionState
    whitespace: SectionState
    competitive: SectionState
    voice: SectionState
    market_pulse: SectionState
    moves: SectionState
    ask: SectionState


@dataclass
class AnalystBrief:
    generated_at: str
    synthesis_source: str                  # "fixture" | "live" | "live+fixture" — what produced this
    scope: ScopeBar
    brief: Brief
    signals: List[SignalItem]
    whitespace: List[WhitespaceItem]
    competitive: List[CompetitiveItem]
    voice: List[VoiceItem]
    market_pulse: List[MarketPulseItem]
    moves: MovesLoop
    ask: AskAnalyst
    states: AnalystStates = None           # per-section data-state contract (Phase 1)


def to_public(brief: AnalystBrief) -> dict:
    """Serialize the brief to the JSON the client consumes (nested dataclasses included). No internal
    identifiers are added here — the router owns tenancy; the payload is pure synthesis."""
    return asdict(brief)


# Top-level keys every AnalystBrief payload carries — the frozen surface the client + future service
# build against (the contract test asserts this exact set).
PUBLIC_KEYS = {"generated_at", "synthesis_source", "scope", "brief", "signals", "whitespace",
               "competitive", "voice", "market_pulse", "moves", "ask", "states"}


def synthesize_category_analyst(tenant_id, category=None, price_band=None) -> AnalystBrief:
    """SYNTHESIS SEAM — the one function the future analyst service implements.

    Signature is stable: (tenant_id, category, price_band) -> AnalystBrief. `tenant_id` is resolved
    server-side by the router (never trusted from the client) and is threaded here so the real
    implementation can scope every read to the tenant via the repository/deps path.

    Phase 1: the reshape-only sections (Signal Feed, Market Pulse, Competitive, Brief, and the live
    parts of Scope/Moves) are assembled from REAL tenant L1 data by realify.domain.analyst_live; the
    not-yet-built sections (Whitespace, Voice of Customer) render fixture content ONLY for the fixture
    tenant and honest-empty coming-state for real tenants (the exposure gate). L1 owns every number,
    ranking and classification here; the prose is deterministic-from-L1 (the L2 phrasing seam).
    TODO(analyst-service): swap the deterministic `_phrase` seam for real L2 narration (numbers stay L1)
    and build Whitespace/VoC synthesis. Ranking/classification stay in L1.
    """
    from realify.domain import analyst_live
    from realify import db
    with db.connect() as con:
        return analyst_live.assemble(con, tenant_id, category, price_band)
