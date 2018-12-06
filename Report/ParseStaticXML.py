from xml.dom.minidom import parse
import xml.dom.minidom
import os
import data
from RuleUtils import Rule


class XMLParser:

    def __init__(self):
        self.unsecure_match_results = dict()
        self.secure_not_match_results = list()

    def start_parse(self):
        # find the xml
        report_dir = './temp/{}/report'.format(data.start_time)
        static_finished = False # 静态检测是否完成
        while not static_finished:
            for file in os.listdir(report_dir):
                if file.endswith('.xml'):
                    static_finished = True
                    self.parse_xml(os.path.join(report_dir, file))
                    break
        # for file in os.listdir(report_dir):
        #     if file.endswith('.xml'):
        #         self.parse_xml(os.path.join(report_dir, file))

    def parse_xml(self,file_path):
        # print file_path
        DOMTree = xml.dom.minidom.parse(file_path)
        report = DOMTree.documentElement

        unsecure_match = report.getElementsByTagName('unsecure_match')
        unsecure_match=unsecure_match[0]
        for fun in unsecure_match.getElementsByTagName('Function'):
            fun_name = fun.getAttribute('name')
            self.unsecure_match_results[fun_name]=[]
            for rule in fun.getElementsByTagName('Matched_rule'):
                rule_obj = Rule(rule_id=rule.getAttribute('id'), rule_name=rule.getAttribute('name'),
                            rule_desc=rule.getAttribute('description'), rule_solution=rule.getAttribute('solution'),
                            risk_level=rule.getAttribute('risk_level'))
                self.unsecure_match_results[fun_name].append(rule_obj)

        secure_not_match = report.getElementsByTagName('secure_not_match')
        secure_not_match=secure_not_match[0]
        for rule in secure_not_match.getElementsByTagName('rule'):
            rule_obj = Rule(rule_id=rule.getAttribute('id'), rule_name=rule.getAttribute('name'),
                        rule_desc=rule.getAttribute('description'), rule_solution=rule.getAttribute('solution'),
                        risk_level=rule.getAttribute('risk_level'))
            self.secure_not_match_results.append(rule_obj)

# xml_parser = XMLParser()
# xml_parser.start_parse()
# print xml_parser.unsecure_match_results
# print xml_parser.secure_not_match_results