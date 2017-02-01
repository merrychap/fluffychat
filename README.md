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
    - PyCrypto
    - PyQt5

### How to run application
There are two ways of running chat. If you want to create a new chat, then you should run this:
```sh
$ python3 chat.py [--create]
```
But if you want to join in existing chat, then you should know IP and connection port of a host sitting in this chat. Also you have to
specify port for receiving messages. When you know all this stuff then run next:
```sh
$ python3 chat.py [-h] [--create] [--host HOST] [-p P] [-r R] [--gui]
```
Argument | Description
-------- | -----------
**-h** | IP of a remote host
**-p** | Default connection port of a remote host
**-r** | Port for receiving data from other hosts
**--create** | Key for creating new chat
**--gui** | Run chat in gui mode

### Already done
- [x] Private messages
- [x] Rooms
- [x] Sending files
- [ ] Encryption
- [ ] Tests
- [ ] GUI
