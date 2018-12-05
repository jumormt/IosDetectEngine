#coding=utf-8
import sys
sys.path.append('modules/static/gen-py')
import os
import time
import socket
import clint
import thread
import logging
from modules import *
import modules.static.static_analyse as static_analyze
from Util import ssh, MD5, socketServer, tcprelay
from Util.utils import Utils
from PreProcess import should_install, pre_clutch
from Report.DocGenerator import Generator
import data
import config
from modules.dynamic.AppDynamicInfo import AppDynamicInfo
from modules.dynamic.open_app import open_some_app
from PreProcess.decryptThread import decryptThread
from datetime import datetime


class IOS():
    def __init__(self, ipa_path, bundle_id, connector, static_type=None):
        data.static_type = static_type
        if not data.logger:
            data.logger = logging.getLogger('root')
        self.status = 0  # 作为检测任务，与server.py中对应
        IOS.connect(connector)  # 与测试机建立连接
        Utils.build()  # 在测试机中建立文件夹，用于检测的中间文件存储
        pre_status = IOS.prepare_for_basic_info(ipa_path, bundle_id)
        if pre_status == 4:
            self.status = 4
        elif pre_status == 5:
            self.status = 5
        self.t_static = static_analyze.static_analyzer()
        self.app_dynamic_info = AppDynamicInfo(data.app_bundleID)
        self.t_socket = socketServer.SocketServerThread(self.app_dynamic_info)
        self.server = Nessus()


    @staticmethod
    def prepare_for_basic_info(ipa_path, bundle_id):
        # data.app_dict = Utils.ret_LastLaunch()  # set app_dict
        # if ipa_path:
        #     should_install.install_ipa_from_local(ipa_path)  # set bundleID
        # elif bundle_id:
        #     data.app_bundleID = bundle_id
        # else:
        #     should_install.ask_for_user_choose()
        #     Utils.getInstalledAppList()  # set bundle_ID
        # Metadata().get_metadata()
        # print data.app_bundleID
        # pre_clutch.clutch()

        # data.app_dict = Utils.ret_last_launch()   !!! NOT SUPPORTED BY iOS9 ANYMORE
        if not data.app_dict:
            data.app_dict = Utils.ret_last_launch_9()  # 获取当前已安装应用列表
        if ipa_path:  # 来自于平台
            try:
                should_install.install_ipa_from_local(ipa_path)  # set bundleID
            except Exception, e:
                Utils.printy("Cannot install ipa ", 2)
                data.logger.debug(e)
                return 4  # 安装失败
        elif bundle_id:  # 来自于平台
            data.app_bundleID = bundle_id
        else:
            should_install.ask_for_user_choose()

        data.app_dict = Utils.ret_last_launch_9()
        Metadata().get_metadata()
        Utils.printy("start analyse " + data.app_bundleID, 4)
        if pre_clutch.clutch():
            pass
        else:
            return 5
        # if IOS.decrypt() == 5:
        #     return 5

        return 0

    @staticmethod
    def connect(connector):
        if connector == "u":
            thread.start_new_thread(tcprelay.main, (['-t', '22:2222'], ))
            time.sleep(5)
        while True:
            try:
                Utils.printy('Conneting..', 0)
                data.client = ssh.set_ssh_conn(config.mobile_ip, config.ssh_port, config.mobile_user, config.mobile_password)
                break
            except socket.error:
                time.sleep(5)
                Utils.printy_result('Operation timed out.', 0)

    def start_static_analyse(self):
        if data.static_type:
            self.t_static.start()
        else:
            data.status ^= 0b0010
        time.sleep(2)  # make sure java -jar in thread can get into directory lib


    def finish_static_analyse(self):
        self.t_static.join()
        Utils.printy_result('Static Analyse.', 1)
        data.status ^= 0b0010
        return True

    def start_dynamic_check(self):
        open_some_app(data.app_bundleID)
        self.t_socket.start()
        # time.sleep(1)
        # while True:
        #     user_input = raw_input(clint.textui.colored.yellow('> >> >>> Do you want to detect MITM? [Y/N] > '))
        #     if user_input == 'Y' or user_input == 'y':
        #         # print '================================================================='
        #         # print '=   If you want to detect the MITM, please config on phone:     ='
        #         # print '=   OPEN the "MITM" and CLOSE the "Traffic"!                    ='
        #         # print '================================================================='
        #         Utils.printy('CONFIG YOUR PHONE : MITM ON and Traffic OFF', 3)
        #         # Util.printy('Start MITM detect.', 0)
        #         while not data.MITM_Done:
        #             time.sleep(2)
        #         Utils.printy_result('MITM Check.', 1)
        #         Utils.printy("CONFIG YOUR PHONE : MITM OFF and Traffic ON", 3)
        #         break
        #     elif user_input == 'N' or user_input == 'n':
        #         data.MITM_Done = True
        #         Utils.printy("CONFIG YOUR PHONE : MITM OFF and Traffic ON", 3)
        #         break
        #     else:
        #         Utils.printy('Invalid input! Please input Y or N', 1)

    def finish_dynamic_check(self):
        self.t_socket.join()
        data.dynamic_json = self.app_dynamic_info
        Utils.printy_result("Dynamic Check .", 1)
        self.analyse()
        IOS.storage_check()
        data.status ^= 0b0001
        return True

    def finish_server_scan(self):
        self.server.join()
        Utils.printy_result('Server Scan.', 1)

    @staticmethod
    def storage_check():
        data.db_file_results = sql_check()
        Plist().check()
        # detect keychain
        keychain_checker = Keychain()
        data.keychain_values = keychain_checker.dump()

    @staticmethod
    def binary_check():
        SharedLibrary().get()
        get_seg_info()
        protect_check().check()
        String().get_strings()
        Utils.printy_result('Binary Check', 1)

    def server_scan(self, hosts):
        # print "hosts", hosts
        self.server.set_args(hosts, data.app_bundleID)
        self.server.start()

    def analyse(self):
        # copy the input data to class data
        input_md5_list = MD5.get_md5(self.app_dynamic_info.user_input)
        input_md5_list.extend(self.app_dynamic_info.user_input)
        data.input_list = set(input_md5_list)
        # print data.input_list

        # detect sensitive content according to user input
        input_json_parser = input_parser()
        input_json_parser.parse_dynamic_info_for_input(self.app_dynamic_info)
        data.dynamic_sensitive_json = self.app_dynamic_info.sensitive_json

        # parse traffic json
        traffic_parser = TrafficParser(self.app_dynamic_info.traffic_json_list)
        traffic_parser.start_parser()
        data.traffic_unsafe_result = traffic_parser.result

        # parse MITM json
        mitm_parser = MitmParser(self.app_dynamic_info.mitm_list)
        mitm_parser.start_parse()
        data.mitm_results = mitm_parser.results

        # detect Hard Code
        hardcode_detect = HardCodeDetect(self.app_dynamic_info.cccrtpy_json_list)
        hardcode_detect.start_detect()
        # print 'hardcode:',hardcode_detect.result

        fuzzer = url_scheme_fuzzer(self.app_dynamic_info)
        fuzzer.fuzz()

    def paltform_entrance(self):
        self.start_dynamic_check()
        IOS.binary_check()
        if data.strings:
            self.server_scan(','.join(String().get_url(data.strings)))
        self.start_static_analyse()
        # data.status ^= 0b0010
        self.check_status()
        data.dynamic_json = self.app_dynamic_info
        self.analyse()
        IOS.storage_check()
        report_gen = Generator()
        report_gen.generate()
        if data.static_type == 'pdf':
            Utils.zip_results()
        Utils.printy("Analyze Done.", 4)
        # if self.finish_dynamic_check():
        #     self.analyse()
        #     IOS.storage_check()
        # if self.finish_static_analyse():
        #     report_gen = Generator()
        #     report_gen.generate()
        # if self.finish_server_scan():
        self.clean()

    def stand_alone_entrance(self):
        # self.start_dynamic_check()
        IOS.binary_check()
        # self.server_scan(','.join(String().get_url(data.strings)))
        self.start_static_analyse()
        # self.check_status()
        data.dynamic_json = self.app_dynamic_info
        self.analyse()
        IOS.storage_check()
        report_gen = Generator()
        report_gen.generate()
        Utils.printy("Analyze Done.", 4)
        self.clean()

    def check_status(self):
        process_time = 0
        while True:
            time.sleep(10)
            process_time += 10
            status = data.status & 0b11
            if status == 0b11:
                break
            # dynamic not finished
            elif status == 0b10:
                if process_time >= 180:
                    self.t_socket.stop()
                    # self.t_socket.join()
                    Utils.printy_result("Stop Dynamic Analysis, Timeout", 0)
                    break
            else:
                continue

    @staticmethod
    def decrypt():
        dTask = decryptThread()
        startime = datetime.now()
        dTask.start()
        while True:
            if dTask.status == "done":
                break
            time.sleep(5)
            period = (datetime.now() - startime).seconds
            if period > 10 and dTask.status == "clutching":
                dTask.stop()
                dTask.join()
                return 5
            # if period > 5 * 60 and dTask.status == "dump_fail":
            #     return 5

    def clean(self):
        data.client.close()


# IOS(None, None, 'w').paltform_entrance()
IOS(None, None, 'w', static_type='xml').stand_alone_entrance()

