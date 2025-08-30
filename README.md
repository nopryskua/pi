# Once

On lounching pi for the first time with ubuntu server run this.

```bash
sudo ./once
```

# Kodi

For videos

```bash
sudo apt install kodi
```

For kodi remote control (on pi os it's already installed)

```bash
sudo apt install cec-utils libcec-dev
sudo usermod -aG video $(whoami)
```

Then to reboot

To run kodi

```bash
kodi-standalone
```

To set it up on startup

Note: Update username and group in service

```bash
sudo cp kodi.service /etc/systemd/system/
sudo systemctl enable --now kodi
sudo systemctl status kodi
```

# Torrent

To setup torrent

## Qbittorrent

(This doesn't work on pi)

```bash
sudo apt install qbittorrent-nox -y
```

To set it up on startup

Note: Update username and group in service

```bash
sudo cp qbittorrent.service /etc/systemd/system/
sudo systemctl enable --now qbittorrent
sudo systemctl status qbittorrent
```

To allow PI 8080 to local network

```
sudo ufw allow from 192.168.1.0/24 to any port 8080 proto tcp
sudo ufw status verbose
```

Now opening `http://pi:8080` where `pi` is the pi host (or an alias in `/etc/hosts`) will show the qbittorrent UI. The user is `admin` and the password may be found from `sudo systemctl status qbittorrent` output (or it's `adminadmin` for pi).

## Jackett

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

# Sound Out

One may configure sound out with the config file

```bash
cp .asoundrc ~/
```
