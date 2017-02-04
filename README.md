# Decentralized chat

### General description
You can communicate with people by writing messages and sending different files. This chat provides rooms and private messages between users. Chat is protected by RSA encryption.

For detailed description see DECOMPOSITION.md file.

### Some details
Chat works only in **local networks** due to the fact that this is under development.

### Requirements
- Python 3.*
    - netifaces
    - PyCrypto
    - PyQt5

### Architecture
Here will be a little description about architecture.

### Example of using
Here will be examples.

### Where is log file?
Log file is __app.log__. You can see it by typing next:
```sh
$ vim app.log
```

### How to run application
There are two ways of running chat. If you want to create a new chat, then you should run this:
```sh
$ python3 chat.py [--create] [-r R]
```
But if you want to join in existing chat, then you should know IP and connection port of a host sitting in this chat. Also you have to
specify port for receiving messages. When you know all this stuff then run next:
```sh
$ python3 chat.py [-h] [--create] [--host HOST] [-p P] [-r R] [--gui] [--dis-enc]
```
Argument | Description
-------- | -----------
**--host** | IP of a remote host
**-p** | Default connection port of a remote host
**-r** | Port for receiving data from other hosts
**--create** | Key for creating new chat
**--gui** | Run chat in GUI mode
**--dis-enc** | Disable RSA encryption. It means when a host from the chat sends you a message it will not be encrypted for you.

### Already done
- [x] Private messages
- [x] Rooms
- [x] Sending files
- [x] RSA encryption
- [ ] Tests
- [ ] GUI
