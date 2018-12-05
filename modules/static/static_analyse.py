import subprocess
import threading
import data
from Util.utils import Utils
import time
import os
import sys
import config
sys.path.append('gen-py')
import importlib
from staticAnalyzer import StaticAnalyze
from staticAnalyzer.ttypes import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

class static_analyzer(threading.Thread):
    def run(self):
        self.do_analyse()

    def do_analyse(self):
        data.static_process_id = os.getpid()
        exec "from staticAnalyzer import StaticAnalyze"
        exec "from staticAnalyzer.ttypes import *"
        Utils.printy('Start static analysis', 0)
        time.sleep(1)
        try:
            transport = TSocket.TSocket(config.thrift_ip, config.thrift_port)
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = StaticAnalyze.Client(protocol)
            transport.open()
            while True:
                if client.connect() == "Connected":
                    Utils.printy_result("Connect to IDA Server", 1)
                    break
            report_dir = "{}/temp/{}/report".format(data.root, data.start_time)
            msg = client.analyze(data.static_file_path, report_dir, report_type='pdf')
            if msg == "Fail":
                Utils.printy_result("Static Analyse", 0)
            else:
                Utils.printy_result('Static Analyse.', 1)
                data.static_report = msg
            transport.close()
            data.status ^= 0b0010
        except Thrift.TException, ex:
            print "%s" % ex.message


