import commands
import data
from Util.utils import Utils

def get_seg_info():
    file_path = data.static_file_path
    # cmd = 'otool -l {}'.format(file_path)
    # out = commands.getoutput(cmd)
    cmd = '{bin} -l {app}'.format(bin=data.DEVICE_TOOLS['OTOOL'], app=data.metadata['binary_path'])
    out = Utils.cmd_block(data.client, cmd)
    segment_dict = dict()

    lines = out.split('\n')
    for i in range(len(lines)):
        if lines[i] =='Section':
            section_name = lines[i+1][11:]
            segment_name = lines[i+2][11:]
            # print segment_name, '-', section_name
            if not segment_dict.has_key(segment_name):
                segment_dict[segment_name]=[]
            if section_name not in segment_dict[segment_name]:
                segment_dict[segment_name].append(section_name)

    data.segment_dict = segment_dict