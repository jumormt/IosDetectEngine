import data
from Util.utils import Utils
import time
from url_builder import url_builder

class url_scheme_fuzzer():

    def __init__(self, app_info):
        self.results = dict()
        self.app = data.metadata['binary_name']
        # get urls from url_builder
        self.builder = url_builder(app_info)
        self.fuzz_inputs = self.builder.build()
        # print self.fuzz_inputs

    def delete_old_reports(self):
        cmd = 'rm -f `find {} -type f | grep {}`'.format(data.crash_report_folder, self.app)
        Utils.cmd_block(data.client, cmd)

    def fuzz(self):
        total_count = len(self.fuzz_inputs)
        count = 0
        for url in self.fuzz_inputs:
            count += 1
            # print '[{}/{}]fuzzing...[{}]'.format(count, total_count, url)
            time.sleep(1)
            self.delete_old_reports()
            Utils.openurl(url)
            time.sleep(2)
            Utils.kill_by_name(self.app)
            self.results[url] = self.crashed()
        Utils.printy_result('Fuzz', True)
        data.fuzz_result = self.results

    def crashed(self):
        cmd = 'find {} -type f | grep {}'.format(data.crash_report_folder, self.app)
        if Utils.cmd_block(data.client, cmd).split("\n")[0]:
            return True
        else:
            return False