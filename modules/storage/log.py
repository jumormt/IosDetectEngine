import data
from Util.utils import Utils
from checker import Checker

class Log():

    def __init__(self):
        self.client = data.client

    def check(self):
        log_file = ['/var/log/syslog']

        # start check log sensitive data
        check = Checker(log_file, 'LOG')
        check.start()
        data.log_file_results = check.results
        Utils.printy_result('Log Check.', 1)
