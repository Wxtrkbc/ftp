#!/usr/bin/env python
# coding=utf-8

import socketserver
import os
import sys
import subprocess
import json
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import settings


class Myhandle(socketserver.BaseRequestHandler):
    response_code_dict = {
        '200': 'Pass authentication!',
        '201': 'Wrong username or password',
        '202': 'Pass register!',
        '203': 'Register failed',
        '204': 'file existed',
        '205': 'continue put',
        '206': 'put',
        '300': 'download',
        '301': 'download again',            # 断点下载
        '302': 'download file not exits',
    }

    def handle(self):
        self.request.sendall('欢迎来到FTP服务器！'.encode())
        while True:
            data = self.request.recv(1024).decode()
            if '|' in data:
                cmd, argv = data.split('|')
            else:
                cmd = data
                argv = None
            self.process(cmd, argv)  # 所有的处理先经过 process

    def process(self, cmd, argv=None):  # 使用反射处理客户端传过来的命令（自定义的命令）
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            func(argv)
        else:
            if cmd.startswith('cd'):            #（处理cd命令，subprocess不支持cd命令）
                os.chdir(cmd.split(' ')[1])
                self.request.sendall(bytes(str(0), encoding='utf-8'))
                self.request.sendall(bytes(os.getcwd(), encoding='utf-8'))
            else:
                # ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, )
                # data = str(ret.stdout.read(), encoding='gbk')
                # data_length = len(data)
                data = subprocess.getoutput(cmd)
                data_length = len(data)
                if data_length != 0:
                    self.request.sendall(bytes(str(data_length), encoding='utf-8'))
                    self.request.sendall(bytes(data, encoding='gbk'))
                else:
                    self.request.sendall(bytes(str(0), encoding='utf-8'))
                    self.request.sendall(bytes(os.getcwd(), encoding='utf-8'))

    def put(self, argv=None):
        file_info = json.loads(argv)
        file_name = file_info['file_name']
        file_size = int(file_info['file_size'])
        file_path = os.path.join(settings.USER_HOME_DIR, 'kobe', 'upload_file', file_name)
        have_send = 0  # 已经上传的位置

        if os.path.exists(file_path):
            self.request.sendall('204'.encode())
            ret = self.request.recv(1024).decode()
            if ret == '205':  # 续传
                have_send = os.stat(file_path).st_size
                self.request.sendall(bytes(str(have_send), encoding='utf-8'))
                f = open(file_path, 'ab')
            else:
                f = open(file_path, 'wb')
        else:
            self.request.sendall('206'.encode())        # 直接上传
            f = open(file_path, 'wb')

        while True:
            if have_send == file_size:
                break
            try:
                ret = self.request.recv(1024)
            except Exception as e:
                break
            f.write(ret)
            have_send += len(ret)

    def get(self, argv=None):
        file_path = os.path.join(settings.USER_HOME_DIR, self.username, 'download_file', argv)
        if os.path.exists(file_path):
            file_size = os.stat(file_path).st_size
            file_info = {
                'file_name': argv,
                'file_size': file_size,
            }

            self.request.sendall('300'.encode())
            self.request.sendall(('{}'.format(json.dumps(file_info))).encode())
            ret = self.request.recv(1024).decode()
            if ret == '300':
                has_sent = int(self.request.recv(1024).decode())
            else:
                has_sent = 0

            with open(file_path, 'rb') as f:
                f.seek(has_sent)
                for line in f:
                    self.request.sendall(line)
        else:
            self.request.sendall('302'.encode())

    def register(self, argv=None):
        response_code = '202'
        username, _ = argv.split(':')  # 取出用户名
        f = open(settings.USER_DB_DIR, 'a+')     # 以a+模式打开的时候，指针已经到最后l
        f.seek(0)
        for line in f:
            if username == line.strip().split(':')[0]:
                response_code = '203'  # 注册失败
        if response_code == '202':
            f.write('\n' + argv)
            os.mkdir(os.path.join(settings.USER_HOME_DIR, username))  # 以用户的名字在服务器端创建一个用户家目录
            os.mkdir(os.path.join(settings.USER_HOME_DIR, username, 'download_file'))
            os.mkdir(os.path.join(settings.USER_HOME_DIR, username, 'upload_file'))
        self.request.sendall(response_code.encode())

    # def dir(self, argv=None):
    #     ret = subprocess.Popen('dir', shell=True, stdout=subprocess.PIPE, )
    #     data = str(ret.stdout.read(), encoding='gbk')
    #     self.request.sendall(bytes(data, encoding='gbk'))

    def login(self, argv):
        username, _ = argv.split(':')
        self.username = username
        with open(settings.USER_DB_DIR, 'r') as f:
            response_code = '201'
            for line in f:
                if argv == line.strip():
                    response_code = '200'  # 认证成功
        self.request.sendall(response_code.encode())
        if response_code == '200':            # 认证成功的话，先切换到用户家目录，在将当前目录发送过去
            os.chdir(os.path.join(settings.USER_HOME_DIR, username))
            self.request.sendall(bytes(os.getcwd(), encoding='utf-8'))


if __name__ == '__main__':
    address = ('127.0.0.1', 9999)
    server = socketserver.ThreadingTCPServer(address, Myhandle)
    server.serve_forever()
