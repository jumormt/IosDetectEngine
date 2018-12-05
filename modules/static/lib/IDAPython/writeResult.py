# _*_coding:utf-8_*_
from xml.dom.minidom import Document

'''
def writeBL(BL_dict):
	doc = Document()
	BL = doc.createElement('BL')
	doc.appendChild(BL)
	
	for calledApi in BL_dict.keys():
		called = doc.createElement('Called')
		called.setAttribute('name',calledApi)
		BL.appendChild(called)
		for callerApi in BL_dict[calledApi]:
			caller = doc.createElement('Caller')
			callerText = doc.createTextNode(callerApi)
			caller.appendChild(callerText)
			called.appendChild(caller)
	
	f = open('BL.xml','w')
	#doc.writexml(f)
	doc.writexml(f,addindent = ' '*4,newl ='\n',encoding = 'utf8')
	f.close()
'''	
doc = Document()
root = doc.createElement('Root')
doc.appendChild(root)
	
def writeMsg(BL_dict):
	for func_name in BL_dict.keys():
		func_ele = doc.createElement('function')
		func_ele.setAttribute('name',func_name)
		root.appendChild(func_ele)
		for b_info in BL_dict[func_name]:
			msg_ele = doc.createElement('b')
			msg_ele.setAttribute('name',b_info[0])
			msg_ele.setAttribute('addr',b_info[1])
			func_ele.appendChild(msg_ele)
			regs_dict=b_info[2]
			content = ''
			for regs_key in regs_dict.keys():
				content = content+regs_key+'='+regs_dict[regs_key]
				content_textNode = doc.createTextNode(content)
				msg_ele.appendChild(content_textNode)
				content = ''
				#regs_ele = doc.createElement(regs_key)
				#regs_text = doc.createTextNode(regs_dict[regs_key])
				#regs_ele.appendChild(regs_text)
				#msg_ele.appendChild(regs_ele)
				
	
	
def writeToXml():
	f = open('bl.xml','w')
	doc.writexml(f, addindent = '',newl ='\n',encoding = 'utf8')
	f.close()
	
	
	
'''def main():
	msg_send_dict = dict()
	regs1 = dict()
	regs1['X0'] = '0x1111'
	regs1['X1'] = '0xffff'
	regs2 = dict()
	regs2['X2'] = '0x121'
	regs2['X3'] = '0xf0f'
	a = list()
	a.append(regs1)
	a.append(regs2)
	
	msg_send_dict["fun1"]=a
	msg_send_dict['fun2']=a
	
	writeMsg(msg_send_dict)
	
	#writeBL(BL_dict)


if __name__ == '__main__':
	main()
'''
