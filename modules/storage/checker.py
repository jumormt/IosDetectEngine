import paramiko
import os
import sqlite3
import signal
from Util.utils import Utils
import config
import data
import subprocess
import plistlib

class Checker():
    def __init__(self, files, type):

        self.results = dict()
        self.input_results = dict()
        self.keyiv_results = dict()
        self.txt_results = dict()

        self.type = type

        self.files = files
        self.input_list = list(data.input_list)

        self.txt_list = self.read_txt()
        self.keyiv_list = self.get_key_iv()
        self.cur_file = ''

    def read_txt(self):
        txt_list = list()
        file = open('./config/sensitive.txt')
        lines = file.readlines()
        for line in lines:
            line = line.strip('\n')
            txt_list.append(line)
        return txt_list

    def get_key_iv(self):
        keyiv_list = list()
        json_list = data.dynamic_json.cccrtpy_json_list
        if json_list:
            for json in json_list:
                if "key" in json and json["key"] != "":
                    keyiv_list.append(json["key"])
                if "iv" in json and json["iv"] != "":
                    keyiv_list.append(json["iv"])
        return keyiv_list

    def parse_file(self, local_file_path):
        if self.type == 'PLIST':
            self.parse_plist(local_file_path)
        elif self.type == 'SQL':
            self.read_db(local_file_path)
        elif self.type == 'LOG':
            self.read_log(local_file_path)
        else:
            pass

    def start(self):
        t = paramiko.Transport(config.mobile_ip, config.ssh_port)
        t.connect(username=config.mobile_user, password=config.mobile_password)
        sftp = paramiko.SFTPClient.from_transport(t)
        count = 0
        for file in self.files:
            self.cur_file = file
            file_name = '{}_{}'.format(os.path.basename(file), count)
            local_file_path = './temp/{}/files/{}'.format(data.start_time, file_name)
            sftp.get(file, local_file_path)
            try:
                signal.signal(signal.SIGALRM, self.my_handler)
                signal.alarm(60 * 2)
                self.parse_file(local_file_path)
                signal.alarm(0)
            except Exception, e:
                data.logger.debug(e)
                # print 'time_out:', file
                # Utils.printy_result('Download db files from app', 0)
            count += 1
        self.results["input"] = self.input_results
        self.results["keyiv"] = self.keyiv_results
        self.results["txt"] = self.txt_results
        t.close()

    def read_log(self, file):
        # clear the log in iphone
        Utils.cmd_block('cat /dev/null > /var/log/syslog')

        log_file = open(file)
        while 1:
            line = log_file.readline()
            self.check_log_line(line)

    def check_log_line(self, line):
        for black_item in self.input_list:
            if black_item in line:
                if self.file not in self.input_results:
                    self.input_results[self.cur_file]=[]
                info = (line, black_item)
                self.input_results[self.cur_file].append(info)

        for black_item in self.txt_list:
            if black_item in line:
                if self.file not in self.txt_results:
                    self.txt_results[self.cur_file]=[]
                info = (line, black_item)
                self.txt_results[self.cur_file].append(info)

        for black_item in self.keyiv_list:
            if black_item in line:
                if self.file not in self.keyiv_results:
                    self.keyiv_results[self.cur_file]=[]
                info = (line, black_item)
                self.keyiv_results[self.cur_file].append(info)

    def read_db(self, file):
        conn = sqlite3.connect(file)
        c = conn.cursor()
        # get all tables
        c.execute("select name from sqlite_master where type='table' order by name")
        tables = c.fetchall()
        for table in tables:
            # self.cur_table = table[0]
            query = 'select * from ' + table[0]
            c.execute(query)
            for row in c:
                self.check_row(row, table[0])
        conn.close()

    def check_row(self, row, table):
        for i in range(len(row)):
            for black_item in self.input_list:
                try:
                    if black_item in str(row[i]):
                        if self.cur_file not in self.input_results:
                            self.input_results[self.cur_file] = []
                        info = (table, str(row[i]), black_item)
                        self.input_results[self.cur_file].append(info)
                except:
                    # Util.printy_result('READ ROW FROM DB ', 0)
                    pass
            for black_item in self.keyiv_list:
                try:
                    if black_item in str(row[i]):
                        if self.file not in self.keyiv_results:
                            self.keyiv_results[self.cur_file] = []
                        info = (table, str(row[i]), black_item)
                        self.keyiv_results[self.cur_file].append(info)
                except:
                    # Util.printy_result('READ ROW FROM DB ', 0)
                    pass
            for black_item in self.txt_list:
                try:
                    if black_item in str(row[i]):
                        if self.cur_file not in self.txt_results:
                            self.txt_results[self.cur_file] = []
                        info = (table, str(row[i]), black_item)
                        self.txt_results[self.cur_file].append(info)
                except:
                    # Util.printy_result('READ ROW FROM DB ', 0)
                    pass

    def parse_plist(self, file):
        pl_cmd = 'plutil -convert xml1 '+file
        subprocess.call(pl_cmd, shell=True)
        try:
            pl = plistlib.readPlist(file)
            key_path = []
            self.parse_element(pl, key_path)
        except Exception, e:
            # print 'plist error'
            data.logger.info(e)

    def parse_element(self, item, key_path):
        if isinstance(item, list):
            for each in item:
                self.parse_element(each, key_path)
        elif isinstance(item, dict):
            for key in item.keys():
                key_path.append(key)
                self.parse_element(item[key], key_path)
                key_path.remove(key)
        else:
            # parse input list
            for black_item in self.input_list:
                if (black_item in str(key_path)) or (black_item in str(item)):
                    if self.cur_file not in self.input_results:
                        self.input_results[self.cur_file] = []
                    info = (str(key_path), str(item), black_item)
                    self.input_results[self.cur_file].append(info)

            # parse key iv list
            for black_item in self.keyiv_list:
                if (black_item in str(key_path)) or (black_item in str(item)):
                    if self.cur_file not in self.keyiv_results:
                        self.keyiv_results[self.cur_file] = []
                    info = (str(key_path), str(item), black_item)
                    self.keyiv_results[self.cur_file].append(info)

            # parse txt list
            for black_item in self.txt_list:
                if (black_item in str(key_path)) or (black_item in str(item)):
                    if self.cur_file not in self.txt_results:
                        self.txt_results[self.cur_file] = []
                    info = (str(key_path), str(item), black_item)
                    self.txt_results[self.cur_file].append(info)

    def my_handler(self, signum, frame):
        raise AssertionError
