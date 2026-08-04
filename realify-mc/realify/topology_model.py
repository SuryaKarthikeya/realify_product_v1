"""Cross-channel onboarding data model (spec §5) — the provenance primitive Resolved<T>, the
reliability-flag lifecycle (with the blocks/satisfied_by mapping as DATA, §7), and the TenantTopology /
ChecklistItem shapes. Pure Python; JSON-serialisable for persistence in the tenant_topology blob.

Rule (§7): detection wins the NUMBER immediately (effective follows detected on conflict); the user's
confirmation only flips provenance STATED→RECONCILED. Topology is always usable — it never blocks on
either side.
"""
from dataclasses import dataclass, field
from typing import Optional

# provenance
STATED, DETECTED, RECONCILED = "STATED", "DETECTED", "RECONCILED"
# entry paths
WIZARD, RAW = "WIZARD", "RAW"
# flag states
ARMED, SATISFIED, WAIVED = "ARMED", "SATISFIED", "WAIVED"
# goals
PROFIT_AFTER_ADS, AD_EFFICIENCY, CATEGORY_INTEL, EVERYTHING = (
    "PROFIT_AFTER_ADS", "AD_EFFICIENCY", "CATEGORY_INTEL", "EVERYTHING")
GOALS = (PROFIT_AFTER_ADS, AD_EFFICIENCY, CATEGORY_INTEL, EVERYTHING)
# checklist item statuses
PENDING, RECEIVED, PARTIAL, NOT_APPLICABLE, NO_LONGER_REQUIRED = (
    "PENDING", "RECEIVED", "PARTIAL", "NOT_APPLICABLE", "NO_LONGER_REQUIRED")

# flag id -> {satisfied_by (file_row_id | action | None), blocks (goals it blocks)} — rules-as-data (§7).
# EVERYTHING surfaces all blocks, so any goal-blocking flag also blocks EVERYTHING.
FLAG_SPECS = {
    "SHARED_INVENTORY":   {"satisfied_by": None,               "blocks": ()},   # auto once MCF confirmed
    "MCF_FEE_REQUIRED":   {"satisfied_by": "AMZ_MCF_FEES",      "blocks": (PROFIT_AFTER_ADS, EVERYTHING)},
    "FEE_GAP":            {"satisfied_by": "gateway_fee_file",  "blocks": (PROFIT_AFTER_ADS, EVERYTHING)},
    "SHIP_COST_ESTIMATED": {"satisfied_by": "inline_shipping_cost", "blocks": ()},
    "CROSSWALK_RECONCILE": {"satisfied_by": "crosswalk_reconcile",  "blocks": ()},
    "MARGIN_UNAVAILABLE": {"satisfied_by": "COGS_INLINE",       "blocks": (PROFIT_AFTER_ADS, EVERYTHING)},
    "AD_SPEND_ABSENT":    {"satisfied_by": "AD_*",              "blocks": (PROFIT_AFTER_ADS, AD_EFFICIENCY, EVERYTHING)},
}


@dataclass
class Resolved:
    """A single interviewed/detected field carrying its provenance. `stated` is the wizard answer
    (null on RAW), `detected` the recognizer's reading (null until files land), `effective` the value
    the pipeline uses."""
    stated: object = None
    detected: object = None
    effective: object = None
    source: Optional[str] = None
    conflict: bool = False
    confirmed_at: object = None

    @classmethod
    def from_stated(cls, v):
        return cls(stated=v, effective=v, source=STATED)

    @classmethod
    def from_detected(cls, v):                       # RAW path — nothing stated
        return cls(detected=v, effective=v, source=DETECTED)

    def observe(self, detected):
        """Detection lands. Detected wins the number immediately; a mismatch vs a stated value flags a
        conflict (the reconcile prompt), but provenance stays STATED until the user confirms."""
        self.detected = detected
        if self.stated is None:
            self.effective, self.source = detected, DETECTED
        elif detected is not None and detected != self.stated:
            self.conflict, self.effective = True, detected
        else:
            self.conflict, self.effective = False, self.stated
        return self

    def confirm(self, ts):
        """User acknowledges the reconcile → provenance RECONCILED (effective already = detected)."""
        self.source, self.confirmed_at = RECONCILED, ts
        return self

    def to_dict(self):
        return {"stated": self.stated, "detected": self.detected, "effective": self.effective,
                "source": self.source, "conflict": self.conflict, "confirmed_at": self.confirmed_at}

    @classmethod
    def from_dict(cls, d):
        d = d or {}
        return cls(d.get("stated"), d.get("detected"), d.get("effective"),
                   d.get("source"), bool(d.get("conflict")), d.get("confirmed_at"))


@dataclass
class ReliabilityFlag:
    """A reliability caveat with a lifecycle (§7): ARMED by an answer or by detection, SATISFIED when
    its satisfied_by input lands, WAIVED when the user acknowledges partial and continues."""
    id: str
    state: str = ARMED
    armed_by: Optional[str] = None                   # node_id | "detection"
    satisfied_by: Optional[str] = None               # resolved from FLAG_SPECS unless overridden

    def __post_init__(self):
        if self.satisfied_by is None:
            self.satisfied_by = FLAG_SPECS.get(self.id, {}).get("satisfied_by")

    def blocks(self):
        return FLAG_SPECS.get(self.id, {}).get("blocks", ())

    def satisfy(self):
        self.state = SATISFIED
        return self

    def waive(self):
        self.state = WAIVED
        return self

    def to_dict(self):
        return {"id": self.id, "state": self.state, "armed_by": self.armed_by,
                "satisfied_by": self.satisfied_by}

    @classmethod
    def from_dict(cls, d):
        return cls(d["id"], d.get("state", ARMED), d.get("armed_by"), d.get("satisfied_by"))


def arm(flags, flag_id, armed_by):
    """Arm a flag once — idempotent on id; a detection-armed flag and an answer-armed flag collapse to
    one ARMED entry (re-arming a WAIVED/SATISFIED flag does not resurrect it)."""
    for f in flags:
        if f.id == flag_id:
            return f
    f = ReliabilityFlag(flag_id, ARMED, armed_by)
    flags.append(f)
    return f


def satisfy_on_receipt(flags, file_row_id):
    """When a file_row_id lands, satisfy any ARMED flag whose satisfied_by it fulfils. 'AD_*' matches
    any ad-partner export (satisfied_by an AD_ row)."""
    for f in flags:
        if f.state != ARMED:
            continue
        sb = f.satisfied_by
        if sb == file_row_id or (sb == "AD_*" and str(file_row_id).startswith("AD_")):
            f.satisfy()
    return flags


@dataclass
class ChecklistItem:
    """Derived from topology (§9) — not a separate source of truth."""
    file_row_id: str
    group: str
    essentiality: str
    status: str = PENDING
    where_to_find: str = ""
    arrival_hint: str = "INSTANT"
    unlocks: list = field(default_factory=list)
    emitted_by: list = field(default_factory=list)
    satisfiable_by: tuple = ()
    acquisition_mode: str = "MANUAL_CSV"

    def to_dict(self):
        return {"file_row_id": self.file_row_id, "group": self.group, "essentiality": self.essentiality,
                "status": self.status, "where_to_find": self.where_to_find, "arrival_hint": self.arrival_hint,
                "unlocks": list(self.unlocks), "emitted_by": list(self.emitted_by),
                "satisfiable_by": list(self.satisfiable_by), "acquisition_mode": self.acquisition_mode}


# named Resolved fields carried on the topology (§5) — flexible so the resolution engine (Phase 5) fills
# them from node answers; serialised individually so provenance round-trips.
_RESOLVED_FIELDS = ("sku_parity", "gateway", "cogs_source", "amazon_mode", "shopify_modes")


@dataclass
class TenantTopology:
    tenant_id: object
    entry_path: str = RAW
    schema_version: int = 1
    channels: list = field(default_factory=list)          # [{platform, status, account_ref}]
    ad_partners: list = field(default_factory=list)        # [partner]
    primary_goal: Optional[str] = None
    resolved: dict = field(default_factory=dict)           # name -> Resolved (sku_parity, gateway, ...)
    flags: list = field(default_factory=list)              # [ReliabilityFlag]
    completeness: dict = field(default_factory=dict)       # goal -> AVAILABLE | PARTIAL([...]) | UNAVAILABLE

    def flag(self, flag_id):
        return next((f for f in self.flags if f.id == flag_id), None)

    def to_dict(self):
        return {"tenant_id": self.tenant_id, "entry_path": self.entry_path,
                "schema_version": self.schema_version, "channels": list(self.channels),
                "ad_partners": list(self.ad_partners), "primary_goal": self.primary_goal,
                "resolved": {k: v.to_dict() for k, v in self.resolved.items()},
                "flags": [f.to_dict() for f in self.flags], "completeness": dict(self.completeness)}

    @classmethod
    def from_dict(cls, d):
        d = d or {}
        return cls(tenant_id=d.get("tenant_id"), entry_path=d.get("entry_path", RAW),
                   schema_version=d.get("schema_version", 1), channels=list(d.get("channels", [])),
                   ad_partners=list(d.get("ad_partners", [])), primary_goal=d.get("primary_goal"),
                   resolved={k: Resolved.from_dict(v) for k, v in (d.get("resolved") or {}).items()},
                   flags=[ReliabilityFlag.from_dict(f) for f in (d.get("flags") or [])],
                   completeness=dict(d.get("completeness") or {}))
