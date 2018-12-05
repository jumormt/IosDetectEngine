#_*_ coding:utf8 _*_
import threading
import socket
import json
from Util.ssh import set_ssh_conn
import config
import time

class ApplistThread(threading.Thread):


    def run(self):
        client = set_ssh_conn(config.mobile_ip, config.ssh_port, config.mobile_user, config.mobile_password)
        socket_settings_plist = '/var/mobile/Library/Preferences/com.softsec.iosdefect.socket.plist'
        self.cmd_block(client,
                        "plutil -key {} -value {} {}".format("ServerIP", config.socket_ip, socket_settings_plist))
        self.cmd_block(client,
                        "plutil -key {} -value {} {}".format("ServerPort", config.socket_port, socket_settings_plist))
        client.close()

        HOST = config.socket_ip
        PORT = config.socket_port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, int(PORT)+1))
        s.listen(1)
        while 1:
            conn, addr = s.accept()
            input_data = conn.recv(20480)
            print input_data
            print len(input_data)
            input_data = input_data[0:-1]  # 不确定要不要
            input_dict = json.loads(input_data)
            print input_dict
            self.writeAppListToFile(input_dict)

    def writeAppListToFile(self, app_info):
        f = open('apps.txt','w')
        lines = []
        for bundle_id in app_info:
            line = bundle_id + ' * ' + app_info[bundle_id] + ' *\r\n'
            lines.append(line)
        lines[-1] = lines[-1][0:-2]
        f.writelines(lines)
        print 'write done'
        f.close()

    def cmd_block(self, client, cmd):
        while True:
            try:
                stdin, out, err = client.exec_command(cmd)
                break
            except Exception, e:
                time.sleep(5)
        if type(out) is tuple: out = out[0]
        str = ''
        for line in out:
            str += line
        return str


if __name__ == '__main__':

    t = ApplistThread()
    t.start()

