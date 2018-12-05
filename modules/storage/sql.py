import data
from Util.utils import Utils
from checker import Checker


def sql_check():
    try:
        files = get_files()
        if not files:
            Utils.printy("No SQL files found ", 2)
            return
        retrieved_files = Utils.get_dataprotection(files)
        data.local_file_protection.extend(retrieved_files)
        check = Checker(files, 'SQL')
        check.start()
        Utils.printy_result('Database Check.', 1)
        return check.results
    except Exception, e:
        data.logger.warn(e)


def get_files():
    files = []
    dirs = [data.metadata['bundle_directory'], data.metadata['data_directory']]
    dirs_str = ' '.join(dirs)
    cmd = '{bin} {dirs_str} -type f -name "*.sqlite"'.format(bin=data.DEVICE_TOOLS['FIND'], dirs_str=dirs_str)
    temp = Utils.cmd_block(data.client, cmd).split("\n")
    cmd = '{bin} {dirs_str} -type f -name "*.db"'.format(bin=data.DEVICE_TOOLS['FIND'], dirs_str=dirs_str)
    temp.extend(Utils.cmd_block(data.client, cmd).split("\n"))

    for db in temp:
        if db != '':
            files.append(db)

    return files
