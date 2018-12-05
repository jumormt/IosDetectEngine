import threading
from datetime import datetime
import data
from Util.utils import Utils
import re
import bin_get
from modules.dynamic.open_app import open_some_app
import DumpDecrypted

class decryptThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.status = "init"

    def run(self):
        self.clutch()

    def clutch(self):
        client = data.client
        clutch_i = Utils.cmd_block(client, 'clutch -i')
        pat = re.compile(r'.+<(.+)>')

        clutch_app_id = -1
        for line in clutch_i.split('\n'):
            m = pat.match(line)
            if m:
                if m.group(1) == data.app_bundleID:
                    clutch_app_id = int(line.split(':')[0])

        if clutch_app_id != -1:

            Utils.printy('the application is encrypted, and use clutch to decrypt', 0)
            # clean the decrypted ipas already done by clutch
            cmd = 'rm /private/var/mobile/Documents/Dumped/*.ipa'
            Utils.cmd_block(client, cmd)

            self.status = "clutching"
            # Only dump binary files from the specified bundleID
            cmd = 'clutch -b ' + str(clutch_app_id)
            out = Utils.cmd_block(client, cmd)
            pat = re.compile(r'.+Finished.+to (.+)\[0m')
            for line in out.split('\n'):
                m = pat.match(line)
                if m:
                    # print m.group(1)
                    source = '{path}/{bundle_id}/{binary}'.format(path=m.group(1),
                                                                  bundle_id=data.metadata['bundle_id'],
                                                                  binary=data.metadata['binary_name'])
                    data.static_file_path = bin_get.via_sftp(source)
                    self.status = "done"

            # if self.status != "done":
            #     Utils.printy('Failed to clutch! Try to dump the decrypted app into a file. ', 2)
            #     self.status = DumpDecrypted.dump_binary()

        else:
            # print 'the application is not encrypted'
            data.static_file_path = bin_get.via_sftp(data.metadata['binary_path'])

    def stop(self):
        open_some_app("com.bigboss.respring")