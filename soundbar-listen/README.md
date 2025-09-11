# Soundbar Listen

For debugging

```bash
docker build -t soundbar-listen . && docker run --network=host -e SOUNDBAR_IP=192.168.1.113 -e PORT=5050 soundbar-listen
```

Then terminate and the events will appear in the output (or after the termination run docker logs for the terminated process)
