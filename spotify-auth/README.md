## Build & Run Auth

Note that this is not an active server but a run once image to get the exchange token.

Note the local environment should contain `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` from Spotify UI and later `SPOTIFY_REFRESH_TOKEN` from running `spotify-auth`.

To get them follow the official Spotify documentation on authenticating a Spotify app.

```bash
docker build -t spotify-auth .
docker run --rm -it -e SPOTIFY_CLIENT_ID=$SPOTIFY_CLIENT_ID -e SPOTIFY_CLIENT_SECRET=$SPOTIFY_CLIENT_SECRET -p 8888:8888 spotify-auth
```

On visiting the link on the browser and logging into Spotify the output should show the refresh token. Set `SPOTIFY_REFRESH_TOKEN` environmental variable to the value.

## Token Exchange & Auth Check

All the env vars should be set.

```bash
AUTH=$(echo -n "$SPOTIFY_CLIENT_ID:$SPOTIFY_CLIENT_SECRET" | base64 | tr -d '\n')

RESPONSE=$(curl -X POST "https://accounts.spotify.com/api/token"   -H "Authorization: Basic $AUTH"    -d "grant_type=refresh_token"   -d "refresh_token=$SPOTIFY_REFRESH_TOKEN")

SPOTIFY_ACCESS_TOKEN="$(echo $RESPONSE | jq -r '.access_token')"

curl -s -X GET "https://api.spotify.com/v1/me/player/devices" \
  -H "Authorization: Bearer $SPOTIFY_ACCESS_TOKEN"
```
