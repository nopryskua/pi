# App

The app is the website to query from Jackett

Note: Make sure to set the API key

```bash
docker build -t jackett-search .
docker run -d --name jackett-search --network host --restart unless-stopped -e JACKETT_API_KEY=$JACKETT_API_KEY jackett-search
sudo ufw allow from 192.168.1.0/24 to any port 5000 proto tcp
```
