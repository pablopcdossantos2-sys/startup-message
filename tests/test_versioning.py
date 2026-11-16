import pytest

from versioning import msix_version, read_version, validate_tag


def test_current_source_has_valid_msix_version():
    value = read_version()
    assert msix_version(value).endswith(".0")


@pytest.mark.parametrize(("value", "expected"), [
    ("1.0.1", "1.0.1.0"),
    ("2.15.65535", "2.15.65535.0"),
    ("1.0002.3", "1.2.3.0"),
])
def test_valid_versions(value, expected):
    assert msix_version(value) == expected


@pytest.mark.parametrize("value", [
    "0.1.0", "1", "1.2", "1.2.3.4", "v1.2.3",
    "1.2.3-beta", "1.2.65536", "-1.0.0", "1.2.x",
])
def test_invalid_versions(value):
    with pytest.raises(ValueError):
        msix_version(value)


def test_tag_must_match_source_version():
    validate_tag("1.0.1", "v1.0.1")
    with pytest.raises(ValueError):
        validate_tag("1.0.1", "v1.0.0")
