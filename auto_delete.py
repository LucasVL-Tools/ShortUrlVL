import os, time, shutil
from config import delete_interval
print("Auto delete started!")

while True:
    time.sleep(5)
    five_days_ago = time.time() - (delete_interval)
    root = "./urls"
    
    for i in os.listdir(root):
        path = os.path.join(root, i)
        if os.stat(path).st_mtime <= five_days_ago:
            try:
                os.remove(path)
            except:
                print("Could not remove file:", i)
