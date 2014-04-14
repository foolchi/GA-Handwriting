#!/usr/bin/python3
''' Check the result '''

import sys
sys.path.append('/usr/local/lib/python3.3/dist-packages/')
sys.path.append('/usr/lib/python3/dist-packages/')
sys.path.append('../data')
import cymysql
from train import Digital
import switchdata
from genetic import Group, mul
import math
from PIL import Image
from train import picprint

SIZE = 1024
xrange = 64
yrange = 64
xsize = 32
ysize = 32
globalpixelresult = []
globalgene = []
globalgroup = []

rec = ['../data/rec_0.bmp', '../data/rec_1.bmp', '../data/rec_2.bmp', '../data/rec_3.bmp', '../data/rec_4.bmp', '../data/rec_5.bmp', '../data/rec_6.bmp', '../data/rec_7.bmp', '../data/rec_8.bmp', '../data/rec_9.bmp']

def datainitial(filelist = rec):
    ''' Read all the picture data and saved to sql database'''
    pixels = []
    conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
    cur = conn.cursor()
    query = 'INSERT INTO checkdata(id, pixel, result, density) VALUES (%s, %s, %s, %s)'
    id = 0
    for fileindex in range(10):
        im = Image.open(filelist[fileindex])
        id = 1000*fileindex
        for i in range(20):
            #print("i:",i,end=' ')
            for j in range(23):
                #print("j:",j)
                temp = Image.new(im.mode, [xrange, yrange])
                for ix in range(xrange):
                    for iy in range(yrange):
                        temp.putpixel((ix, iy), im.getpixel((i*xrange+ix, j*yrange+iy)))
                dtemp = Digital(0, temp)
                pixels = dtemp.getpixel()
                density = pixels.count(1)
                if (density == 0):
                    continue
                picprint(pixels)
                pimplode = switchdata.implode(pixels)
                cur.execute(query, (id, pimplode, fileindex, density))
                id += 1
            conn.commit()
    conn.close()

    print("load done")
    '''
    group0 = Group(0)
    group0.generatescores(pixels)
    group0.nextgeneration()
    '''
def checkdataload():
    ''' Load the data from sql '''
    global globalpixelresult
    conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
    cur = conn.cursor()
    globalpixelresult = []
    cur.execute('SELECT pixel, density ,result, id FROM picdata')
    for r in cur.fetchall():
        pixdata = switchdata.explode(r[0])
        density = int(r[1])
        if (density == 0):
            continue
        pixdata = [pix/density for pix in pixdata]
        pixresult = []
        pixresult.append(pixdata)
        pixresult.append(int(r[2]))
        pixresult.append(int(r[3]))
        globalpixelresult.append(pixresult)
#print(len(globalpixels),'*',len(globalpixels[0]), '*', len(globalpixels[0][0]))
    conn.close()

def geneload():
    ''' Load the genetic data from sql '''
    global globalgene
    conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
    cur = conn.cursor()
    globalgene = []
    cur.execute('SELECT * FROM genedata')
    for r in cur.fetchall():
        genetemp = []
        genetemp.append(switchdata.explode(r[0]))
        genetemp.append(int(r[1]))
        globalgene.append(genetemp)
    conn.close()
    return globalgene

def groupload():
    ''' Load the group data from sql '''
    global globalgroup
    globalgroup = []
    conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
    cur = conn.cursor()
    cur.execute('SELECT * FROM globaldata')
    fetchall = cur.fetchall()
    size = len(fetchall)
    print(size)
    if (size >= 1):
        globalgroup = [float(r) for r in fetchall[size-1]]
    return globalgroup
    conn.close()

def checkall():
    ''' Check the result '''
    rightanswer = [0]*10
    checked = [0]*10
    n = -1
    for check in globalpixelresult:
        n += 1
        if (n % 10 != 0):
            continue
        pixels = check[0]
        result = check[1]
        checked[result] += 1
        checkdata = [0,0,0,0,0,0,0,0,0,0]
        for generesult in globalgene:
            gene = generesult[0]
            gresult = generesult[1]
            #print(gresult)
            checkdata[gresult] += math.fabs(mul(pixels, gene) - globalgroup[gresult])
        answer = checkdata.index(min(checkdata))
        print('ID: ', check[2], 'Result: ', result, 'Answer: ', answer)
        if (result == answer):
            rightanswer[result] += 1
    for i in range(10):
        print('Group: ',i, 'Checked: ', checked[i],  'RightAnswer: ', rightanswer[i])

if __name__ == '__main__':
    checkdataload()
    print('checkdataload done')
    geneload()
    print('geneload done')
    groupload()
    print('groupload done')
    #print(globalgroup)
    checkall()

