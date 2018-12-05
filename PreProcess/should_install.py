#coding=utf-8
import os
from Util.utils import Utils
import data
import commands
from modules.dynamic.open_app import open_some_app
import Util.plistlib as plistlib
import time
import config
import clint
import zipfile
import re
import simplejson
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def ask_for_user_choose():
    Utils.printy('[1]: I have installed the app .', 1)
    Utils.printy('[2]: I have the ipa file local to install.', 1)
    while True:
        user_choose_input = raw_input(clint.textui.colored.yellow("> >> >>> Enter your choice please [1/2]: > "))
        if user_choose_input == '1':
            Utils.getInstalledAppList()
            break
        elif user_choose_input == '2':
            if install_ipa_from_local(""):
                break
            else:
                continue
        else:
            Utils.printy('Invalid input!', 2)


def install_ipa_from_local(ipa_path):
    if ipa_path:  # 从平台下发的任务，经由这个方法，ipa_path有值
        ipa = zipfile.ZipFile(ipa_path)
        pat = re.compile("Payload[/\\\][\w.]+[/\\\]Info.plist")
        for name in ipa.namelist():
            if pat.search(name):
                plist_path = name
                break
                # plist_path = ipa.extract(name)
                # plist = plistlib.readPlist(plist_path)
                # data.app_bundleID = plistlib.readPlist(plist_path)["CFBundleIdentifier"]
                # print data.app_bundleID

    else:  # 从单机版入口，ipa_path为空，需要实时要求用户输入
        while True:
            ipa_path = raw_input(clint.textui.colored.yellow("> >> >>> Input the Path: > ")).strip()
            if not os.path.exists(ipa_path):
                Utils.printy_result('No such file ', 0)
            elif not ipa_path.endswith("ipa"):
                Utils.printy_result('Not ipa file ', 0)
            else:
                break

    # sftp to iPhone
    Utils.sftp_put(config.mobile_ip, config.ssh_port, config.mobile_user, config.mobile_password,
                   '/tmp/detect/temp.ipa', ipa_path)
    if ipa_path:
        ipa = zipfile.ZipFile(ipa_path)
        pat = re.compile("Payload[/\\\][\w.]+[/\\\]Info.plist")
        for name in ipa.namelist():
            if pat.search(name):
                break
        plist_path = ipa.extract(name)
        tmp = plist_path + '.tmp'
        data.app_bundleID = commands.getstatusoutput(
            'plutil -extract CFBundleIdentifier xml1 {} -o {}; plutil -p {}'.
            format(plist_path, tmp, tmp))[1].strip('"')
        Utils.cmd_block(data.client, 'ipainstaller {}'.format('/tmp/detect/temp.ipa'))
        return True

    # open_some_app("com.bigboss.respring")
    # time.sleep(int(config.respring_time))
