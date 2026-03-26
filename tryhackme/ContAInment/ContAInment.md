
Hi! This is a writeup for TryHackMe room *ContAInment*.

![](containment1.png)

Room description:

*You are a Security Analyst at **West Tech**, a classified defence and R&D contractor. Early this morning, internal monitoring systems flagged unusual network activity originating from the workstation of senior researcher **Oliver Deer**. Upon accessing the machine, a ransom note was discovered on the desktop, suggesting that sensitive project data had been exfiltrated and encrypted. Your job is to investigate the incident: identify how the attacker gained access, trace their actions, recover any stolen data, and neutralise the threat. Time is critical; the
integrity of West Tech’s most sensitive technologies may be at risk.*

First thing I need to do after deploying a machine is to connect to it via ssh.

![](containment2.png)

I also have access to the AI chatbot integrated to the deployed machine and have access to it's files. That's sounds cool!

![](containment3.png)

From room hint I found out that the attacker made some mistakes and those can be found in a pcap files on the machine.
So, I need to locate those files.
First I've checked where I've landed after ssh-ing into machine using *pwd* command. Then I've used *find /home/o.deer/ -type f -name "*.pcap"* to locate all pcap files within *o.deer's* home directory.

![](containment4.png)

There are quite a few of them and they are in the different directories divided by dates. After checking them one by one to find something off, I've found pcap file in one of the directories that is bigger than the others.

![](containment5.png)

Now, I'm gonna turn to my personal AI chatbot, which has some tools available and one of them is *pcap_file_reassembler*, so I'm gonna use it.
I give instruction to the AI chatbot to reassemble a pcap file I've found earlier.

![](containment6.png)

And after a while, it gave me response:

![](containment7.png)

From the output txt file, that AI chatbot generate for me I found out that the attacker used prompt injection attack to extract sensitive information about one of the employees.

![](containment8.png)

There is also a password in this file: *westtechvictim1* which I'm gonna unzip file in the home directory, the file I've spotted earlier.

![](containment9.png)

I've located inflated files and I've checked straight away those two txt files that contains word "flag" in their names.
In the *thm_flags_guide.txt* I found instructions where the flag is and that I need to decode it.

![](containment10.png)

So, I've checked *thm_flags.txt* it has 500 lines of base64 encoded strings.

![](containment11.png)

In the instruction I found that the AI assistant might help in finding a correct flag. So, I asked him to do it.

![](containment12.png)

After some time the AI assistant successfully identified the flag.

**Answer: thm{23,82,20,17,53}**

![](containment13.png)