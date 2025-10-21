# apputil.py
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
        """Initialize Genius helper. Token from env var GENIUS_ACCESS_TOKEN if not provided."""
        self.access_token = access_token or os.getenv("GENIUS_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("Genius access token required. Set GENIUS_ACCESS_TOKEN or pass access_token.")
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_artist(self, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Search for search_term and return the artist dict for the most-likely (first) hit.
        Returns None if no artist found.
        """
        # 1) search
        search_json = self._get_json("/search", params={"q": search_term})
        hits = search_json.get("response", {}).get("hits", [])
        if not hits:
            return None

        # 2) first hit primary artist id (defensive)
        artist_id = None
        first = hits[0].get("result", {})
        primary = first.get("primary_artist") or first.get("artist")
        if primary and isinstance(primary, dict):
            artist_id = primary.get("id")

        if not artist_id:
            # try to find any hit with primary_artist id
            for hit in hits:
                r = hit.get("result", {})
                p = r.get("primary_artist") or r.get("artist")
                if p and p.get("id"):
                    artist_id = p.get("id")
                    break

        if not artist_id:
            return None

        # 3) artist endpoint
        artist_json = self._get_json(f"/artists/{artist_id}")
        artist = artist_json.get("response", {}).get("artist")
        return artist

    def get_artists(self, search_terms: List[str]) -> pd.DataFrame:
        """
        Given a list of search terms, return DataFrame with columns:
        ['search_term', 'artist_name', 'artist_id', 'followers_count']
        """
        rows = []
        for term in search_terms:
            try:
                artist = self.get_artist(term)
            except requests.HTTPError:
                # if HTTP error (e.g., 401/429), record None values for this term
                artist = None

            if artist:
                name = artist.get("name")
                artist_id = artist.get("id")
                # followers may be stored in different places
                followers = artist.get("followers_count") or artist.get("followers") or artist.get("stats", {}).get("followers")
            else:
                name = None
                artist_id = None
                followers = None

            rows.append(
                {
                    "search_term": term,
                    "artist_name": name,
                    "artist_id": artist_id,
                    "followers_count": followers,
                }
            )

        df = pd.DataFrame(rows, columns=["search_term", "artist_name", "artist_id", "followers_count"])
        return df


if __name__ == "__main__":
    # Quick manual test (ensure GENIUS_ACCESS_TOKEN is set in .env or pass token)
    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        print("Set GENIUS_ACCESS_TOKEN in env or use Genius(access_token='...')")
    else:
        g = Genius()
        print(g.get_artist("Radiohead") and g.get_artist("Radiohead").get("name"))
        print(g.get_artists(["Rihanna", "Tycho", "Seal", "U2"]))
