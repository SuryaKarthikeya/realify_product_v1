"""Startup configuration check. Prints each source's mode and warns when a source
is set to live but is missing the key/config it needs to actually return data —
so a live source never silently produces zero cards because of a missing key."""
import os
from . import config

# what each source needs to function in live mode
def _checks():
    return [
        ("keepa",   config.MODE["keepa"],   bool(config.KEEPA_KEY),
         "KEEPA_KEY", f"domain={config.KEEPA_DOMAIN}"),
        ("recalls", config.MODE["recalls"],
         (config.RECALL_REGION in ("US","BOTH")) or bool(os.environ.get("DATA_GOV_IN_KEY") and os.environ.get("DATA_GOV_IN_RECALL_RESOURCE")),
         "DATA_GOV_IN_KEY + DATA_GOV_IN_RECALL_RESOURCE (for IN)", f"region={config.RECALL_REGION}"),
        ("news",    config.MODE["news"],    bool(config.NEWS_API_KEY),
         "NEWS_API_KEY", f"country={config.NEWS_COUNTRY}"),
        ("trends",  config.MODE["trends"],  True,   # pytrends needs no key (best-effort)
         "pytrends installed", f"geo={config.TRENDS_GEO}"),
        ("anthropic (L2)", "live" if config.ANTHROPIC_API_KEY else "fallback",
         bool(config.ANTHROPIC_API_KEY), "ANTHROPIC_API_KEY", f"model={config.L2_MODEL}"),
    ]

def check(log=print):
    log("─" * 64)
    log("Realify source configuration")
    log("─" * 64)
    warnings = []
    for name, mode, ready, needs, extra in _checks():
        if mode == "live" and not ready:
            status = "LIVE ⚠ MISSING CONFIG"
            warnings.append(f"{name}: set to live but missing {needs} — will fail/return nothing.")
        elif mode == "live":
            status = "LIVE ✓"
        elif mode == "fallback":
            status = "fallback (deterministic)"
        else:
            status = "fixture (seeded)"
        log(f"  {name:16s} {status:24s} {extra}")
    log("─" * 64)
    if warnings:
        log("WARNINGS:")
        for w in warnings:
            log(f"  ⚠ {w}")
        log("  → fix the .env entry, or set that source back to fixture, to avoid empty cards.")
        log("─" * 64)
    return warnings
