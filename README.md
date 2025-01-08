# Float
This project uses [croc](https://github.com/schollz/croc)  

A group of crocodiles is called a *float.*  

**You must install croc on the machine running the bot.**  `curl https://getcroc.schollz.com | bash` or [install a release](https://github.com/schollz/croc/releases) and update `croc_path` in the config.json to point to the binary.

You need a .env file with the BOT_TOKEN key.

If running via docker compose a volume for the files will be mounted at `/home/float/files`.

This bot provides simple file storage and transfers localized to the discord server(s) it is in.  

Under ideal conditions the upload and download is faster than Google Drive or other cloud storage alternatives, more secure, and much faster to interface with.  

To install croc on my friends machines and add send and receive options to their context menus I use this script: [windows](https://gist.github.com/Malcolm-Q/f933b0a5bbf43f9994b8fe69c589ac8a) & [Linux](https://gist.github.com/Malcolm-Q/bc7c98b4996c97f90ec6a5a1781e2bf6)  
Here's what it looks like:  
![send with croc img](https://github.com/user-attachments/assets/1978d0d2-1d7d-40ba-b737-5b67dfca4fba)  
![receive with croc img](https://github.com/user-attachments/assets/c02f4922-bfae-466f-9a14-a4a14d0ccac5)

# Bot Commands:
- /upload --code
    - Allows you to upload a file to the server folder with croc.
    - The code arg is mandatory and must be a valid croc code.
- /serve --file
    - Allows you to request a file.
    - File name does not have to be an exact match. EX: `my_` will return `MY_GAME/`.
    - Will time out after 60 seconds if you do not enter the code provided into croc.
- /ls --filter --folder
    - Lists files on the server folder.
    - Supplying the name of a folder will list the contents of said folder.
    - Supply a filter arg is equivalent to ls | grep "arg".
- /rm --target
    - Removes a file or folder. Has to be an exact match.
- /mv --target --output
    - moves / renames a file.
- /ps
    - Lists processes
- /kill --id
    - Kills the process listed in /ps
 
# Example Usage
You make a build of a game you're working on and want to test it with your friends.  
Right click the folder and click `send with croc`, the code will be copied to your clipboard.  
In discord do `/upload <code>`  

Notify your friends it is uploaded.

They can do `/serve <folder_name>`
Then in file explorer right click where they want to receive it, hit `receive with croc` and paste the code the bot sent.

croc is is licensed under the MIT License. See LICENSE or https://github.com/schollz/croc for details.
