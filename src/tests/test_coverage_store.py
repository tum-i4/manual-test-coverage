from manual_test_coverage.core.coverage_store import CoverageStore, collect_covered_offsets


def test_collect_covered_offsets_normalizes_payload():
    payload = {"demo.exe": [20, 10, 10, 30]}

    result = collect_covered_offsets(payload)

    assert result == {"demo.exe": [10, 20, 30]}


def test_coverage_store_records_and_clears_offsets():
    store = CoverageStore()

    store.add("demo.exe", [10, 10, 20])

    assert store.for_module("demo.exe") == [10, 20]
    assert store.as_dict() == {"demo.exe": [10, 20]}

    store.clear()

    assert store.as_dict() == {}
