# _*_coding:utf-8_*_
import idc
import idautils
import idaapi
from idaapi import *
import re
import sqlite3
import json
import sys
import xml.etree.ElementTree as ET

reload(sys)
sys.setdefaultencoding('utf-8')


class Binary:

    def __init__(self):
        self.parser = {
            '__objc_classrefs': self.parse_classref,
            '__objc_superrefs': self.parse_classref,
            '__objc_selrefs': self.parse_selector,
            '__objc_ivar': self.parse_ivar,
            '__objc_classlist': self.parse_class,
            'UNDEF': self.parse_imports
        }
        self._classrefs = dict()  # name: classref_ea
        self._classlist = dict()  # name: classlist_ea
        self._selrefs = dict()
        self._ivars = dict()  # ivar_ea: type
        self._ivars_2 = dict()  # type:  ivar_ea list
        self._allocs = []
        self._imports = dict()  # symbol_name: ea
        self._functions = dict()  # function_name: startEA
        self.callG = dict()
        self.parse()

    def parse_classref(self, ea):
        classname = idc.Name(ea).replace('classRef_', '')
        self._classrefs[classname] = ea

    def parse_selector(self, ea):
        # m = re.search('[^"]+"(?P<sel>.+)"', idc.GetDisasm(ea))
        # if m:
        #     self._selrefs[m.group('sel')] = ea
        self._selrefs[idc.Name(ea).replace('selRef_', '').replace('_', ':')] = ea

    def parse_ivar(self, ea):
        cmt = idc.GetCommentEx(ea, True)
        if cmt:
            type = cmt.split()[0]
            self._ivars[ea] = type
            if type in self._ivars_2:
                self._ivars_2[type].append(ea)
            else:
                self._ivars_2[type] = [ea, ]
        else:
            print 'CANNOT GET CMT OF IVAR: '.format(hex(ea))

    def parse_class(self, ea):
        classname = idc.GetDisasm(ea).split('_OBJC_CLASS_$_')[-1]
        self._classlist[classname] = ea

    def parse_imports(self, ea):
        self._imports[idc.Name(ea)] = ea

    def parse(self):
        for f in idautils.Functions():
            func_name = idc.GetFunctionName(f)
            self._functions[func_name] = f

        for seg in idautils.Segments():
            segName = idc.SegName(seg)
            if segName in ['__objc_classrefs', '__objc_superrefs', '__objc_selrefs', '__objc_classlist', 'UNDEF']:  # step: 8
                for ea in range(idc.SegStart(seg), idc.SegEnd(seg), 8):
                    self.parser[segName](ea)
            elif segName in ['__objc_ivar']:  # step: 4
                for ea in range(idc.SegStart(seg), idc.SegEnd(seg), 4):
                    self.parser[segName](ea)

    def get_data(self):
        return {
            'classrefs': self._classrefs,
            'classlist': self._classlist,
            'selrefs': self._selrefs,
            'ivars': self._ivars,
            'ivars2': self._ivars_2,
            'allocs': self._allocs,
            'imports': self._imports,
            'functions': self._functions
        }


class StaticAnalyzer:

    def __init__(self):
        self.binData = Binary().get_data()
        self.to_be_analyzed = set()

    def parse_rules(self):
        rule_dir = '../rule'
        to_be_analyzed = set()
        for f in os.listdir(rule_dir):
            try:
                tree = ET.parse(os.path.join(rule_dir, f))
                root = tree.getroot()
                for func in root.iter('Function'):
                    s = func.attrib['name']
                    if s == "_objc_msgSend":
                        ctx = set()
                        for p in func.findall('Parameter'):
                            p_type = p.text.split('=')[0]
                            p_name = p.text.split('=')[-1]
                            if p_type == 'X0':
                                if p_name in self.binData['classrefs']:
                                    if ctx:
                                        ctx &= self.find_xrefs(self.binData['classrefs'][p_name])
                                    else:
                                        ctx = self.find_xrefs(self.binData['classrefs'][p_name])
                            elif p_type == 'X1':
                                if p_name in self.binData['selrefs']:
                                    if ctx:
                                        ctx &= self.find_xrefs(self.binData['selrefs'][p_name])
                                    else:
                                        ctx = self.find_xrefs(self.binData['selrefs'][p_name])
                            else:
                                for symbol, ea in self.binData['imports'].items():
                                    if p_name in symbol:
                                        if ctx:
                                            ctx &= self.find_xrefs(ea)
                                        else:
                                            ctx = self.find_xrefs(ea)
                                print p.text

                        to_be_analyzed.update(ctx)
                    else:
                        if s in self.binData['functions']:
                            to_be_analyzed.update(self.find_xrefs(self.binData['functions'][s]))
                        else:
                            print "CANNOT FIND SYMBOL {}.".format(s)
            except Exception as e:
                print e, f
        self.to_be_analyzed = to_be_analyzed

    def find_xrefs(self, ea):
        ret = set()
        for xref in XrefsTo(ea):
            fi = idaapi.get_func(xref.frm)
            if fi:
                ret.add(fi.startEA)
        return ret


def parse_MOV(addr):
    des = idc.GetOpnd(addr, 0)
    src = idc.GetOpnd(addr, 1)
    #～change W to X , ignore W
    if des.startswith('W'):
        des = 'X'+des[1:]

    if src.startswith('#'):   # MOV X0 #0Xffff
        regs[des]=src[1:].encode('utf-8').strip()
    else:
        if src in regs:
            regs[des] = regs[src]
        elif des in regs:
            regs[des] = 'Unknown'


def parse_STR(addr):
    src = idc.GetOpnd(addr, 0)
    des = idc.GetOpnd(addr, 1)[1:-1]
    if src in regs:
        regs[des]=regs[src]
    else:
        regs[des]='Unknown'


def parse_LDR(addr):
    des = idc.GetOpnd(addr, 0)
    #～change W to X , ignore W
    if des.startswith('W'):
        des = 'X'+des[1:]

    asm = idc.GetDisasm(addr)


    pat5 = re.compile(r'.+"(.+)".*')#~LDR X1, =sel_defaultManager; "defaultManager"  ""indicate the value
    pat  = re.compile(r'.+;(.+)\*(.+)')   #~LDR X1 = ......  ;NSObject *object
    pat1 = re.compile(r'.+#(classRef|selRef)_(.+)@PAGEOFF]')  #~LDR  X0, [X23,#classRef_NSNumber@PAGEOFF]  X0 is NSNumber
    pat6 = re.compile(r'.+#_(.+)_ptr')   #!  LDR  X8, #_kSecAttrAccount_ptr@PAG X8=kSecAttrAccount
    pat2 = re.compile(r'.+\[(.+)\]')   #~  LDR X3, [X8]   similar with MOV
    pat3 = re.compile(r'.+=_OBJC_CLASS_\$_(.+)')  #~LDR  X0, =_OBJC_CLASS_$_NSMutableURLRequest
    pat4 = re.compile(r'.+=(.+)')   #~LDR  X8, =_kCFStreamSSLAllowsAnyRoot

    m5 = pat5.match(asm)
    m  = pat.match(asm)
    m1 = pat1.match(asm)
    m6 = pat6.match(asm)
    m2 = pat2.match(asm)
    m3 = pat3.match(asm)
    m4 = pat4.match(asm)

    if m5:
        regs[des] = unicode(m5.group(1), errors='ignore')
    elif m:
        content = m.group(1)
        content.strip()
        regs[des] = content
    elif m1:
        content = m1.group(2)
        if content.endswith('_'):
            content = content[:-1]
        regs[des] = content
    elif m6:
        regs[des]=m6.group(1)
    elif m2:
        src = m2.group(1)
        if src in regs:
            regs[des]=regs[src]
        else:
            regs[des] = 'Unknown'
    elif m3:
        regs[des] = m3.group(1)
    elif m4:
        regs[des] = m4.group(1)
    else:
        regs[des] = 'Unknown'


def parse_B(func_name, addr):
    ignore_list = ["_objc_autorelease","_objc_release","_objc_retain","___stack_chk_fail"]
    imp_msg = ["_objc_msgSend", "_objc_msgSendSuper2", "_objc_msgSendSuper2_stret", "_objc_msgSend_stret"]
    lable = idc.GetOpnd(addr,0)

    for item in ignore_list:
        if item in lable:
            return


    reg_info = json.dumps(get_x0_to_x7_from_dict(regs))
    value = (func_name, lable, reg_info,)
    conn.execute("INSERT INTO BlTable VALUES (?,?,?)", value)
    '''
    if lable in imp_msg:
        value = (func_name, lable, reg_info, )
        conn.execute("INSERT INTO BlTable VALUES (?,?,?)",value)
    else:
        value = (func_name, lable, )
        conn.execute("INSERT INTO BlTable (FUNC, BL) VALUES (?,?)", value)
    '''
    conn.commit()


def parse_Other(addr):
    asm = idc.GetDisasm(addr)
    des = idc.GetOpnd(addr, 0)
    pat = re.compile(r'.+; "(.+)"')
    m   = pat.match(asm)
    if m:
        str = m.group(1)
        str = unicode(str, errors='ignore')
        regs[des]= str

def getX0FromFuncName(func_name):
    pat = re.compile(r".+\[(\S+).+")
    m = pat.match(func_name)
    if m:
        return m.group(1)
    else:
        return 'Unknown'


def analysis_Xt(addr, xt, start_addr):
    if idc.GetMnem(addr) == 'LDR':
        return parse_LDR(addr)

def get_x0_to_x7_from_dict(regs_dict):
    x_keys = ('X0','X1','X2','X3','X4','X5','X6','X7')
    newDict = dict()
    for item in regs_dict:
        if item in x_keys:
            newDict[item] = regs_dict[item]
    return newDict


#BL_dict = dict() #~no paramters call, no class and selector
regs = dict()  #store register value in this function

conn = sqlite3.connect('bl.db')
conn.execute('''CREATE TABLE IF NOT EXISTS BlTable
            (FUNC CHAR(100),
            BL CHAR(50),
            REGS CHAR(200));''')

sta = StaticAnalyzer()
sta.parse_rules()

# for func in Functions():
for func in sta.to_be_analyzed:
    print "this is main"
    if idc.SegName(func) == '__stubs':
        continue

    func_name = idc.GetFunctionName(func)
    print func_name

    regs.clear()
    regs['X0'] = getX0FromFuncName(func_name)
    regs['X1'] = 'Unknown'

    for addr in FuncItems(func):

        ins = idc.GetMnem(addr)

        if ins == 'MOV':
            parse_MOV(addr)
        elif ins == 'LDR' or ins=='LDUR':
            parse_LDR(addr)
        elif ins == 'B' or ins=='BL' or ins=='BX' or ins=='BLX' or ins=='BLR':
            parse_B(func_name, addr)
        elif ins == 'STR' or ins == 'STUR':
            parse_STR(addr)
        else:
            parse_Other(addr)

conn.close()
# Exit(0)








