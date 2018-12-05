import hashlib

def get_md5(input_set):
    # print 'input is :', input_set
    temp_list = []
    for input in input_set:
        m = hashlib.md5()
        m.update(input)
        temp_list.append(m.hexdigest())
    temp_swap_list =[]
    for item in temp_list:
        temp_swap_list.append(item.swapcase())
    temp_list.extend(temp_swap_list)
    return temp_list

# if __name__ == '__main__':
#     list = ['www','qqq']
#     print get_md5(list)