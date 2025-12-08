# your code here ...

import requests
import pandas as pd

class Genius:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.genius.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

    def search(self, search_term):
        """
        Exercise 1:
        Search Genius API for songs matching the search_term.
        Returns the JSON response dictionary.
        """
        url = f"{self.base_url}/search"
        params = {"q": search_term}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_artist(self, search_term):
        """
        Exercise 2:
        Get detailed artist info for the primary artist found
        in the first hit of the search_term.
        Returns the JSON response dictionary of artist info.
        """
        # Search first to get artist ID
        search_results = self.search(search_term)
        hits = search_results.get("response", {}).get("hits", [])

        if not hits:
            raise ValueError(f"No results found for '{search_term}'")

        # Extract the primary artist ID from the first hit
        primary_artist = hits[0].get("result", {}).get("primary_artist", {})
        artist_id = primary_artist.get("id")

        if not artist_id:
            raise ValueError(f"No primary artist found for '{search_term}'")

        # Use the artist ID to get detailed artist info
        artist_url = f"{self.base_url}/artists/{artist_id}"
        response = requests.get(artist_url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_artists(self, search_terms):
        """
        Exercise 3:
        Takes a list of search terms and returns a DataFrame with:
        - search_term
        - artist_name
        - artist_id
        - followers_count (if available)
        """
        rows = []
        for term in search_terms:
            try:
                artist_data = self.get_artist(term)
                artist_info = artist_data.get("response", {}).get("artist", {})

                rows.append({
                    "search_term": term,
                    "artist_name": artist_info.get("name"),
                    "artist_id": artist_info.get("id"),
                    "followers_count": artist_info.get("followers_count", None)
                })
            except Exception as e:
                rows.append({
                    "search_term": term,
                    "artist_name": None,
                    "artist_id": None,
                    "followers_count": None
                })
                print(f"Warning: Could not get artist info for '{term}'. Error: {e}")

        return pd.DataFrame(rows)
