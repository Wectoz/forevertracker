import json
from pathlib import Path

import pytest

from wowforever import cli, realms
from wowforever.blizzard import FetchError, ParseError
from wowforever.realms import Realm, forever_realms, parse_search, token
from wowforever.store import Store

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "realms_search.json").read_text())


def test_parse_search_keeps_forever_realms_only():
    assert parse_search("us", FIXTURE) == [
        Realm("us", "Ashenvale", "RP", False, "Low"),
        Realm("us", "Zandalar", "PvP", True, "Full"),
    ]


def test_parse_search_skips_realm_without_category():
    data = json.loads(json.dumps(FIXTURE))
    data["results"][0]["data"]["realms"].append({"name": {"en_US": "Nocat"}, "type": {"type": "NORMAL"}})
    assert [r.name for r in parse_search("us", data)] == ["Ashenvale", "Zandalar"]


def test_parse_search_without_forever_realms_is_empty():
    data = {"results": [FIXTURE["results"][1]]}
    assert parse_search("us", data) == []


@pytest.mark.parametrize("data", [[], {}, {"results": {}}, {"results": [{"data": {}}]}])
def test_parse_search_malformed_raises(data):
    with pytest.raises(ParseError):
        parse_search("us", data)


def test_forever_realms_follows_pages():
    urls = []

    def get(url):
        urls.append(url)
        page = int(url.rsplit("_page=", 1)[1])
        return {"pageCount": 2, "results": [FIXTURE["results"][0 if page == 1 else 2]]}

    assert [r.name for r in forever_realms("us", "tok", get)] == ["Ashenvale", "Zandalar"]
    assert len(urls) == 2
    assert urls[0].startswith("https://us.api.blizzard.com/data/wow/search/connected-realm?")
    assert "namespace=" in urls[0] and urls[0].endswith("_page=1")


def test_token_sends_basic_auth():
    calls = []

    def post(url, data, headers):
        calls.append((url, data, headers))
        return {"access_token": "abc", "token_type": "bearer", "expires_in": 86399}

    assert token("id", "secret", post) == "abc"
    url, data, headers = calls[0]
    assert url == "https://oauth.battle.net/token"
    assert data == b"grant_type=client_credentials"
    assert headers["Authorization"] == "Basic aWQ6c2VjcmV0"


def test_token_without_access_token_raises_without_leaking():
    with pytest.raises(ParseError) as err:
        token("id", "secret", lambda *a: {"oops": 1})
    assert "secret" not in str(err.value)


def test_save_realms_replaces_region_and_ignores_empty():
    from datetime import UTC, datetime

    store = Store(":memory:")
    t1, t2 = datetime(2026, 10, 27, 10, tzinfo=UTC), datetime(2026, 10, 27, 11, tzinfo=UTC)
    store.save_realms("us", [Realm("us", "A", "PvP", True, "Low"), Realm("us", "B", "PvE", True, "High")], t1)
    store.save_realms("eu", [Realm("eu", "C", "RP", False, "Full")], t1)
    store.save_realms("us", [Realm("us", "B", "PvE", False, "High")], t2)
    store.save_realms("eu", [], t2)
    got = store.realms()
    assert list(got) == ["us", "eu"]
    assert got["us"] == (t2, [Realm("us", "B", "PvE", False, "High")])
    assert got["eu"] == (t1, [Realm("eu", "C", "RP", False, "Full")])


def test_cli_realms_without_secrets_is_noop(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("BLIZZARD_CLIENT_ID", raising=False)
    monkeypatch.setenv("BLIZZARD_CLIENT_SECRET", "x")
    db = tmp_path / "db.sqlite3"
    assert cli.main(["--db", str(db), "realms"]) == 0
    assert "BLIZZARD_CLIENT_ID/BLIZZARD_CLIENT_SECRET not set; realm status skipped." in capsys.readouterr().out
    assert Store(db).realms() == {}


def test_cli_realms_one_region_failing_still_saves_other(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("BLIZZARD_CLIENT_ID", "id")
    monkeypatch.setenv("BLIZZARD_CLIENT_SECRET", "secret")
    monkeypatch.setattr(realms, "token", lambda i, s, post=None: "tok")

    def fake(region, access_token, get=None):
        if region == "eu":
            raise FetchError("boom")
        return [Realm("us", "Z", "PvP", True, "Full")]

    monkeypatch.setattr(realms, "forever_realms", fake)
    db = tmp_path / "db.sqlite3"
    assert cli.main(["--db", str(db), "realms"]) == 0
    assert list(Store(db).realms()) == ["us"]
    assert "boom" in capsys.readouterr().err
