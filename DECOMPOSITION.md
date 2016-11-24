# Decomposition file

### Description
This is decomposition file with description by each directory and file

### Directory tree
├── app.log
├── chat_console.py
├── chats
│   └── console
│       ├── base_chat.py
│       ├── main_chat.py
│       ├── room_chat.py
│       └── user_chat.py
├── database
│   ├── chat_dbhelper.py
│   └── db_helper.py
├── database.db
├── DECOMPOSITION.md
├── network
│   └── client.py
├── opt
│   └── appearance.py
├── README.md
└── scripts
    └── ...

__Summary__: 5 directories, 13 files, 2055 lines


### Directory description
- chats/ ─ It contains modules for different types of chat. For instance, room or user chat
- chats/console/ ─ There are placed console chat modules
- database/ ─ Contains modules for working with application database
- network/ ─ Module for networking is placed here
- opt/ ─ Different optional modules that help work with chat. For example, module with colors class

### Files description
#### Files that contain information
- ```app.log``` ─ Chat's logging file
- ```database.db``` ─ Application inner database
- ```README.md``` ─ Readme file
- ```DECOMPOSITION.md``` ─ File with decomposition (current file)

#### Chats
- ```chat_console.py``` ─ This script contains main function that runs all application
- ```base_chat.py``` ─ Provides all base functionality of chats. Also connects chat with database by using ```chat_dbhelper.py```
- ```main_chat.py``` ─ Main page of the chat, where you can open room or private chats
- ```room_chat.py``` ─ Functionality of rooms are placed here
- ```user_chat.py``` ─ Module for private communication between users

#### Database
- ```chat_dbhelper.py``` ─ Provides connection between chats and database functionality
- ```db_helper.py``` ─ Module for working with database

#### Networking
- ```client.py``` ─ All networking is provided by this module

#### Optional
- ```appearance.py``` ─ For now, it contains class with colors

#### Scripts
- ...
