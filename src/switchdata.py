#!/usr/bin/python3

def implode(array):
    ''' Int array to string '''
    string = ''
    for i in array:
        string += str(i)
    return string

def explode(string):
    ''' String to int array '''
    array = []
    size = len(string)
    for i in range(size):
        array.append(int(string[i]))
    return array


if __name__ == '__main__':
    a = [1,2,3,4,5,6,7,8,9]
    string = implode(a)
    print(string)
    b = explode(string)
    print(b)
    for i in b:
        print(i)
