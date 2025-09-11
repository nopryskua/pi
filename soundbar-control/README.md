# Via Home Assistant

After running

```
docker run -d   --name homeassistant   --restart=unless-stopped   -v /home/pi/homeassistant/config:/config   --network=host   ghcr.io/home-assistant/home-assistant:stable
```

And generating the API key

To power on

```bash
curl -X POST   -H "Authorization: Bearer $TOKEN"   -H "Content-Type: application/json"   -d '{"entity_id": "media_player.sc9s"}'   http://localhost:8123/api/services/media_player/turn_off

curl -X POST   -H "Authorization: Bearer $TOKEN"   -H "Content-Type: application/json"   -d '{"entity_id": "media_player.sc9s"}'   http://localhost:8123/api/services/media_player/turn_on
```
