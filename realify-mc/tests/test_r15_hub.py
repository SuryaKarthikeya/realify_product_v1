"""R15 hub + signin (hermetic, static render):
 · Part G.4 — the superlogin hub has a full-screen GENERATING lock (Cancel-only) around world creation
 · Part G.5 — direct-vs-managed inputs are explicit (Brand name = direct; Agency name = managed)
 · Part H.7 — the hub links back to the marketing home
 · Part H.6 — the /signin page links back to the marketing home
"""
from realify.site import hub, ui

_H = hub.hub_html("tester@realify.ai")


def test_g4_generation_lock_and_cancel_present():
    assert "id=genLock" in _H and "id=genCancel" in _H          # full-screen lock + Cancel control
    assert "function showGenLock" in _H and "function genRun" in _H
    assert "genRun(ev.currentTarget" in _H                      # generate/save run through the lock


def test_g5_direct_vs_managed_labels():
    assert "a DIRECT brand" in _H                               # Brand name → direct brand
    assert "leave blank if direct" in _H                        # Agency name → managed (blank = direct)


def test_h7_hub_links_home():
    assert 'href="/platform"' in _H


def test_h6_signin_links_home():
    assert 'href="/platform"' in ui.signin_page()


if __name__ == "__main__":
    for _n, _fn in list(globals().items()):
        if _n.startswith("test_") and callable(_fn):
            _fn()
    print("R15 hub/signin tests passed")
