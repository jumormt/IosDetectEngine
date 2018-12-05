# -*- coding:utf-8 -*-
import re
import os
import config
from Util.utils import Utils
import data
import DumpDecrypted
import sys
import bin_get

reload(sys)
sys.setdefaultencoding('utf-8')


# ------get clutch -i result-----
def clutch():
    clutch_app_id = 0
    clutch_success = False
    client = data.client
    clutch_i = Utils.cmd_block(client, 'Clutch -i')

    for line in clutch_i.split('\n'):
        if data.app_bundleID in line:
            break
        clutch_app_id += 1

    if clutch_app_id:

        Utils.printy('the application is encrypted, use Clutch to decrypt', 0)
        # clean the decrypted ipas already done by clutch
        cmd = 'rm /private/var/mobile/Documents/Dumped/*.ipa'
        Utils.cmd_block(client, cmd)
        cmd = 'rm -rf /var/tmp/clutch/*'
        Utils.cmd_block(client, cmd)


        # Only dump binary files from the specified bundleID
        cmd = 'Clutch -b ' + str(clutch_app_id)
        out = Utils.cmd_block_limited(client, cmd, 600)
        dumped_file = Utils.cmd_block(client, 'ls /var/tmp/clutch/*/').split()
        if data.app_bundleID in dumped_file:
            clutch_success = True
            dir = Utils.cmd_block(client, 'ls -H /var/tmp/clutch/').strip()
            source = '{path}/{bundle_id}/{binary}'.format(path='/var/tmp/clutch/{}'.format(dir),
                                                          bundle_id=data.metadata['bundle_id'],
                                                          binary=data.metadata['binary_name'])
            data.static_file_path = bin_get.via_sftp(source)

        if not clutch_success:
            Utils.printy('Failed to clutch! Try to dump the decrypted app into a file. ', 2)
            clutch_success = DumpDecrypted.dump_binary()

        return clutch_success

    else:
        Utils.printy('Failed to Clutch. Get the binary might be encrypted. Static Analysis may fail.', 4)
        data.static_file_path = bin_get.via_sftp(data.metadata['binary_path'])
        return True





