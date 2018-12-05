# _*_coding:utf-8_*_
from idaapi import *
import re
import writeResult
'''

'''
#msg_send_dict = dict()  #~msg_send call
BL_dict = dict() #~no paramters call, no class and selector
regs = dict()  #store register value in this function

def parse_MOV(addr):
	des = idc.GetOpnd(addr, 0)
	src = idc.GetOpnd(addr, 1)
	#～change W to X , ignore W
	if des.startswith('W'):
		des = 'X'+des[1:]
				
	if src.startswith('#'):   # MOV X0 #0Xffff
		regs[des]=src[1:]
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
		regs[des] = m5.group(1)
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
	#print asm,'-> ',regs[des]


def parse_B(func_name, addr):
	asm = idc.GetDisasm(addr)
	#print asm
	lable = idc.GetOpnd(addr,0)
	
	if func_name not in BL_dict:
		listTmp = []
		BL_dict[func_name] = listTmp
	
	msgList = []
	msgList.append(lable)
	msgList.append(hex(addr))
	msgList.append(dict(regs))
	BL_dict[func_name].append(msgList)
	
	'''
	if lable =='_objc_msgSend' or lable =="_objc_msgSendSuper2" or lable =="_objc_msgSendSuper2_stret" or lable =="_objc_msgSend_stret":
		if func_name not in msg_send_dict:
			listTmp = []
			listTmp.append(dict(regs))
			msg_send_dict[func_name] = listTmp
		else:
			msg_send_dict[func_name].append(dict(regs))
	else:
		if lable in BL_dict:
			if func_name not in BL_dict[lable]:
				BL_dict[lable].append(func_name)
		else:
			BL_dict[lable]=[func_name]
	'''

def parse_Other(addr):
	asm = idc.GetDisasm(addr)
	des = idc.GetOpnd(addr, 0)
	pat = re.compile(r'.+"(.+)"')
	m   = pat.match(asm)
	if m:
		regs[des]=m.group(1)
		#print asm,'-> ',regs[des]

def getX0FromFuncName(func_name):
	pat = re.compile(r".+\[(\S+).+")
	m = pat.match(func_name)
	if m:
		return m.group(1)
	else:
		return 'Unknown'

def showResult():
	for func_name in BL_dict.keys():
		print 'fun_name',func_name
		for it in BL_dict[func_name]:
			print '-------------------------------'
			print 'bl->',it[0]
			print 'addr',it[1]
			regs = it[2]
			for reg in regs.keys():
				print func_name,'->',reg,':',regs[reg]

def analysis_Xt(addr, xt, start_addr):
	
	if idc.GetMnem(addr) == 'LDR':
		return parse_LDR(addr)


def main():
	

	
	for func in Functions():
		
		if idc.SegName(func) == '__stubs':
			continue
			
		func_name = idc.GetFunctionName(func)
		
		print 'start analyse [ ',func_name,' ]'
		print idc.SegName(func)
		regs.clear()
		regs['X0'] = getX0FromFuncName(func_name)
		regs['X1'] = 'Unknown'
        #if func_name != '-[PDKeychainBindingsController storeString:forKey:]' :
            #continue
		
		
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
				#print idc.GetMnem(addr)
				
		writeResult.writeMsg(BL_dict)
		BL_dict.clear()
			
			# _objc_msgSend, _objc_msgSend_Super, _objc_msgSend_stret
			#if idc.GetOpnd(addr, 0) == '_objc_msgSend':
			#	msg_send_dict[addr] = [func_name, regs['X0'], regs['X1']]
				
	'''
	for key in BL_dict.keys():
		for me in BL_dict[key]:
			print key,':',me
	'''
	#showResult();
	#writeResult.writeMsg(BL_dict)
	#writeResult.writeMsg(msg_send_dict)

	
	
if __name__ == '__main__':
	main()
	writeResult.writeToXml()
	Exit(0)
			
			
