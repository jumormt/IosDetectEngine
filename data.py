import os
import sys

# project start time, also is the project home directory in ./temp
start_time = ''

# this is the main ssh connection
client = None

omp_client = None

dbServer = None

# all installed app info
app_dict = {}

# app package name
app_bundleID = ''

# the metadata of the app which is choosed
metadata = {}

# segment and section info
segment_dict = {}

# the shared libs of the app which is choosed
shared_lib = []

# check the protection
# {u'arm64': {'Encrypted': True, 'Stack Canaries': True, 'ARC': True, 'PIE': True}, u'armv7': {'Encrypted': True, 'Stack Canaries': True, 'ARC': True, 'PIE': True}}
protection_check_lables = dict()

# hardcode
hardcode = []

# static analyse file (xxx.ipa or mach-o)
static_file_path = ''

#strings in mach-o binary file
strings = []

#input strings got from dynamic detect (MD5 included)
input_list = None

# traffic detect result
traffic_unsafe_result = []

# mitm result
mitm_results = dict()

#dynamic sensitive json
dynamic_sensitive_json = dict()

#dynamic json receive from iOS
dynamic_json = None

# fuzz result
fuzz_result = dict()

# local files check results
db_file_results = dict()
plist_file_results = dict()
log_file_results = dict()

# keychain values
keychain_values = []

# local files protection check
local_file_protection = []

# static analysis type
static_type = None
static_report = None

MITM_Done = False

DEVICE_PATH_TEMP_FOLDER  = '/tmp/ios_detect_tmp/'
PATH_LIBS = os.path.join(sys.path[0], 'libs')
PATH_DEVICETOOLS = os.path.join(PATH_LIBS, 'devicetools')

DEVICE_SETUP = {
    'PREREQUISITES': ['apt-get', 'dpkg'],
    'TOOLS': {
        # Installation modes supported:
        #   - PACKAGES  = None && LOCAL  = None --> don't install the tools (prerequisite, etc.)
        #   - PACKAGES != None && LOCAL  = None --> add repo if not None, then use apt-get to install the tool
        #   - PACKAGES  = None && LOCAL != None --> use local installation

        # BASIC COMMANDS
        'APT-GET': {'COMMAND': 'apt-get', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
        'DPKG': {'COMMAND': 'dpkg', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
        'WHICH': {'COMMAND': 'which', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
        'UNZIP':  {'COMMAND': 'unzip', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},

        # TOOLKITS
        'BIGBOSS': {'COMMAND': None, 'PACKAGES': ['bigbosshackertools'], 'REPO': 'http://apt.thebigboss.org/repofiles/cydia/', 'LOCAL': None},
        'DARWINTOOLS': {'COMMAND': None, 'PACKAGES': ['org.coolstar.cctools'], 'REPO': None, 'LOCAL': None},
        'COREUTILS': {'COMMAND': None, 'PACKAGES': ['coreutils', 'coreutils-bin'], 'REPO': None, 'LOCAL': None},

        # PROGRAMS
        'CLASS-DUMP': {'COMMAND': 'class-dump', 'PACKAGES': ['pcre', 'net.limneos.classdump-dyld', 'class-dump'], 'REPO': '', 'LOCAL': None},
        'CLUTCH': {'COMMAND': 'Clutch2', 'PACKAGES': ['com.iphonecake.clutch2'], 'REPO': 'http://cydia.iphonecake.com/', 'LOCAL': None},
        'CYCRIPT': {'COMMAND': 'cycript', 'PACKAGES': ['cycript'], 'REPO': None, 'LOCAL': None},
        #'DEBUGSERVER': {'COMMAND': '/usr/bin/debugserver', 'PACKAGES': None, 'REPO': None, 'LOCAL': os.path.join(PATH_DEVICETOOLS, 'debugserver_81')},
        'FILEDP': {'COMMAND': 'FileDP', 'PACKAGES': None, 'REPO': None, 'LOCAL': os.path.join(PATH_DEVICETOOLS, 'FileDP')},
        'FIND': {'COMMAND': 'find', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
        'FRIDA': {'COMMAND': 'frida', 'PACKAGES': ['re.frida.server'], 'REPO': 'https://build.frida.re/', 'LOCAL': None},
        'FSMON': {'COMMAND': 'fsmon', 'PACKAGES': None, 'REPO': None, 'LOCAL': os.path.join(PATH_DEVICETOOLS, 'fsmon')},
        'GDB': {'COMMAND': 'gdb', 'PACKAGES': ['gdb'], 'REPO': 'http://cydia.radare.org/', 'LOCAL': None},
        'IPAINSTALLER': {'COMMAND': 'ipainstaller', 'PACKAGES': ['com.autopear.installipa'], 'REPO': None, 'LOCAL': None},
        'KEYCHAINDUMPER': {'COMMAND': 'keychain_dumper', 'PACKAGES': ['keychaindumper'], 'REPO': None, 'LOCAL': None},
        #'KEYCHAINEDITOR': {'COMMAND': 'keychaineditor', 'PACKAGES': None, 'REPO': None, 'LOCAL': os.path.join(PATH_DEVICETOOLS, 'keychaineditor')},
        'LDID': {'COMMAND': 'ldid', 'PACKAGES': ['ldid'], 'REPO': None, 'LOCAL': None},
        'LIPO': {'COMMAND': 'lipo', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
        'OPEN': {'COMMAND': 'open', 'PACKAGES': ['com.conradkramer.open'], 'REPO': None, 'LOCAL': None},
        'OTOOL': {'COMMAND': 'otool', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
        'PBWATCHER': {'COMMAND': 'pbwatcher', 'PACKAGES': None, 'REPO': None, 'LOCAL': os.path.join(PATH_DEVICETOOLS, 'pbwatcher')},
        'PLUTIL': {'COMMAND': 'plutil', 'PACKAGES': ['com.ericasadun.utilities'], 'REPO': None, 'LOCAL': None},
        'SOCAT': {'COMMAND': 'socat', 'PACKAGES': ['socat'], 'REPO': None, 'LOCAL': None},
        'STRINGS': {'COMMAND': 'strings', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
        'UIOPEN': {'COMMAND': 'uiopen', 'PACKAGES': None, 'REPO': None, 'LOCAL': None},
    }
}

DEVICE_TOOLS = dict([(k, v['COMMAND']) for k, v in DEVICE_SETUP['TOOLS'].iteritems() if v['COMMAND'] is not None])

crash_report_folder = '/var/mobile/Library/Logs/CrashReporter'

report_path = ""

root = ""

nessus_url = ""

database_appid = None

logger = None

status = 0b0000

dynamic_process_id = 0

static_process_id = 0

