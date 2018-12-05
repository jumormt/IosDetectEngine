import paramiko
import data
import config


# ------ssh parameters------
# ip       = "192.168.3.248"
# port     = 22
# username = "root"
# password = "alpine"
# session_timeout = 60
#
# def set_ssl_conn():
#     #get config
#     ip = config.iphone_ip
#     port= config.ssh_port
#     username = config.ssh_username
#     password = config.ssh_password
#
#     client = paramiko.SSHClient()
#     client.load_system_host_keys()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     client.connect(ip, port, username=username, password=password)
#     data.client = client

def set_ssh_conn(ip, port, username, password):
    c = paramiko.SSHClient()
    c.load_system_host_keys()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(ip, int(port), username=username, password=password)
    return c

