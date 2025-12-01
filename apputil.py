import os
from typing import Any, Dict, List, Optional

import requests
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class Genius:
    BASE_URL = "https://api.genius.com"

    def __init__(self, access_token: Optional[str] = None) -> None:
        self.access_token = access_token or os.getenv("GENIUS_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("Genius access token required.")
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.BASE_URL}{path}", headers=self.headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def get_artist(self, search_term: str) -> Optional[Dict[str, Any]]:
        search_json = self._get_json("/search", params={"q": search_term})
        if not search_json:
            return None

        response = search_json.get("response", search_json)
        hits = response.get("hits", [])
        if not hits:
            return None

        result = hits[0].get("result", {})
        primary = result.get("primary_artist") or result.get("artist")
        if not primary or not primary.get("id"):
            return None

        artist_json = self._get_json(f"/artists/{primary['id']}")
        if not artist_json:
            return None

        return artist_json.get("response", {}).get("artist") or artist_json.get("artist")

    def get_artists(self, search_terms: List[str]) -> pd.DataFrame:
        rows = []
        for term in search_terms:
            artist = self.get_artist(term)

            if artist:
                rows.append({
                    "search_term": term,
                    "artist_name": artist.get("name"),
                    "artist_id": artist.get("id"),
                    "followers_count": artist.get("followers_count")
                                      or artist.get("followers")
                                      or artist.get("stats", {}).get("followers"),
                })
            else:
                rows.append({
                    "search_term": term,
                    "artist_name": None,
                    "artist_id": None,
                    "followers_count": None,
                })

        return pd.DataFrame(rows)
