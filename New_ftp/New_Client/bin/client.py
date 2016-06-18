#!/usr/bin/env python
# coding=utf-8
import socket
import hashlib

import os
import sys
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import settings

class Client:
    def __init__(self, address):
        self.address = self.get_ip_port(address)
        self.help_message = [
            '目前自定义的命令仅支持以下操作：\n'
            '\tput|filename',
            '\tget|filename',
            '\thelp'
        ]
        self.start()
        self.cwd = ''


    def get_ip_port(self, address):
        ip, port = address.split(':')
        return (ip, int(port))

    def register(self):
        try_counts = 0
        while try_counts < 3:
            user = input('请输入用户名：')
            # user = 'kobe'
            if len(user) == 0:
                continue
            passwd = input('请输入用密码：')
            # passwd = '123'
            if len(passwd) == 0:
                continue
            pd = hashlib.sha256()
            pd.update(passwd.encode())
            self.socket.sendall('register|{}:{}'.format(user, pd.hexdigest()).encode())  # 发送加密后的账户信息
            ret = self.socket.recv(1024).decode()
            if ret == '202':
                print('注册成功请登录')
                os.mkdir(os.path.join(settings.USER_HOME_DIR, user))  # 在客户端创建一个用户家目录
                os.mkdir(os.path.join(settings.USER_HOME_DIR, user, 'download_file'))
                os.mkdir(os.path.join(settings.USER_HOME_DIR, user, 'upload_file'))
                return True
            else:
                try_counts += 1
        sys.exit("Too many attemps")

    def login(self):
        try_counts = 0
        while try_counts < 3:
            user = input('请输入用户名：')
            # user = 'kobe'
            self.user = user
            if len(user) == 0:
                continue
            passwd = input('请输入用密码：')
            # passwd = '123'
            if len(passwd) == 0:
                continue
            pd = hashlib.sha256()
            pd.update(passwd.encode())
            self.socket.sendall('login|{}:{}'.format(user, pd.hexdigest()).encode())  # 发送加密后的账户信息
            ret = self.socket.recv(1024).decode()
            if ret == '200':
                print('登陆成功！')
                self.cwd = self.socket.recv(1024).decode()
                return True
            else:
                try_counts += 1
        sys.exit("Too many attemps")

    def internet(self):
        while True:
            inp = input('[{} h(elp) q(uit)]:'.format(self.cwd))
            # inp = 'ipconfig'
            if '|' in inp:
                cmd, argv = inp.split('|')
            elif inp == 'q':
                break
            else:
                cmd = inp
                argv = None
            self.process(cmd, argv)

    def process(self, cmd, argv):               # 处理自定义的命令
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            func(argv)
        else:
            self.socket.sendall(bytes(cmd, encoding='utf-8'))       # 处理系统本身支持的命令
            ret_length = int(self.socket.recv(1024).decode())
            has_recv = 0
            data = ''
            if ret_length == 0:
                self.cwd = self.socket.recv(1024).decode()
            while has_recv < ret_length:                         # 如果命令的返回超过了1024，需要循环接受
                ret = str(self.socket.recv(1024), encoding='gbk')
                has_recv += len(ret)
                data += ret
            print(data)

    def help(self, argv=None):
        for i in self.help_message:
            print(i)

    def put(self, argv=None):
        if argv == None or argv == '':
            print("Please add the file path that you want to upload")
            return
        print('上传之前请确保的文件在用户upload文件夹下')
        file_path = os.path.join(settings.USER_HOME_DIR, self.user, 'upload_file', argv)
        if os.path.exists(file_path):
            file_size = os.stat(file_path).st_size
            file_info = {
                'file_name': argv,
                'file_size': file_size,
            }
            has_sent = 0

            self.socket.sendall(('put|{}'.format(json.dumps(file_info))).encode())
            ret = self.socket.recv(1024).decode()
            if ret == '204':
                inp = input("文件存在，是否续传？Y/N:").strip()
                if inp.upper() == "Y":
                    self.socket.sendall('205'.encode())
                    has_sent = int(self.socket.recv(1024).decode())
                else:
                    self.socket.sendall('207'.encode())
            with open(file_path, 'rb') as f:
                f.seek(has_sent)
                for line in f:
                    self.socket.sendall(line)
                    has_sent += len(line)
                    k = int((has_sent / file_size * 100))  # 下面的代码是用来显示进度条
                    table_space = (100 - k) * ' '
                    flag = k * '*'
                    time.sleep(0.05)
                    sys.stdout.write('\r{}   {:.0%}'.format((flag + table_space), (has_sent / file_size)))
            print()  # 显示换行的作用

        else:
            print('用户upload文件下不存在该文件，请重新操作')

    def get(self, argv=None):
        if len(argv) == None:
            print("Please add the file path that you want to get")
            return
        self.socket.sendall(('get|{}'.format(argv)).encode())
        ret = self.socket.recv(1024).decode()
        if ret == '300':
            file_info = json.loads(self.socket.recv(1024).decode())
            file_name = file_info['file_name']
            file_size = int(file_info['file_size'])

            file_path = os.path.join(settings.USER_HOME_DIR, self.user, 'download_file', argv)
            have_send = 0
            if os.path.exists(file_path):
                inp = input("文件存在，是否继续下载？Y/N:").strip()
                if inp.upper() == "Y":    # 断点下载
                    self.socket.sendall('300'.encode())
                    have_send = os.stat(file_path).st_size
                    self.socket.sendall(bytes(str(have_send), encoding='utf-8'))
                    f = open(file_path, 'ab')
                else:
                    self.socket.sendall('301'.encode())
                    f = open(file_path, 'wb')
            else:
                self.socket.sendall('301'.encode())  # 直接下载
                f = open(file_path, 'wb')
        else:
            sys.exit('服务器文件不存在')

        while True:
            if have_send == file_size:
                break
            try:
                ret = self.socket.recv(1024)
            except Exception as e:
                break
            f.write(ret)
            have_send += len(ret)
            k = int((have_send / file_size * 100))  # 下面的代码是用来显示进度条
            table_space = (100 - k) * ' '
            flag = k * '*'
            time.sleep(0.05)
            sys.stdout.write('\r{}   {:.0%}'.format((flag + table_space), (have_send / file_size)))
        print()  # 显示换行的作用

    # def dir(self, argv=None):
    #     self.socket.sendall('dir|{}'.format(argv).encode())
    #     ret =str(self.socket.recv(1024), encoding='gbk')
    #     print(ret)

    def start(self):
        self.socket = socket.socket()
        try:
            self.socket.connect(self.address)
        except Exception as e:
            sys.exit("Failed to connect server:%s" % e)
        print(self.socket.recv(1024).decode())
        inp = input('1、注册，2、登录，3、离开： ')
        # inp = '2'
        if inp == '1':
            if self.register():
                if self.login():     # 登陆成功后进行交互操作
                    self.internet()
        elif inp == '2':
            if self.login():
                self.internet()
        else:
            sys.exit()


if __name__ == '__main__':
    address = input('请输入FTP服务端地址(ip:port)：')
    # address = '127.0.0.1:9999'
    client = Client(address)
