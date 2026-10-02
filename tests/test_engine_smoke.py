from pathlib import Path

from profile_engine import compute_profile, SSN_PATH


def test_bundled_silso_exists_and_no_client_path():
    assert SSN_PATH.is_file()
    p = compute_profile(
        "Smoke", "1977-01-06", "F",
        gestation_mode="conception",
        conception="1976-04-15",
        uncertainty_days=0,
    )
    assert p["meta"]["dataset"]["path_exposed_to_client"] is False
    assert p["meta"]["subject"]["central_conception"] == "1976-04-15"
    assert len(p["processing"]["parameters"]) >= 20
    assert p["experimental"]["somatic"]["status"] == "EXPERIMENTAL"
    assert p["experimental"]["somatic"]["diagnostic_use"] is False
    assert p["experimental"]["psychophysiology"]["status"] == "EXPERIMENTAL"


def test_precomputed_reference_files_bundled():
    data = Path(__file__).resolve().parents[1] / "data"
    for name in (
        "SN_d_tot_V2.0.txt",
        "physical_reference_bank_w5_v01.pkl.gz",
        "physical_reference_bank_w7_v01.pkl.gz",
        "silso_context_reference_v2.pkl.gz",
    ):
        assert (data / name).is_file(), name
