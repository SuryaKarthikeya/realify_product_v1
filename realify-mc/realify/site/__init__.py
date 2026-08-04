"""Realify public site — the marketing shell (platform / pricing / about), auth pages (signin / signup /
welcome) and in-app subscription components (badge / banners / billing gate). Server-rendered HTML in the
marketing design language (white / #2563eb). Pure view layer: no DB or session access lives here — the
routers (realify.routers.marketing / billing) and realify.billing own state. Folded in from the former
standalone /beta app (migration 0011)."""
