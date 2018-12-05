from Util import utils
import data


def open():
    #the bundle id of application
    bundleID = data.app_bundleID

    #the client of ssh
    client = data.client

    #the cmd of open application
    open_cmd = 'open '+bundleID

    utils.Utils.cmd_block(client, open_cmd)

def open_some_app(bundle):
    # the client of ssh
    client = data.client

    # the cmd of open application
    open_cmd = 'open ' + bundle

    utils.Utils.cmd_block(client, open_cmd)