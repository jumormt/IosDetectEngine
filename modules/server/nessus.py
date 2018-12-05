import requests
import json
import sys
import time
import data
import threading
from Util.utils import Utils


class Nessus(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.url = 'https://localhost:8834'
        self.usr = 'jumormt'
        self.pwd = '1234'
        self.token = ''
        self.verify = False
        # self.targets = ''
        # self.app = ''
        requests.packages.urllib3.disable_warnings()
        self.login()
        policies = self.get_policies()
        self.policy_id = policies['Basic Network Scan']

    def run(self):
        self.scan()

    def set_args(self, targets, app):
        self.targets = targets
        self.app = app

    def build_url(self, resource):
        return '{0}{1}'.format(self.url, resource)

    def login(self):
        login = {'username': self.usr, 'password': self.pwd}
        data = self.connect('POST', '/session', data=login)
        self.token = data['token']
        Utils.printy('Log into the Nessus system.', 0)
        # print 'token:', self.token

    def logout(self):
        self.connect('DELETE', '/session')
        # print 'Logout!!!!'

    def get_policies(self):
        data = self.connect('GET', '/editor/policy/templates')
        return dict((p['title'], p['uuid']) for p in data['templates'])

    def connect(self, method, resource, data=None, params=None):
        verify = self.verify
        headers = {'X-Cookie': 'token={0}'.format(self.token),
                   'content-type': 'application/json'}
        data = json.dumps(data)
        if method == 'POST':
            r = requests.post(self.build_url(resource), data=data, headers=headers, verify=verify)
        elif method == 'PUT':
            r = requests.put(self.build_url(resource), data=data, headers=headers, verify=verify)
        elif method == 'DELETE':
            r = requests.delete(self.build_url(resource), data=data, headers=headers, verify=verify)
        else:
            r = requests.get(self.build_url(resource), params=params, headers=headers, verify=verify)
        if r.status_code != 200:
            e = r.json()
            # print e['error']
            if e['error'] == 'Invalid Credentials':
                self.login()
            else:
                sys.exit()
        if 'download' in resource:
            return r.content
        try:
            return r.json()
        except ValueError:
            return r.content

    def add(self, name, desc, targets, pid):
        scan = {'uuid': pid,
                'settings': {
                    'name': name,
                    'description': desc,
                    'text_targets': targets}
                }
        data = self.connect('POST', '/scans', data=scan)
        return data['scan']

    def launch(self, sid):
        data = self.connect('POST', '/scans/{0}/launch'.format(sid))
        return data['scan_uuid']

    def get_history_ids(self, sid):
        data = self.connect('GET', '/scans/{0}'.format(sid))
        return dict((h['uuid'], h['history_id']) for h in data['history'])

    def status(self, sid, hid):
        params = {'history_id': hid}
        data = self.connect('GET', '/scans/{0}'.format(sid), params)
        try:
            return data['info']['status']
        except KeyError:
            return 'irregular'

    def export_status(self, sid, fid):
        data = self.connect('GET', '/scans/{0}/export/{1}/status'.format(sid, fid))
        return data['status'] == 'ready'

    def export(self, sid, hid):
        data = {'history_id': hid,
                'format': 'html',
                'chapters': 'vuln_hosts_summary'}

        data = self.connect('POST', '/scans/{0}/export'.format(sid), data=data)
        fid = data['file']
        while self.export_status(sid, fid) is False:
            time.sleep(5)
        return fid

    def download(self, sid, fid):
        nessus_data = self.connect('GET', '/scans/{0}/export/{1}/download'.format(sid, fid))
        filename = './temp/{}/report/{}.nessus'.format(data.start_time, data.app_bundleID)
        # print('Saving scan results to {0}.'.format(filename))
        with open(filename, 'w') as f:
            f.write(nessus_data)

    def delete(self, sid):
        self.connect('DELETE', '/scans/{0}'.format(sid))

    def scan(self):
        target = self.targets
        app = self.app
        scan_data = self.add(app, 'Test urls in {0}'.format(app), target, self.policy_id)
        scan_id = scan_data['id']
        data.nessus_url = self.url + '/#/scans/{}/hosts'.format(scan_id)
        scan_uuid = self.launch(scan_id)
        # history_id = self.get_history_ids(scan_id)[scan_uuid]
        # while self.status(scan_id, history_id) != 'completed':
        #     # print time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
        #     time.sleep(10)
        #
        # # print('Exporting the completed scan.')
        # file_id = self.export(scan_id, history_id)
        # self.download(scan_id, file_id)
        #
        # # print('Deleting the scan.')
        # self.delete(scan_id)
        self.logout()
        data.status ^= 0b0100

# hosts = ['www.baidu.com']
# server = Nessus()
# def server_scan(hosts):
#     server.set_args(hosts, "test")
#     server.start()
# server_scan(hosts)