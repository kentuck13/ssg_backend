import os

directories = ['./content/', './output/', './templates/']
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
