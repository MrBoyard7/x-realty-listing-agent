from realty_agent.enrichment.county_assessor import resolve_county_and_assessor_url


def test_known_city_resolves_county_and_url():
    county, url = resolve_county_and_assessor_url("Phoenix", "AZ")
    assert county == "Maricopa"
    assert url == "https://mcassessor.maricopa.gov/"


def test_unknown_city_returns_none_none():
    county, url = resolve_county_and_assessor_url("Nowhere Town", "AZ")
    assert county is None
    assert url is None


def test_missing_city_or_state_returns_none_none():
    assert resolve_county_and_assessor_url(None, "AZ") == (None, None)
    assert resolve_county_and_assessor_url("Phoenix", None) == (None, None)
