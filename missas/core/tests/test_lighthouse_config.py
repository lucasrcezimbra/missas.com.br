import json
from pathlib import Path


def test_lighthouse_config_exists():
    """Test that the Lighthouse configuration file exists."""
    config_path = Path(".lighthouserc.json")
    assert config_path.exists(), "Lighthouse configuration file should exist"


def test_lighthouse_config_valid_json():
    """Test that the Lighthouse configuration is valid JSON."""
    config_path = Path(".lighthouserc.json")
    with open(config_path) as f:
        config = json.load(f)

    assert isinstance(config, dict), "Configuration should be a valid JSON object"


def test_lighthouse_config_thresholds():
    """Test that the Lighthouse configuration has the correct performance thresholds."""
    config_path = Path(".lighthouserc.json")
    with open(config_path) as f:
        config = json.load(f)

    assertions = config["ci"]["assert"]["assertions"]

    # Check performance threshold (≥ 90)
    performance = assertions["categories:performance"]
    assert performance[0] == "error"
    assert performance[1]["minScore"] == 0.9

    # Check accessibility threshold (≥ 98)
    accessibility = assertions["categories:accessibility"]
    assert accessibility[0] == "error"
    assert accessibility[1]["minScore"] == 0.98

    # Check best practices threshold (= 100)
    best_practices = assertions["categories:best-practices"]
    assert best_practices[0] == "error"
    assert best_practices[1]["minScore"] == 1.0

    # Check SEO threshold (= 100)
    seo = assertions["categories:seo"]
    assert seo[0] == "error"
    assert seo[1]["minScore"] == 1.0


def test_lighthouse_config_locale():
    """Test that the Lighthouse configuration uses Brazilian Portuguese locale."""
    config_path = Path(".lighthouserc.json")
    with open(config_path) as f:
        config = json.load(f)

    locale = config["ci"]["collect"]["settings"]["locale"]
    assert locale == "pt-BR", "Locale should be set to Brazilian Portuguese"
