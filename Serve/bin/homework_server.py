#!/usr/bin/env python
# coding=utf-8
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from Serve.auth import myauth
from Serve.models import *
from Serve.config import settings
import socketserver
import subprocess
import logging


def register(mysocket, username, passwd):  # 服务端用来处理客户端注册
    mylog(os.path.join(settings.USER_LOG_DIR, username), 'Register')
    if myauth.register(username, passwd):
        mysocket.sendall(str2bytes('注册成功现在可以登录了!'))
        homepath = os.path.join(settings.USER_HOME_DIR, username)
        logpath = os.path.join(settings.USER_LOG_DIR, username)
        os.mkdir(homepath)  # 创建用户家目录
        f = open(logpath, 'w')
        f.close()


def login(mysocket, username, passwd):  # 服务端用来处理客户端登陆
    mylog(os.path.join(settings.USER_LOG_DIR, username), 'Login')
    mysocket.sendall(str2bytes('登录成功!'))
    mysocket.sendall(str2bytes('1'))  # 作为判断的标志
    os.chdir(os.path.join(settings.USER_HOME_DIR, username))  # 切换到用户家目录


def upfile(mysocket, username):  # 服务端用来处理客户端上传文件
    mylog(os.path.join(settings.USER_LOG_DIR, username), 'upload')
    file_name = bytes2str(mysocket.recv(1024))  # 接受客户端要上传的文件名
    done_file_size = 0
    if os.path.exists(os.path.join(settings.USER_HOME_DIR, username, 'upfile', file_name)):
        mysocket.sendall(str2bytes('是否要续传'))
        ret = mysocket.recv(1024)
        if bytes2str(ret).upper() == 'Y':
            f = open(os.path.join(settings.USER_HOME_DIR, username, 'upfile', file_name), 'ab')
            done_file_size = os.stat(os.path.join(settings.USER_HOME_DIR, username, 'upfile', file_name)).st_size
            mysocket.sendall(str2bytes(str(done_file_size)))
        else:
            f = open(os.path.join(settings.USER_HOME_DIR, username, 'upfile', file_name), 'wb')
    else:
        mysocket.sendall(str2bytes('重新上传'))
        f = open(os.path.join(settings.USER_HOME_DIR, username, 'upfile', file_name), 'wb')
    file_size = int(bytes2str(mysocket.recv(1024)))
    mysocket.sendall(str2bytes('ok'))  # 发送一个确认应答，解决粘包问题
    while True:
        if done_file_size == file_size:
            break
        try:
            ret = mysocket.recv(1024)
        except Exception as e:
            break
        f.write(ret)
        done_file_size += len(ret)


def operat(mysocket, username):  # 接受客户端输入的命令，并将结果返回
    while True:
        rec = mysocket.recv(1024)
        commands = bytes2str(rec)  # 接受输入的命令
        mylog(os.path.join(settings.USER_LOG_DIR, username), commands)
        if commands == 'q':
            break
        # if commands.startswith('cd'):
        #     cm, file_path = commands.split(' ', 1)
        #     if file_path == '..':
        #         os.chdir(os.path.dirname(__file__))
        #         print(os.getcwd())
        #     else:
        #         os.chdir(file_path)
        #     mysocket.sendall(str2bytes(str(0)))
        #     mysocket.sendall(str2bytes(commands+'操作成功'))
        # else:
        data = subprocess.getoutput(commands)
        mysocket.sendall(str2bytes(str(len(data))))  # 先发送命令执行结果的大小
        mysocket.sendall(str2bytes(data))  # 发送命令执行的结果


def mylog(path, msg):  # 日志模块用来纪录客户端用户的操作
    logging.basicConfig(filename=path,
                        format='%(asctime)s-%(name)s-%(levelname)s-%(module)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %p',
                        level=10,
                        )
    logging.log(10, msg)


class myTCPHandle(socketserver.BaseRequestHandler):
    def handle(self):
        print("connet from %s:%s" % self.client_address)  # 还有一个self.server
        conn = self.request
        conn.sendall(str2bytes('1、注册，2、登陆，3、离开'))
        while True:
            ret = conn.recv(1024)
            if bytes2str(ret) == '1':  # 注册
                username = bytes2str(conn.recv(1024))
                passwd = bytes2str(conn.recv(1024))
                register(conn, username, passwd)  # 注册
            elif bytes2str(ret) == '2':  # 登陆
                username = bytes2str(conn.recv(1024))
                passwd = bytes2str(conn.recv(1024))
                if myauth.login(username, passwd):  # 登陆认证成功的话
                    login(conn, username, passwd)  # 执行服务端登陆程序
                    while True:
                        ret1 = conn.recv(1024)
                        if bytes2str(ret1) == '1':  # 客户端要上传文件
                            upfile(conn, username)
                        elif bytes2str(ret1) == '2':  # 客户端要操作主机
                            operat(conn, username)
                        else:
                            break
                else:
                    conn.sendall(str2bytes('登录失败'))
                    conn.sendall(str2bytes('0'))
            else:
                break


if __name__ == '__main__':
    address = ('127.0.0.1', 9999)
    server = socketserver.ThreadingTCPServer(address, myTCPHandle)
    server.serve_forever()
