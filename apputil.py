    def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Wrapper around requests.get that returns the parsed JSON dict on success,
        or None on failure (HTTP error, JSON decode error, etc).
        """
        url = f"{self.BASE_URL}{path}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                return data
            # if the returned JSON is not a dict, return None (defensive)
            return None
        except Exception:
            # Do not propagate network/HTTP/JSON errors up to the caller — return None
            return None

    def get_artist(self, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Search for search_term and return the artist dict for the most-likely (first) hit.
        Robust to a few JSON shapes returned by mocks/tests.
        """
        # 1) search
        search_json = self._get_json("/search", params={"q": search_term})
        if not search_json:
            return None

        # search_json might be either:
        #   {"response": {"hits": [...]}}
        # or top-level {"hits": [...]}
        resp_block = search_json.get("response") if isinstance(search_json, dict) and "response" in search_json else search_json
        hits = []
        if isinstance(resp_block, dict):
            hits = resp_block.get("hits", []) if isinstance(resp_block.get("hits", []), list) else []
        elif isinstance(search_json.get("hits", []), list):
            hits = search_json.get("hits", [])

        if not hits:
            return None

        # 2) find an artist id from the first hit or fallback to other hits
        artist_id = None
        def extract_artist_id_from_result(result: Dict[str, Any]) -> Optional[int]:
            # possible locations for primary artist
            if not isinstance(result, dict):
                return None
            # typical shapes: result["primary_artist"]["id"] or result["artist"]["id"]
            for key in ("primary_artist", "artist"):
                candidate = result.get(key)
                if isinstance(candidate, dict) and candidate.get("id"):
                    try:
                        return int(candidate.get("id"))
                    except Exception:
                        return None
            # sometimes artist id might be under result["result"]["primary_artist"] — handle caller-supplied shape up the chain
            return None

        first_result = hits[0].get("result") if isinstance(hits[0], dict) else None
        if first_result:
            artist_id = extract_artist_id_from_result(first_result)

        # fallback: check other hits for a primary artist id
        if not artist_id:
            for hit in hits:
                r = hit.get("result") if isinstance(hit, dict) else None
                if r:
                    artist_id = extract_artist_id_from_result(r)
                    if artist_id:
                        break

        if not artist_id:
            return None

        # 3) request the artist endpoint and extract artist dict robustly
        artist_json = self._get_json(f"/artists/{artist_id}")
        if not artist_json:
            return None

        # possible shapes:
        # {"response": {"artist": {...}}}
        # or top-level {"artist": {...}}
        artist = None
        if isinstance(artist_json.get("response"), dict) and isinstance(artist_json["response"].get("artist"), dict):
            artist = artist_json["response"]["artist"]
        elif isinstance(artist_json.get("artist"), dict):
            artist = artist_json["artist"]
        else:
            # maybe artist_json["response"] **is** the artist dict directly (some mocks)
            resp_block2 = artist_json.get("response")
            if isinstance(resp_block2, dict) and resp_block2.get("id"):
                artist = resp_block2

        return artist

    def get_artists(self, search_terms: List[str]) -> pd.DataFrame:
        """
        Given a list of search terms, return DataFrame with columns:
        ['search_term', 'artist_name', 'artist_id', 'followers_count']
        """
        rows = []
        for term in search_terms:
            artist = None
            try:
                artist = self.get_artist(term)
            except Exception:
                # defensive: if anything unexpected happens, treat as no result
                artist = None

            if artist:
                name = artist.get("name")
                artist_id = artist.get("id")
                # followers may be stored in different places in different responses
                followers = None
                # common places
                if isinstance(artist.get("followers_count"), (int, float)):
                    followers = artist.get("followers_count")
                elif isinstance(artist.get("followers"), (int, float)):
                    followers = artist.get("followers")
                elif isinstance(artist.get("stats", {}), dict) and isinstance(artist["stats"].get("followers"), (int, float)):
                    followers = artist["stats"].get("followers")
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
