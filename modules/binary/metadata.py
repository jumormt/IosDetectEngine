import os
from Util.utils import Utils
import data
import plistlib


class Metadata():

    def __init__(self):
        self.app = data.app_bundleID
        self.client = data.client

    def get_metadata(self):
        """Retrieve metadata of the target app."""
        # self._app = app_name
        # if self._device._applist is None:
        #     self._device._list_apps()
        return self._retrieve_metadata()

    def _retrieve_metadata(self):
        """Parse MobileInstallation.plist and the app's local Info.plist, and extract metadata."""
        # Content of the MobileInstallation plist
        # client = self.client
        # data in LastLauchServicesMap.plist
        global_info = data.app_dict[self.app]
        uuid = global_info['Bundle'].rsplit('/', 1)[-1]
        name = global_info['Application'].rsplit('/', 1)[-1]
        bundle_id = global_info['Identifier']
        bundle_directory = global_info['Bundle']
        data_directory = global_info['Data']
        binary_directory = global_info['Application']
        try:
            entitlements = global_info['Entitlements']
        except KeyError:
            entitlements = None

        # Content of the app's local Info.plist
        path = Utils.escape_path('%s/Info.plist' % binary_directory)
        info_plist = self.parse_plist(path)
        platform_version = info_plist['DTPlatformVersion']
        sdk_version = info_plist['DTSDKName']
        minimum_os = info_plist['MinimumOSVersion']
        app_version_long = info_plist['CFBundleVersion']
        app_version_short = info_plist['CFBundleShortVersionString']
        app_version = '{} ({})'.format(app_version_long, app_version_short)
        try:
            url_handlers = info_plist['CFBundleURLTypes'][0]['CFBundleURLSchemes']
        except KeyError:
            url_handlers = None

        # Compose binary path
        binary_folder = binary_directory
        binary_name = os.path.splitext(binary_folder.rsplit('/', 1)[-1])[0]
        binary_path = Utils.escape_path(os.path.join(binary_folder, binary_name))

        # Detect architectures
        architectures = self._detect_architectures(binary_path)

        # Pack into a dict
        metadata = {
            'uuid': uuid,
            'name': name,
            'app_version': app_version,
            'bundle_id': bundle_id,
            'bundle_directory': bundle_directory,
            'data_directory': data_directory,
            'binary_directory': binary_directory,
            'binary_path': binary_path,
            'binary_name': binary_name,
            'entitlements': entitlements,
            'platform_version': platform_version,
            'sdk_version': sdk_version,
            'minimum_os': minimum_os,
            'url_handlers': url_handlers,
            'architectures': architectures,
        }
        try:
            values = (
                uuid,
                name,
                app_version,
                bundle_id,
                bundle_directory,
                data_directory,
                binary_directory,
                binary_path,
                binary_name,
                entitlements,
                platform_version,
                sdk_version,
                minimum_os,
                url_handlers,
                architectures
            )
            # print values
            # data.db.execute("INSERT INTO metadata VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)

            data.metadata = metadata
            return True
        except AttributeError:
            return False

    def parse_plist(self, plist):
        """Given a plist file, copy it to temp folder, convert it to XML, and run plutil on it."""
        # Copy the plist
        plist_temp = self.build_temp_path_for_file(plist.strip("'"))
        plist_copy = Utils.escape_path(plist_temp)
        self.file_copy(plist, plist_copy)
        # Convert to xml
        cmd = '{plutil} -convert xml1 {plist}'.format(plutil=data.DEVICE_TOOLS['PLUTIL'], plist=plist_copy)
        Utils.cmd_block(self.client, cmd)
        # Cat the content
        cmd = 'cat {}'.format(plist_copy)
        out = Utils.cmd_block(self.client, cmd)
        # Parse it with plistlib
        out = str(''.join(out).encode('utf-8'))
        pl = plistlib.readPlistFromString(out)
        return pl

    def build_temp_path_for_file(self, fname):
        """Given a filename, returns the full path for the filename in the device's temp folder."""
        return os.path.join(data.DEVICE_PATH_TEMP_FOLDER, Utils.extract_filename_from_path(fname))

    def file_copy(self, src, dst):
        src, dst = Utils.escape_path(src), Utils.escape_path(dst)
        cmd = "cp {} {}".format(src, dst)
        Utils.cmd_block(self.client, cmd)

    def _detect_architectures(self, binary):
        """Use lipo to detect supported architectures."""
        # Run lipo
        cmd = '{lipo} -info {binary}'.format(lipo=data.DEVICE_TOOLS['LIPO'], binary=binary)
        out = Utils.cmd_block(self.client, cmd)
        # Parse output
        msg = out.strip()
        res = msg.rsplit(': ')[-1].split(' ')
        return res