DNS Made Easy Python Based Updater
==========
Basic Python script to iterate over an array of json items and update each associated Dynamic DNS Record as configured.
Based off of the good work of https://github.com/wyrmiyu/ddns-tools :)
Just attempting to take it to the next level a little bit.


Requires following non-core modules:
==========

python-requests, https://pypi.python.org/pypi/requests/

python-dns, https://pypi.python.org/pypi/dnspython/


What it does?
==========
Currently the script uses "myip" web-page by Dnsmadeeasy to determine client's current IP.
It then compares it to the actual DNS record and in case the IPs differ, the script will attempt to update the record.

The update itself is done via the documented API provided by Dnsmadeeasy.
Further the script ensures that the SSL certificate of dnsmadeeasy.com is valid one, before attempting the update.


TTL and cron
==========
As the DNS TIme-To-Live value sets the caching time for your record, your DNS update won't show up
for your script until the TTL has run off. Therefore you should see that cron and TTL are somewhat in
sync in this matter, so that you won't end up having redundant updates to Dnsmadeeasy.

If you set the script to run from cron - for example - once per 10 minutes, then set your TTL to 600 seconds respectively.

