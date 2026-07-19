from realty_agent.enrichment.redfin import build_redfin_url
from realty_agent.enrichment.zillow import build_zillow_url


def test_build_zillow_url_full_address():
    url = build_zillow_url("1423 E Cactus Rd", "Phoenix", "AZ", "85020")
    assert url == "https://www.zillow.com/homes/1423-E-Cactus-Rd-Phoenix-AZ-85020_rb/"


def test_build_zillow_url_returns_none_without_address():
    assert build_zillow_url(None, "Phoenix", "AZ", "85020") is None


def test_build_redfin_url_full_address():
    url = build_redfin_url("1423 E Cactus Rd", "Phoenix", "AZ", "85020")
    assert url.startswith("https://www.redfin.com/search?query=")
    assert "1423" in url


def test_build_redfin_url_returns_none_without_address():
    assert build_redfin_url(None, "Phoenix", "AZ", "85020") is None
