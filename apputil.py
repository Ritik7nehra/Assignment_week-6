import requests

class Genius:
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.base_url = "https://api.genius.com"

    def get_artist(self, artist_name):
        """
        Fetches artist info from Genius API.
        If no access token is provided, returns a dummy message.
        """
        if not self.access_token:
            return f"Access token not provided. Dummy result for artist: {artist_name}"

        search_url = f"{self.base_url}/search"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"q": artist_name}

        response = requests.get(search_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            hits = data["response"]["hits"]
            if hits:
                artist = hits[0]["result"]["primary_artist"]["name"]
                return f"Artist found: {artist}"
            else:
                return f"No artist found for '{artist_name}'"
        else:
            return f"Error: {response.status_code} - {response.text}"


if __name__ == "__main__":
    # Replace YOUR_ACCESS_TOKEN_HERE with your Genius API token (optional)
    genius = Genius(access_token="UGMK10dVg0dmcuzWy6INvHy-I8aNWbblm-jWPeUfOcIVAZk6sEUW0TZzS0flrn1L")
  # You can add token here if available
    print(genius.get_artist("Radiohead"))
