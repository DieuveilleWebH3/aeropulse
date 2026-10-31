from importlib.metadata import version

import aeropulse


def test_package_can_be_imported() -> None:
    assert aeropulse.__name__ == "aeropulse"


def test_installed_distribution_has_expected_version() -> None:
    assert version("aeropulse") == "0.1.0"
