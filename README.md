# Decentralized console chat

### General description
You can communicate with people by writing messages and sending different files. This chat provides rooms and private messages between users.
For detailed description see DECOMPOSITION.md file

### Where is log file?
Log file is app.log. You can see it by typing next:
```sh
$ vim app.log
```

### Requirements
- Python 3.*
    - netifaces

### How to run application
There are two ways of running chat. If you want to create a new chat, then you should run this:
```sh
$ python3 chat_console.py
```
But if you want to join in existed chat, then you should know ip of a host sitting in this chat and then run next:
```sh
$ python3 chat_console.py -H [ip] -sP [connection port] -rP [receiving port]
```
Argument | Description
-H | IP of remote host
-sP | Default connection port of remote host
-rP | Port of receiving data from other hosts

### Already done
- [x] Private messages
- [x] Rooms
- [x] Sending files
- [ ] Tests
- [ ] GUI (?)
