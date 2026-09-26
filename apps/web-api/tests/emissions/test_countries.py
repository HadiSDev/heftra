"""Open CEDA's alpha-3 country codes become the alpha-2 codes suppliers and companies carry."""
from __future__ import annotations

from web_api.emissions.countries import ALPHA3_TO_ALPHA2, alpha2


def test_a_country_code_is_converted():
    assert alpha2("DNK") == "DK"
    assert alpha2("GBR") == "GB"
    assert alpha2("TWN") == "TW"


def test_the_code_is_read_whatever_its_case_or_padding():
    assert alpha2(" deu ") == "DE"


def test_kosovo_uses_its_user_assigned_codes():
    assert alpha2("XXK") == "XK"


def test_a_code_that_is_no_country_is_unknown():
    assert alpha2("ROW") is None


def test_no_two_countries_share_an_alpha_2_code():
    assert len(set(ALPHA3_TO_ALPHA2.values())) == len(ALPHA3_TO_ALPHA2)
