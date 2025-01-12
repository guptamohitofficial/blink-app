### List of challenges faced and resolved
- Building multithreaded UI - tkinter main loop doesn't want to be in child thred, trying to fit camera frame into it, implemented json api for now
- Given code had lot more than required functionality, copied the minimum and just converted to do only what is required.
- Building executable, pyinstaller needs to know about dat file, i'm passing the path but its crashing, improving the loggin of the app itself to figure it out.
- Gracefullt stopping all - Usually .join() closes the thread but flask in it self is a continious loop listening http requests and we also need to handle the open cv loop, used the given signal mechanism to deal with it.