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
*/10 * * * * /home/nestor/.refresh_plex.sh
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
sudo chown -R plex:media /var/lib/plexmediaserver/Movies
sudo chmod -R 775 /var/lib/plexmediaserver/Movies
sudo chmod g+s /var/lib/plexmediaserver/Movies
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
docker run -d \
  --name flaresolverr \
  -p 8191:8191 \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

Now more indexers work

```bash
curl "http://localhost:9117/api/v2.0/indexers/all/results?apikey=$JACKETT_API_KEY&Query=4k&Limit=10"
```

# Persistent Journalctl

```bash
# Make sure the base dir exists and has the right perms
sudo mkdir -p /var/log/journal
sudo chown root:systemd-journal /var/log/journal
sudo chmod 2755 /var/log/journal

# Create machine-id based subdir (same ID as in /etc/machine-id)
sudo mkdir -p /var/log/journal/$(cat /etc/machine-id)
sudo chown root:systemd-journal /var/log/journal/$(cat /etc/machine-id)
sudo chmod 2755 /var/log/journal/$(cat /etc/machine-id)

# Restart journald
sudo systemctl restart systemd-journald

# Flush
sudo journalctl --flush
```

# For History

Put to `~/.bashrc`

```bash
# ~/.bashrc additions for persistent, "infinite" history

# Don’t truncate history
export HISTSIZE=
export HISTFILESIZE=

# Append instead of overwrite history on shell exit
shopt -s histappend

# Save after every command (not just when the shell exits)
PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

# Add timestamps
export HISTTIMEFORMAT="%F %T "

# Ignore duplicate commands and trivial ones
export HISTCONTROL=ignoredups:erasedups
export HISTIGNORE="ls:cd:exit:pwd:clear"
```

# Network check

```bash
cp .check_remote.sh ~/
crontab -e
*/3 * * * * /home/nestor/.check_remote.sh
```

# Query

To conveniently query from Jackett

```bash
./query.py --query "4k"
```

# FZF

```bash
sudo apt install fzf
```

And add to `~/.bashrc`

```bash
# fzf setup
# Auto-completion and keybindings
if [ -f /usr/share/doc/fzf/examples/key-bindings.bash ]; then
  source /usr/share/doc/fzf/examples/key-bindings.bash
fi
```

# PulseAudio

For slightly better quality

```bash
# Install
sudo apt install pulseaudio pulseaudio-utils

# Since it's user service, linger
sudo loginctl enable-linger nestor
loginctl user-status nestor

# Enable
systemctl --user enable pulseaudio.service
systemctl --user enable pulseaudio.socket
systemctl --user start pulseaudio.service

# Check
systemctl --user status pulseaudio.service
```

# Spotify

```bash
wget https://github.com/Spotifyd/spotifyd/releases/download/v0.4.1/spotifyd-linux-aarch64-default.tar.gz
tar -xvzf spotifyd-linux-aarch64-default.tar.gz
sudo chmod +x spotifyd
sudo mv spotifyd /usr/local/bin/
sudo apt install libpulse0
rm -rf spotifyd-linux-aarch64-default.tar.gz
```

```bash
# Allow mDNS (UDP 5353) from your LAN
sudo ufw allow from 192.168.1.0/24 to any port 5353 proto udp

# Allow zeroconf TCP port from your LAN (or some other port if configured differently)
sudo ufw allow from 192.168.1.0/24 to any port 1234 proto tcp
```

There is a need for a workaround to add the following line `/etc/hosts`.

```bash
0.0.0.0                 apresolve.spotify.com
```

It's also necessary to add the same to AdGuard DNS overrides since it overrides the override.

Then test the playback by using Spotify UI, selecting the new device, and playing a song.

```bash
spotifyd --no-daemon --verbose --zeroconf-port=1234
```

Now configure a service.

```bash
mkdir -p ~/.config/systemd/user
cp spotifyd.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable spotifyd.service
systemctl --user start spotifyd.service

# Check
systemctl --user status spotifyd.service
```

# AdGuard

```bash
# For autonomous DNS (optional)
sudo nmcli con mod "preconfigured" ipv4.ignore-auto-dns yes
sudo nmcli con mod "preconfigured" ipv4.dns "1.1.1.1"
sudo nmcli con up "preconfigured"
dig google.com | grep SERVER

# For static IP
sudo nmcli con mod "preconfigured" ipv4.addresses 192.168.1.50/24
sudo nmcli con mod "preconfigured" ipv4.gateway 192.168.1.1
sudo nmcli con mod "preconfigured" ipv4.method manual
sudo nmcli con up "preconfigured"

# Then SSH to the new IP 192.168.1.50

# Now AdGuard
sudo mkdir -p /etc/adguardhome/work
sudo mkdir -p /etc/adguardhome/conf

docker run -d \
  --name adguardhome \
  --restart unless-stopped \
  --network host \
  -v /etc/adguardhome/work:/opt/adguardhome/work \
  -v /etc/adguardhome/conf:/opt/adguardhome/conf \
  adguard/adguardhome

# Firewall
sudo ufw allow from 192.168.1.0/24 to any port 53 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 53 proto udp
sudo ufw allow from 192.168.1.0/24 to any port 3000 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 80 proto tcp
```

Finally, use PI IP as DHCP server DNS of your router (not the router DNS itself).

# Misc utils (optional)

```bash
# For testing playback
sudo apt install mpv

# For checking capabilities
sudo apt install read-edid edid-decode

# To check HDMI devices
aplay -l

# To check what soundbar supports
cat /sys/class/drm/card1-HDMI-A-2/edid | edid-decode
```

# Mopidy Player

```bash
# Getting the repo
sudo mkdir -p /etc/apt/keyrings
sudo wget -q -O /etc/apt/keyrings/mopidy-archive-keyring.gpg \
  https://apt.mopidy.com/mopidy-archive-keyring.gpg

sudo wget -q -O /etc/apt/sources.list.d/mopidy.sources https://apt.mopidy.com/bookworm.sources

# Installing the main server and the local scraper
sudo apt install mopidy
sudo apt install mopidy-local

# Installing the UI
sudo apt install python3-pip
sudo python3 -m pip install --break-system-packages Mopidy-Iris

# To access iris UI
sudo ufw allow from 192.168.1.0/24 to any port 6680 proto tcp

# Config
cp mopidy.conf ~/.config/mopidy/

# Access to media folder
sudo usermod -aG media mopidy

# Service
cp mopidy.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable mopidy
systemctl --user start mopidy
systemctl --user status mopidy

# Scan (maybe more frequent)
crontab -e
0 3 * * * /usr/bin/mopidy local scan
```

Now `http://pi:6680/iris` does the job.

# Tailscale

Register and install app on mac

Then install on PI

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

And run

```bash
sudo tailscale up
```

Check connected devices where second collumn will be hostname

```bash
tailscale status
```

Update local laptop `~/.ssh/config` to include the new way to connect

```bash
Host tpi
	User nestor
	HostName raspberrypi
```