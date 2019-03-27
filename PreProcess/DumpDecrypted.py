from Util.utils import Utils
import data
import config
import os
import bin_get


def dump_binary():
    try:
        target_doc_path = data.metadata['data_directory']+'/Documents'
        target_doc_file = target_doc_path+'/dumpdecrypted.dylib'
        Utils.sftp_put(ip=config.mobile_ip, port=config.ssh_port,
                       username=config.mobile_user, password=config.mobile_password,
                       remote_path=target_doc_file,
                       local_file='./tools/dumpdecrypted.dylib')

        target_bin_path = data.metadata['binary_path']
        dump_cmd = 'DYLD_INSERT_LIBRARIES={} {}'.format(target_doc_file, target_bin_path)
        Utils.cmd_block(data.client, dump_cmd)
        # get decrypted file from iphone
        remote_file = './{}.decrypted'.format(data.metadata['binary_name'])
        data.static_file_path = bin_get.via_sftp(remote_file)

        return True
    except Exception:
        return False



