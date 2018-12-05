import re
import collections
import data
from Util.utils import Utils


class protect_check():
    # ==================================================================================================================
    # UTILS
    # ==================================================================================================================
    def __init__(self):
        self.tests = collections.defaultdict(dict)
        self.client = data.client

    def __run_otool(self, query, grep=None):
        """Run otool against a specific architecture."""
        cmd = '{bin} {query} {app}'.format(bin=data.DEVICE_TOOLS['OTOOL'],
                                           query=query,
                                           app=data.metadata['binary_path'])
        if grep:
            cmd = "%s | grep -Ei \"%s\"" % (cmd, grep)
        out = Utils.cmd_block(self.client, cmd).split("\n")
        return out

    def __check_flag(self, line, flagname, flag):
        """Extract result of the test."""
        tst = filter(lambda el: re.search(flag, el), line)
        res = True if tst and len(tst) > 0 else False
        self.tests[flagname] = res

    # ==================================================================================================================
    # CHECKS
    # ==================================================================================================================
    def _check_cryptid(self):
        out = self.__run_otool('-l', grep='cryptid')
        self.__check_flag(out, "Encrypted", "cryptid(\s)+1")

    def _check_pie(self):
        out = self.__run_otool('-hv')
        self.__check_flag(out, "PIE", "PIE")

    def _check_arc(self):
        out = self.__run_otool('-IV', grep='(\(architecture|objc_release)')
        self.__check_flag(out, "ARC", "_objc_release")

    def _check_stack_canaries(self):
        out = self.__run_otool('-IV', grep='(\(architecture|___stack_chk_(fail|guard))')
        self.__check_flag(out, "Stack Canaries", "___stack_chk_")

    # ==================================================================================================================
    # RUN
    # ==================================================================================================================
    def check(self):
        for arch in data.metadata['architectures']:
            data.protection_check_lables[arch] = dict()
            # Checks
            self._check_cryptid()
            self._check_pie()
            self._check_arc()
            self._check_stack_canaries()
            for name, val in self.tests.items():
                data.protection_check_lables[arch][name] = val
