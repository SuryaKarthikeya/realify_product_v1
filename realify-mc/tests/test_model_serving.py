"""Tests for the model-serving boundary (#005 1e): version stamping + crash isolation."""
import os, tempfile, sys

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_model_"), "t.db")
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import models  # noqa: E402


class _Good:
    id = "fake-good"
    version = "9.9.9"
    covers = {"x"}
    def predict(self, con, tid, asin, det):
        return {"kind": self.id, "value": 1.0, "confidence": "high", "top_features": []}


class _Boom:
    id = "fake-boom"
    version = "1.0.0"
    covers = {"x"}
    def predict(self, con, tid, asin, det):
        raise RuntimeError("model crashed")


def test_prediction_is_version_stamped():
    out = models._serve(_Good(), None, 1, "ASIN1", "x", timeout=5)
    assert out["version"] == "9.9.9"
    assert out["model_id"] == "fake-good"
    assert out["value"] == 1.0 and out["confidence"] == "high"


def test_model_crash_degrades_to_low_and_is_stamped():
    out = models._serve(_Boom(), None, 1, "ASIN1", "x", timeout=5)
    assert out["confidence"] == "low" and out["value"] is None
    assert out["version"] == "1.0.0"
    assert "crashed" in out.get("error", "")


def test_registered_models_declare_a_version():
    for m in models.REGISTRY:
        assert getattr(m, "version", None), f"{m.id} is missing a version"


if __name__ == "__main__":
    test_prediction_is_version_stamped()
    test_model_crash_degrades_to_low_and_is_stamped()
    test_registered_models_declare_a_version()
    print("model serving OK")
