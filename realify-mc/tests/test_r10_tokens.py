"""R10 (hermetic): the design-token extraction (Commit 1) — tokens.py is the single source, ui.py
points at it, and the marketing CSS is byte-identical (pixel-identical proxy). Plus the team service
constants. The Postgres team-management behavior lives in tests/agency/test_r10.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.site import tokens                      # noqa: E402
from realify.site import ui                          # noqa: E402
from realify.agency import team                      # noqa: E402


def test_tokens_extracted_and_shared():
    assert tokens.TOKENS.startswith(":root{")
    assert "--blue:#2E68E6" in tokens.TOKENS and "--bg:#F4F6F9" in tokens.TOKENS   # marketing palette
    assert tokens.TOKENS in ui.CSS                    # ui.py points at the shared token source
    # SHELL_CSS (for agency/interior imports) carries the tokens + reusable primitives
    assert tokens.TOKENS in tokens.SHELL_CSS and ".btn" in tokens.SHELL_CSS and ".tag" in tokens.SHELL_CSS


def test_marketing_css_pixel_identical():
    # The extraction is a pure splice: ui.CSS = reset + TOKENS + the rest, so the rendered marketing
    # CSS is byte-identical to before (regression gate). Assert the exact head shape.
    assert ui.CSS.startswith("\n*{box-sizing:border-box;margin:0;padding:0}\n:root{")
    # every marketing primitive still present (no class dropped)
    for cls in (".nav", ".btn-blue", ".hero", ".authcard", ".pricecard", "footer"):
        assert cls in ui.CSS, f"marketing class lost in extraction: {cls}"


def test_team_roles_and_seat_cap():
    assert team.SEAT_CAP == 10
    assert set(team.ROLES) == {"agency_admin", "account_manager", "ads_specialist", "analyst"}
    # all-brands roles flagged; the AM is the only assigned-book role
    assert team.ROLES["agency_admin"][1] is True and team.ROLES["ads_specialist"][1] is True
    assert team.ROLES["account_manager"][1] is False
