#!/usr/bin/env python
# coding=utf-8

import socket
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from Serve.config import settings
from Serve.auth import myauth
from Serve.models import *
import time



def register(client_socket, inp):  # 处理客户端程序注册代码
    client_socket.sendall(str2bytes(str(inp)))
    user = input('请输入用户名：')
    client_socket.sendall(str2bytes(user))
    passwd = input('请输入用密码：')
    client_socket.sendall(str2bytes(passwd))
    ret = client_socket.recv(1024)
    print(bytes2str(ret))


def login(client_socket, inp):  # 处理客户端程序登陆代码
    client_socket.sendall(str2bytes(str(inp)))

    user = input('请输入用户名：')
    client_socket.sendall(str2bytes(user))

    passwd = input('请输入用密码：')
    client_socket.sendall(str2bytes(passwd))

    ret = client_socket.recv(1024)  # 获取登录成功的消息
    print(bytes2str(ret))


def upfile(client_socket):  # 处理客户端程序上传文件代码
    file_list = os.listdir(os.path.join(settings.BASE_DIR, 'Client', 'client_file'))
    file_str = '\n'.join([i for i in file_list if not i.startswith('.')])
    print('该目录下有以下文件可上传：\n{}'.format(file_str))
    has_up = 0  # 纪录断点续传的位置
    file_name = input('请输入你要传的文件名: ')

    client_socket.sendall(str2bytes(file_name))  # 发送要上传的文件名
    data = client_socket.recv(1024)
    if bytes2str(data) == '是否要续传':
        inp = input('是否要续传y/n: ')
        client_socket.sendall(str2bytes(inp))
        if inp.upper() == 'Y':
            has_up = int(bytes2str(client_socket.recv(1024)))
            print(has_up)
    else:
        pass
    file_size = os.stat(os.path.join(settings.BASE_DIR, 'Client', 'client_file', file_name)).st_size  # 文件大小
    client_socket.sendall(str2bytes(str(file_size)))
    if bytes2str(client_socket.recv(1024)) == 'ok':  # 收到服务端的确认后再上传，解决粘包问题
        with open(os.path.join(settings.BASE_DIR, 'Client', 'client_file', file_name), 'rb') as f:
            f.seek(has_up)
            for line in f:
                client_socket.sendall(line)
                has_up += len(line)
                k = int((has_up / file_size * 100))  # 下面的代码是用来显示进度条
                table_space = (100 - k) * ' '
                flag = k * '*'
                time.sleep(0.05)
                sys.stdout.write('\r{}   {:.0%}'.format((flag + table_space), (has_up / file_size)))
        print()  # 显示换行的作用


def operating(client_socket):  # 处理客户端输入命令来操作服务端
    while True:
        com = input('请输入你要操作的指令(q退出): ')
        if com == 'q':
            client_socket.sendall(str2bytes(com))
            break
        client_socket.sendall(str2bytes(com))
        result_len = int(bytes2str(client_socket.recv(1024)))  # 接受命令执行结果的长度
        has_recv = 0
        data = ''
        # if result_len == 0:
        #     data = bytes2str(client_socket.recv(1024))
        while has_recv < result_len:
            ret = bytes2str(client_socket.recv(1024))
            has_recv += len(ret)
            data += ret
        print(data)


def main():
    client_socket = socket.socket()
    client_socket.connect(('127.0.0.1', 9999,))
    ret = client_socket.recv(1024)  # 阻塞中
    print(bytes2str(ret))
    while True:
        inp = int(input('请输入序号: '))
        if inp == 1:
            register(client_socket, inp)  # 客户端注册
        elif inp == 2:
            login(client_socket, inp)
            retflag = client_socket.recv(1024)  # 获取判断登陆成功的标志位
            if bytes2str(retflag) == '1':  # 登陆成功的话
                while True:
                    inp = input('1、上传文件，2、操作主机，3、离开: ')
                    client_socket.sendall(str2bytes(inp))
                    if inp == '1':  # 上传文件
                        upfile(client_socket)
                    elif inp == '2':  # 操作主机
                        operating(client_socket)
                    else:
                        break
                break
            else:
                break
        else:
            break
    client_socket.close()


if __name__ == '__main__':
    main()
