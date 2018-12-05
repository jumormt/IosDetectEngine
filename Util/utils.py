#coding=utf-8
import os
import re
import zipfile
import paramiko
import data
import simplejson
import pipes
from clint.textui import colored, puts, indent
import sys
import time
import commands
import socket
from PreProcess import *
reload(sys)
sys.setdefaultencoding('utf-8')

# ======================================================================================================================
# GENERAL UTILS
# ======================================================================================================================
class Utils():
    # ==================================================================================================================
    # PATH UTILS
    # ==================================================================================================================
    @staticmethod
    def escape_path(path):
        """Escape the given path."""
        path = path.strip(''''"''')  # strip occasional single/double quotes from both sides
        return pipes.quote(path)

    @staticmethod
    def escape_path_scp(path):
        """To be correctly handled by scp, paths must be quoted 2 times."""
        temp = Utils.escape_path(path)
        return '''"%s"''' % temp

    @staticmethod
    def extract_filename_from_path(path):
        return os.path.basename(path)

    @staticmethod
    def extract_paths_from_string(str):
        # Check we have a correct number of quotes
        if str.count('"') == 4 or str.count("'") == 4:
            # Try to get from double quotes
            paths = re.findall(r'\"(.+?)\"', str)
            if len(paths) == 2: return paths[0], paths[1]
            # Try to get from single quotes
            paths = re.findall(r"\'(.+?)\'", str)
            if len(paths) == 2: return paths[0], paths[1]
        # Error
        return None, None

    # ==================================================================================================================
    # UNICODE STRINGS UTILS
    # ==================================================================================================================
    @staticmethod
    def to_unicode_str(obj, encoding='utf-8'):
        """Checks if obj is a string and converts if not."""
        if not isinstance(obj, basestring):
            obj = str(obj)
        obj = Utils.to_unicode(obj, encoding)
        return obj

    @staticmethod
    def to_unicode(obj, encoding='utf-8'):
        """Checks if obj is a unicode string and converts if not."""
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj

    @staticmethod
    def regex_escape_str(str):
        """Make the string regex-ready by escaping it."""
        return re.escape(str)

    # ==================================================================================================================
    #  SSH UTILS
    # ==================================================================================================================
    @staticmethod
    def cmd_block(client, cmd):
        if client:
            data.logger.debug("cmd_block " + cmd)
            while True:
                try:
                    stdin, out, err = client.exec_command(cmd)
                    break
                except Exception, e:
                    time.sleep(5)
                    data.logger.debug("Command Transfer Error" + e)
            if type(out) is tuple: out = out[0]
            str = ''
            try:
                for line in out:
                    str += line
            except Exception as e:
                print e
            return str
        else:
            return None

    @staticmethod
    def cmd_block_limited(client, cmd, timelimit):
        data.logger.debug("cmd_block " + cmd)
        str = ''
        while True:
            try:
                stdin, out, err = client.exec_command(cmd, timeout=timelimit)
                if type(out) is tuple: out = out[0]
                for line in out:
                    str += line
                break
            except Exception as e:
                if type(e).__name__ == "timeout":
                    break
                time.sleep(5)
                data.logger.debug("Command Transfer Error" )
        return str

    @staticmethod
    def sftp_get(ip, port, username, password, remote_file, local_path):
        # -----set up sftp to get decrypted ipa file-----
        while True:
            try:
                t = paramiko.Transport(ip, port)
                t.connect(username=username, password=password)
                data.logger.info('{} -> {}'.format(remote_file, local_path))
                sftp = paramiko.SFTPClient.from_transport(t)
                sftp.get(remote_file, local_path)
                t.close()
                break
            except Exception as e:
                time.sleep(5)
                data.logger.debug("SFTP GET FILE Error")
                cmd = "sftp -P {} {}@{}:{} {}".format(port, username, ip, remote_file, local_path)
                out = commands.getstatusoutput(cmd)
                if out[0] == 0:
                    break


    @staticmethod
    def sftp_put(ip, port, username, password, remote_path, local_file):
        while True:
            try:
                t = paramiko.Transport(ip, port)
                t.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(t)
                # print '{} -> {}'.format(local_file, remote_path)
                sftp.put(localpath=local_file, remotepath=remote_path)
                t.close()
                break
            except:
                time.sleep(5)
                data.logger.debug("SFTP PUT FILE Error")

    # @staticmethod
    # def sftp_get_files(ip, port, username, password, remote_files, local_dir):
    #     t = paramiko.Transport(ip, port)
    #     t.connect(username=username, password=password)
    #     sftp = paramiko.SFTPClient.from_transport(t)
    #     for file in remote_files:
    #         sftp.get(remote_file, local_path)

    @staticmethod
    def get_dataprotection(filelist):
        """Get the Data Protection of the files contained in 'filelist'."""
        computed = []
        for el in filelist:
            if el:
                fname = Utils.escape_path(el.strip())
                dp = '{bin} -f {fname}'.format(bin=data.DEVICE_TOOLS['FILEDP'], fname=fname)
                dp += ' 2>&1'                                            # needed because by default FileDP prints to STDERR
                res = Utils.cmd_block(data.client, dp).split("\n")
                # Parse class
                cl = res[0].rsplit(None, 1)[-1]
                computed.append((fname, cl))
        return computed

    @staticmethod
    def openurl(url):
        cmd = "{uiopen} {u}".format(uiopen=data.DEVICE_TOOLS['UIOPEN'], u=url)
        Utils.cmd_block(data.client, cmd)

    @staticmethod
    def kill_by_name(bin_name):
        cmd = 'killall -9 {}'.format(bin_name)
        Utils.cmd_block(data.client, cmd)

    @staticmethod
    def getInstalledAppList():
        apps = data.app_dict.keys()
        for app in apps:
            Utils.printy('[{}] {}'.format(apps.index(app), app), 1)
        while True:
            try:
                app_index = int(raw_input(colored.yellow("> >> >>> Choose the app to analyze: > ")))
                data.app_bundleID = apps[app_index]
                break
            except IndexError:
                Utils.printy_result('Index out of range ', 0)

    @staticmethod
    def cut_off():
        with indent(4, quote=' '):
            for i in range(0, 30):
                # print u'\u1368',
                print ". ",
            print

    @staticmethod
    def printy(s, status):
        colors = ['green', 'white', 'red', 'cyan', 'yellow']
        with indent(4, quote=time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time())) + "   "):
            str = '{:10}'.format(s)
            puts(getattr(colored, colors[status])(str))

    @staticmethod
    def printy_result(s, status):
        with indent(4, quote=time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time())) + "   "):
            str = '{:.<40}'.format(s)
            if status:
                puts(getattr(colored, 'green')(str + '[OK]'))
            else:
                puts(getattr(colored, 'red')(str + '[ERROR]'))

    @staticmethod
    def ret_last_launch():
        client = data.client
        Utils.cmd_block(client,
                        'cp /var/mobile/Library/MobileInstallation/LastLaunchServicesMap.plist '
                        '/var/mobile/Library/MobileInstallation/temp.plist')
        Utils.cmd_block(client, 'plutil -convert json /var/mobile/Library/MobileInstallation/temp.plist')
        json = Utils.cmd_block(client, 'cat /var/mobile/Library/MobileInstallation/temp.json')
        Utils.cmd_block(client, 'rm /var/mobile/Library/MobileInstallation/temp.plist')
        Utils.cmd_block(client, 'rm /var/mobile/Library/MobileInstallation/temp.json')
        json_dict = simplejson.loads(json)
        app_dict = json_dict['User']
        with open('apps.txt', 'w') as file:
            for bundle_id in app_dict.keys():
                bundle_name = Utils.get_bundle_name_byID(app_dict,bundle_id)
                file.write(bundle_id +' * {} *'.format(bundle_name) + "\r\n")
        file.close()
        return app_dict

    @staticmethod
    def get_bundle_name_byID(app_dict, bundle_id):
        bundle_name = ''

        bundle_dir= app_dict[bundle_id]['Path']
        info_plist_path = bundle_dir+'/Info.plist'
        tmp_plist_path = '/var/tmp/Info_tmp.plist'
        tmp_json_path  = '/var/tmp/Info_tmp.json'
        Utils.cmd_block(data.client,'cp '+info_plist_path+' ' + tmp_plist_path)
        Utils.cmd_block(data.client,'plutil -convert json ' + tmp_plist_path)
        info_plist_json = Utils.cmd_block(data.client,'cat ' + tmp_json_path)
        Utils.cmd_block(data.client,'rm ' + tmp_json_path)
        Utils.cmd_block(data.client, 'rm ' + tmp_plist_path)
        try:
            info_plist_dict = simplejson.loads(info_plist_json)
            bundle_name = info_plist_dict['CFBundleName']
        except:
            bundle_name = u"解析异常，请尝试重启手机"
        return bundle_name

    @staticmethod
    def build():
        data.root = os.path.abspath('.')
        data.start_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
        root = os.path.join(".", "temp", data.start_time)
        for dir in ["binary", "report", "files"]:
            os.makedirs(os.path.join(root, dir))
        Utils.cmd_block(data.client, "mkdir /tmp/detect/")
        Utils.cmd_block(data.client, "mkdir {}".format(data.DEVICE_PATH_TEMP_FOLDER))

    @staticmethod
    def ret_name_from_db(name):
        name = name.strip()
        bundle_id = name.split("*")[0].strip()
        return bundle_id

    @staticmethod
    def shutdown():
        print "SHUTDOWN"

    @staticmethod
    def ret_last_launch_9():
        client = data.client
        app_ids = Utils.cmd_block(client, 'ipainstaller -l').split()
        app_dict = {}
        with open('apps.txt', 'w') as file:
            for bundle_id in app_ids:
                # if bundle_id not in app_dict:
                #     app_dict[bundle_id] = dict()
                # (bundle_name, bundle_dir,) = Utils.get_bundle_name_byID_9(app_dict, bundle_id)
                # if "Path" not in app_dict[bundle_id]:
                #     app_dict[bundle_id] = bundle_dir
                # if "CFBundleName" not in app_dict[bundle_id]:
                #     app_dict[bundle_id] = bundle_name
                Utils.get_bundleInfo_byID_9(app_dict, bundle_id)
                file.write(bundle_id +' * {} *\n'.format(app_dict[bundle_id]["CFBundleName"]))
        file.close()
        return app_dict

    @staticmethod
    def get_bundleInfo_byID_9(app_dict, bundle_id):
        bundle_info = dict()
        key_words = ["Identifier", "Version", "Name", "Bundle", "Application", "Data"]
        out = Utils.cmd_block(data.client, 'ipainstaller -i ' + bundle_id).split("\n")
        for item in out:
            kw = item.split(":")[0]
            if kw in key_words:
                bundle_info[kw] = item.split(":")[-1].strip()
        info_plist_path = bundle_info["Application"]+'/Info.plist'

        try:
            bundle_name = Utils.cmd_block(data.client, "plutil -key CFBundleName '{}'".format(info_plist_path))
        except Exception as e:
            bundle_name = u"解析异常，请尝试重启手机"
        bundle_info["CFBundleName"] = bundle_name
        app_dict[bundle_id] = bundle_info

    @staticmethod
    def zip_results():
        doc_report = data.report_path
        pdf_report = data.static_report
        zip_name = doc_report.replace('.doc', '.zip')
        zip = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
        zip.write(doc_report)
        zip.write(pdf_report)
        zip.close()
        data.report_path = zip_name






