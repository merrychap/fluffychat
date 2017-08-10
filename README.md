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
$ python3 main.py [--create] [--recv-port R]
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


### Examples
**To start** typing any command you should at first **press "enter"**
Below is placed example of creating a new chat
```sh
$ python3 main.py --create -r 8080
[*] Please, specify your username(a-zA-Z_.):> merrychap
[*] Specify your root path for storing files:> /home/merrychap/Desktop/fluffychat
('192.168.0.102', 8080)

Type "@help" for list of commands with the descriptio

[*] Enter command:> @help

======================================
Type commands with @ on the left side of a command.
List of commands:

+ help : Shows this output
+ room "room_name" : Switches to the room message mode. 
+ add_user : "username" "room_name"
+ users : Shows online users.
+ create_room "roomname" : Creates new room. 
+ user "username" : Switches to the user message mode. 
+ change_root_path "root path" : Changes the directory of storing files
+ change_visibility : Changes your visibility in the chat
+ remove_room "roomname" : Removes created room.
+ username "username" : Changes the current username. 
+ exit : Closes chat.
+ rooms : Shows available rooms.
======================================
```

The next example is connecting to the existing chat.
```sh
$ python3 main.py --host 192.168.0.102 -p 8080 -r 8080
*] Please, specify your username(a-zA-Z_.):> Holo
[*] Specify your root path for storing files:> /home/Holo/Desktop/fluffychat
('192.168.0.103', 8080)

Type "@help" for list of commands with the descriptio

[*] Enter command:> @users

======================================
+ merrychap
+ Holo
======================================
```

### Already done
- [x] Private messages
- [x] Rooms
- [x] Sending files
- [x] RSA encryption
- [ ] Tests
- [ ] GUI
