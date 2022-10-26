import os, time
from config import max_age
print("Auto delete started!")
root="./urls"

while True:
    time.sleep(25)
    for i in os.listdir(root):
        path = os.path.join(root, i)
        file = open(path, "r")
        try:
            expiration = file.readlines()[3][:-1]
            if int(float(expiration)) <= time.time():
                try:
                    os.remove(path)
                    print("Auto deleted file:", i)
                except:
                    print("Could not remove file:", i)
        except:
            pass

