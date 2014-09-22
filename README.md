[downforeveryoneorjustme.com](http://downforeveryoneorjustme.com/) + [status.github.com](https://status.github.com/)

Ridiculously simple url monitoring plus handy chart generation. It's all been done a million times before but I couldn't find it! Nagios is a pain to configure, Amazon monitoring and other services are way overkill, so there's this.

```crontab
* * * * * /opt/upmon/upmon.py http://api.bam-x.com/
```
