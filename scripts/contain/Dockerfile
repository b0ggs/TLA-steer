FROM python@sha256:edaf703dce209d774af3ff768fc92b1e3b60261e7602126276f9ceb0e3a96874
RUN apt-get update && apt-get install -y --no-install-recommends git tinyproxy && rm -rf /var/lib/apt/lists/* /var/spool/cron/crontabs /var/cache/ldconfig /var/cache/apt/archives/partial /etc/ssl/private /usr/local /home /root /mnt /media /srv /opt
COPY codex-package /usr/lib/codex
COPY probe.py taskcheck.py /usr/lib/mdseval/
COPY sealed-deps /sealed-deps
RUN printf '%s\n' 'User tinyproxy' 'Group tinyproxy' 'Port 8888' 'Listen 0.0.0.0' 'Timeout 600' 'LogFile "/dev/stderr"' 'PidFile "/tmp/tinyproxy.pid"' 'MaxClients 20' 'Allow 0.0.0.0/0' 'ConnectPort 443' 'Filter "/etc/tinyproxy/model.filter"' 'FilterDefaultDeny Yes' > /etc/tinyproxy/mdseval.conf && printf '%s\n' '^chatgpt\.com$' '^api\.openai\.com$' > /etc/tinyproxy/model.filter
