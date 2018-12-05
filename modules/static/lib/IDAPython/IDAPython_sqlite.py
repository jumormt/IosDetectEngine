# _*_coding:utf-8_*_
from idaapi import *
import re
import sqlite3
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

#BL_dict = dict() #~no paramters call, no class and selector
regs = dict()  #store register value in this function

conn = sqlite3.connect('bl.db')
conn.execute('''CREATE TABLE IF NOT EXISTS BlTable
			(FUNC CHAR(100),
			BL CHAR(50),
			REGS CHAR(200));''')


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


def main():

	for func in Functions():
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


	
	
if __name__ == '__main__':
	main()
	conn.close()
	Exit(0)
			
			
