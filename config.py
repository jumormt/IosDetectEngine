import ConfigParser
from Util.utils import Utils

config = ConfigParser.SafeConfigParser()
config.read("./config/para_config.conf")

mobile_ip = config.get('mobile', 'mobile_ip')
mobile_user = config.get('mobile', 'mobile_user')
mobile_password = config.get('mobile', 'mobile_password')

server_ip = config.get('server', 'server_ip')
server_user = config.get('server', 'server_user')
server_password = config.get('server', 'server_password')

ssh_port = config.get('ssh', 'ssh_port')

socket_ip = config.get('socket', 'socket_ip')
socket_port = config.get('socket', 'socket_port')

respring_time = config.get('other', 'respring_time')

thrift_ip = config.get('thrift', 'server_ip')
thrift_port = config.get('thrift', 'server_port')

Utils.printy('Finished configuration.', 0)

