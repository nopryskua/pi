Create a small web service that uses jacket indexes and initiates downloads for transmission

```
transmission-remote -a "magnet:?xt=urn:btih:YOUR_MAGNET_HASH&dn=Example+Name"
```

Run on boot

```bash
docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
```
