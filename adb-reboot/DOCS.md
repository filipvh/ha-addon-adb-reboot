
Create a config like

```yaml
reboot: 
  - host: "192.168.1.22"
    cron: "0 0 * * 1"
  - host: "panel1.host.internal.lol.com"
    cron: "0 0 * * *"
```

start and let it do its thing
