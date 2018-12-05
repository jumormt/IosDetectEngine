import data
from Util.utils import Utils


class SharedLibrary():
    def __init__(self):
        self.client = data.client

    def get(self):
        cmd = '{bin} -L {app}'.format(bin=data.DEVICE_TOOLS['OTOOL'], app=data.metadata['binary_path'])
        out = Utils.cmd_block(self.client, cmd).split("\n")
        if out:
            try:
                del out[0]
                for i in out:
                    i = i.strip('\t')
                    if len(i) > 0:
                        data.shared_lib.append(i)
                # print "--------------------shared_library-------------------"
                return True
            except AttributeError:
                return False
        else:
            return False
