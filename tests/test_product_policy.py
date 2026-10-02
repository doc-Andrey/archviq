import json
from pathlib import Path


def test_product_policy_free_vs_paid():
    p = Path(__file__).resolve().parents[1] / "config" / "products.json"
    cfg = json.loads(p.read_text(encoding="utf-8"))
    policy = cfg["policy"]
    assert policy["ssn_analytics"] == "FREE"
    assert policy["cognitive_tests"] == "PAID"
    assert policy["questionnaires"] == "PAID"
    assert policy["compatibility"] == "PAID"
    assert policy["somatic_branch"] == "FREE_EXPERIMENTAL"
    assert policy["psychophysiology_branch"] == "FREE_EXPERIMENTAL"
