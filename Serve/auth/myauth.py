#!/usr/bin/env python
# coding=utf-8


import hashlib
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from Serve.config import settings


def sha(password):
    passwd = hashlib.sha256(bytes('wxtrkbc', encoding='utf-8'))
    passwd.update(bytes(password, encoding='utf-8'))
    return passwd.hexdigest()


def register(user, passwd):
    with open(settings.USER_BASE_DIR, 'a') as f:
        f.write('{}:{}\n'.format(user, sha(passwd)))
        return True

def login(user, passwd):
    with open(settings.USER_BASE_DIR, 'r', encoding='utf-8')as f:
        for line in f:
            info = line.strip().split(':')
            if user == info[0] and sha(passwd) == info[1]:
                return True
        return False
