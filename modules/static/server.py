import sys
import time
import os
sys.path.append('./gen-py')
from staticAnalyzer import StaticAnalyze
from staticAnalyzer.ttypes import *
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import time
# from utils import Transfer
import glob
import commands


class analyzerHandler:

    def __init__(self):
        self.client_ip = None
        self.client_port = None

    def connect(self, client_ip=None, client_port=None):
        self.client_ip = client_ip
        self.client_port = client_port
        return "Connected"

    def analyze(self, bin_path, report_dir, report_type=None):

        if report_type == 'pdf':
            analyzer_jar = 'iOSS.jar'
            analyzer_bin = 'IosStaticAnalysis'
        elif report_type == 'xml':
            analyzer_jar = 'iOSS1.jar'
        root_dir = os.path.abspath(".")
        local_bin_path = os.path.join(root_dir, 'temp', 'temp_macho')
        local_report = os.path.join(root_dir, 'report')
        if os.path.isdir(local_report):
            for f in os.listdir(local_report):
                os.remove(os.path.join(local_report, f))
        else:
            os.mkdir(local_report)
        # Transfer().sftp_get(bin_path, local_bin_path)
        output = commands.getstatusoutput("cp {} {}".format(bin_path, local_bin_path))
        time.sleep(10)
        # cmd = 'java -jar {} {} {}'.format(analyzer_jar, local_bin_path, local_report)
        cmd = './{} {} {}'.format(analyzer_bin, local_bin_path, local_report)
        print cmd
        # os.popen(cmd)
        output = commands.getstatusoutput(cmd)

        print 'static analyse success!'
        if len(os.listdir(local_report)) == 1:
            file_name = os.listdir(local_report)[0]
            report_path = os.path.join(local_report, file_name)
            # Transfer().sftp_put(report_dir + '/' + file_name, report_xml)
            output = commands.getstatusoutput("cp {} {}".format(report_path, os.path.join(report_dir, file_name)))
            return os.path.join(report_dir, file_name)
        else:
            print "Unexpected results."
            return 'Fail'


handler = analyzerHandler()
processor = StaticAnalyze.Processor(handler)
transport = TSocket.TServerSocket("127.0.0.1", 9090)
tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
print "Starting thrift server in python..."
# analyzerHandler().analyze("bin_path", "rep_path")
server.serve()
print "done!"
