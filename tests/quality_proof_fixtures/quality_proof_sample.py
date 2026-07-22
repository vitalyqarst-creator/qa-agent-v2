def test_sample_check_passes() -> None:
    assert sorted({"source", "coverage", "review"}) == [
        "coverage",
        "review",
        "source",
    ]
