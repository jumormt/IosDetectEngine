import sqlite3
import data
from Util.utils import Utils


class DBServer():
    def __init__(self):
        Utils.printy("Initiate DB", 0)
        # try:
        #     con = sqlite3.connect("test.db")
        #     c = con.cursor()
        #     c.execute('''create table metadata (
        #               uuid text primary key,
        #               name text,
        #               app_version text,
        #               bundle_id text,
        #               bundle_directory text,
        #               data_directory text,
        #               binary_directory text,
        #               binary_path text,
        #               binary_name text,
        #               entitlements text,
        #               platform_version text,
        #               sdk_version text,
        #               minimum_os text,
        #               url_handlers text,
        #               architectures text
        #               )''')
        #
        #     c.execute('''create table strings (
        #     uuid text,
        #     str text unique
        #     )''')
        #
        #     con.commit()
        #     con.close()
        # except sqlite3.Error as e:
        #     print e

    def on(self):
        try:
            self.con = sqlite3.connect("task.db")
            self.c = self.con.cursor()
        except sqlite3.Error as e:
            # print e.args[0]
            data.logger.debug("Can't Connect to Database")
            Utils.shutdown()

    def down(self):
        try:
            self.con.commit()
            self.con.close()
            print "DBServer Down"
        except sqlite3.Error as e:
            print e.args[0]

    def execute(self, query):
        try:
            self.c.execute(query)
            self.con.commit()
            return self.c.fetchall()
        except sqlite3.Error as e:
            data.logger.debug(e.args[0])
            return False

    def execute(self, query, args):
        try:
            self.c.execute(query, args)
            self.con.commit()
            return self.c.fetchall()
        except sqlite3.Error as e:
            data.logger.debug(e.args[0])
            return False

    def refresh_status(self):
        self.execute("update ios_app set status=? where status=?", ('2', '3'))





