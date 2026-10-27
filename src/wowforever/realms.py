"""Read WoW Forever realm status from Blizzard's game data API."""

import base64
import http.client
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from wowforever.blizzard import TIMEOUT, USER_AGENT, FetchError, ParseError

REGIONS = ("us", "eu")
NAMESPACE = "dynamic-classic-{region}"  # UNCONFIRMED guess until launch
_FOREVER_RE = re.compile(r"forever", re.I)  # matched against a realm's category; UNCONFIRMED guess until launch

TOKEN_URL = "https://oauth.battle.net/token"
SEARCH_URL = "https://{region}.api.blizzard.com/data/wow/search/connected-realm"
_TYPES = {"NORMAL": "PvE", "PVP": "PvP", "RP": "RP", "RPPVP": "RP-PvP"}


@dataclass(frozen=True)
class Realm:
    region: str
    name: str
    type: str  # "PvP" | "PvE" | "RP" | "RP-PvP"
    up: bool
    population: str  # "Low", "Medium", "High", "Full", or a new label as Blizzard gives it


def _request(request: urllib.request.Request) -> dict:
    # Errors name the URL only: never the client secret or the access token.
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, UnicodeDecodeError, ValueError) as err:
        raise FetchError(f"{request.full_url}: {err}") from err


def _post(url: str, data: bytes, headers: dict) -> dict:
    return _request(urllib.request.Request(
        url, data=data, method="POST", headers={"User-Agent": USER_AGENT, "Accept": "application/json", **headers}))


def token(client_id: str, client_secret: str, post: Callable[..., dict] | None = None) -> str:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = (post or _post)(
        TOKEN_URL, b"grant_type=client_credentials", {"Authorization": f"Basic {credentials}"})
    try:
        access = data["access_token"]
    except (KeyError, TypeError) as err:
        raise ParseError("token response has no access_token") from err
    if not isinstance(access, str) or not access:
        raise ParseError("token response has no access_token")
    return access


def _name(localized) -> str:
    if not isinstance(localized, dict) or not localized:
        raise ValueError("missing localized text")
    return str(localized.get("en_US") or localized.get("en_GB") or next(iter(localized.values())))


def parse_search(region: str, data: dict) -> list[Realm]:
    try:
        results = data["results"]
        if not isinstance(results, list):
            raise ValueError("results is not a list")
        found = []
        for result in results:
            group = result["data"]
            up = group["status"]["type"] == "UP"
            population = str(group["population"]["type"]).title()
            for realm in group["realms"]:
                category = realm.get("category")
                if not isinstance(category, dict) or not _FOREVER_RE.search(_name(category)):
                    continue
                kind = str(realm["type"]["type"])
                found.append(Realm(region, _name(realm["name"]), _TYPES.get(kind, kind.title()), up, population))
    except (KeyError, TypeError, ValueError, AttributeError) as err:
        raise ParseError(f"unexpected realm search response: {err}") from err
    return sorted(found, key=lambda r: r.name)


def forever_realms(region: str, access_token: str, get: Callable[[str], dict] | None = None) -> list[Realm]:
    if get is None:
        def get(url: str) -> dict:
            return _request(urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT, "Accept": "application/json", "Authorization": f"Bearer {access_token}"}))

    namespace = NAMESPACE.format(region=region)
    base = SEARCH_URL.format(region=region) + "?" + urllib.parse.urlencode({"namespace": namespace, "orderby": "id"})
    found: list[Realm] = []
    page, pages = 1, 1
    while page <= pages:
        data = get(f"{base}&_page={page}")
        try:
            pages = int(data.get("pageCount") or 1)
        except (AttributeError, TypeError, ValueError) as err:
            raise ParseError(f"unexpected realm search response: {err}") from err
        found += parse_search(region, data)
        page += 1
    return sorted(found, key=lambda r: r.name)
