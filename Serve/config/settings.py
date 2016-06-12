#!/usr/bin/env python
# coding=utf-8

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

USER_BASE_DIR = os.path.join(BASE_DIR, 'Serve', 'db', 'user_db')

USER_HOME_DIR = os.path.join(BASE_DIR, 'Serve', 'user_home')

USER_LOG_DIR = os.path.join(BASE_DIR, 'Serve', 'Log')