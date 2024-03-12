from src.ottoneu_lineup_generator import generateFangraphsSplitsAPIUrl
import pytest

def test_api():
    profilePage = 'http://www.fangraphs.com/statss.aspx?playerid=19197'
    year = '2023'
    splitsPage = 'https://www.fangraphs.com/api/players/splits?playerid=19197&split=&season=2023&position=C'
    assert generateFangraphsSplitsAPIUrl(profilePage, year) == splitsPage
