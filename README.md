# Once

On lounching pi for the first time with ubuntu server run this.

```bash
sudo ./once
```

# Plex

```bash
curl https://downloads.plex.tv/plex-keys/PlexSign.key | sudo apt-key add -
echo deb https://downloads.plex.tv/repo/deb public main | sudo tee /etc/apt/sources.list.d/plexmediaserver.list
sudo apt update
sudo apt install plexmediaserver -y
sudo systemctl enable plexmediaserver
sudo systemctl start plexmediaserver
sudo systemctl status plexmediaserver
sudo ufw allow from 192.168.1.0/24 to any port 32400 proto tcp
```

Then some messing around to claim the server. Important to access pi by ip directly, not alias.

To discover token

```
sudo cat /var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/Preferences.xml | grep PlexOnlineToken
```

To refresh where 3 is library ID from

```
curl "http://127.0.0.1:32400/library/sections?X-Plex-Token=YOUR_TOKEN"
```

```
curl "http://127.0.0.1:32400/library/sections/3/refresh?X-Plex-Token=YOUR_TOKEN"
```

And to cron in a script

```
crontab -e
*/10 * * * * /home/nestor/refresh_plex.sh >> /home/nestor/plex_refresh.log 2>&1
```

# Transmission

```bash
sudo apt install transmission-daemon -y
```

Temp fix

```bash
sudo sysctl -w net.core.rmem_max=4194304
sudo sysctl -w net.core.wmem_max=1048576
```

And put to `/etc/sysctl.conf` for the permanent fix

```bash
net.core.rmem_max=4194304
net.core.wmem_max=1048576
```


Stop and change `/etc/transmission-daemon/settings.json` to test and hide once not needed

```bash
sudo systemctl stop transmission-daemon
```

Need auth for both plex and transmission to have access

```
sudo groupadd media
sudo usermod -aG media plex
sudo usermod -aG media debian-transmission
sudo chown -R plex:media /var/lib/plexmediaserver/test
sudo chmod -R 775 /var/lib/plexmediaserver/test
sudo chmod g+s /var/lib/plexmediaserver/test
```

Firewall

```
sudo ufw allow from 192.168.1.0/24 to any port 9091 proto tcp
sudo ufw status verbose
```

# Jackett

To manually install

```bash
sudo apt install apt-transport-https -y
sudo mkdir -p /opt/jackett
cd /opt/jackett
sudo wget https://github.com/Jackett/Jackett/releases/latest/download/Jackett.Binaries.LinuxARM64.tar.gz
sudo tar -xvzf Jackett.Binaries.LinuxARM64.tar.gz
sudo rm Jackett.Binaries.LinuxARM64.tar.gz
sudo chown -R $(whoami):$(whoami) /opt/jackett
```

Then back from the current repo root

Note: Update username and group in service

```bash
sudo cp jackett.service /etc/systemd/system/
sudo systemctl enable --now jackett
sudo systemctl status jackett
```

To allow PI 9117 to local network

```
sudo ufw allow from 192.168.1.0/24 to any port 9117 proto tcp
sudo ufw status verbose
```

Now opening `http://pi:9117` where `pi` is the pi host (or an alias in `/etc/hosts`) will show the Jackett UI.

The remaining steps are installing indexers with the UI (just follow the UI) and making Qbittorrent use Jackett as the search engine.

For the search engine configuration use the UI for the API key and select the correct host and copy the configuration to the correct location.

Note: Don't forget to set your API key

```
cp jackett.json ~/.local/share/qBittorrent/nova3/engines/
```

The final step is to restart Qbittorrent and add the search plugin URL https://raw.githubusercontent.com/qbittorrent/search-plugins/master/nova3/engines/jackett.py.

All done, both downloading and searching!

# Docker

```bash
sudo apt remove docker docker-engine docker.io containerd runc
sudo apt update
sudo apt install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker --now
sudo groupadd docker || true
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world
```

# Flaresolverr

Add the URL to Jackett

```bash
docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
```
