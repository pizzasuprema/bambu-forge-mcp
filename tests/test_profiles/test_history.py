import pytest

from bambu_forge.profiles.history import PrintHistoryStore


@pytest.fixture
def history(tmp_path):
    store = PrintHistoryStore(db_path=tmp_path / "history.db")
    yield store
    store.close()


def test_log_and_list(history):
    history.log_print(
        design_name="Benchy",
        profile_name="0.20mm Standard",
        printer_model="X1C",
        filament_type="PLA",
        filament_grams=25.0,
        print_time_minutes=45,
        outcome="success",
        quality_grade="excellent",
    )
    history.log_print(
        design_name="Gear",
        profile_name="0.16mm Quality",
        printer_model="X1C",
        filament_type="PETG",
        filament_grams=40.0,
        print_time_minutes=90,
        outcome="failure",
        failure_mode="adhesion",
    )

    entries = history.list_history()
    assert len(entries) == 2
    benchy = next(e for e in entries if e["design_name"] == "Benchy")
    assert benchy["profile_name"] == "0.20mm Standard"
    assert benchy["outcome"] == "success"
    assert benchy["quality_grade"] == "excellent"
    gear = next(e for e in entries if e["design_name"] == "Gear")
    assert gear["failure_mode"] == "adhesion"
    assert gear["filament_type"] == "PETG"


def test_list_filter_outcome(history):
    history.log_print(
        design_name="Benchy",
        profile_name="Standard",
        printer_model="X1C",
        filament_type="PLA",
        filament_grams=25.0,
        print_time_minutes=45,
        outcome="success",
    )
    history.log_print(
        design_name="Vase",
        profile_name="Standard",
        printer_model="X1C",
        filament_type="PLA",
        filament_grams=60.0,
        print_time_minutes=120,
        outcome="failure",
        failure_mode="stringing",
    )

    results = history.list_history(outcome="success")
    assert len(results) == 1
    assert results[0]["design_name"] == "Benchy"


def test_get_insights(history):
    history.log_print("A", "P", "X1C", "PLA", 20.0, 30, "success")
    history.log_print("B", "P", "X1C", "PLA", 30.0, 60, "success")
    history.log_print("C", "P", "X1C", "PETG", 50.0, 90, "failure", failure_mode="adhesion")
    history.log_print("D", "P", "X1C", "PLA", 10.0, 20, "failure", failure_mode="adhesion")

    insights = history.get_insights()
    assert insights["total_prints"] == 4
    assert insights["success_rate"] == pytest.approx(0.5)
    assert insights["avg_print_time"] == pytest.approx(50.0)
    assert insights["total_filament_grams"] == pytest.approx(110.0)
    assert insights["most_used_filament"] == "PLA"
    assert insights["most_common_failure_mode"] == "adhesion"


def test_profile_success_rate(history):
    history.log_print("A", "FastDraft", "X1C", "PLA", 10.0, 20, "success")
    history.log_print("B", "FastDraft", "X1C", "PLA", 15.0, 25, "success")
    history.log_print("C", "FastDraft", "X1C", "PLA", 12.0, 22, "failure")

    rate = history.get_profile_success_rate("FastDraft")
    assert rate["profile_name"] == "FastDraft"
    assert rate["total_prints"] == 3
    assert rate["success_rate"] == pytest.approx(2 / 3, abs=0.001)
