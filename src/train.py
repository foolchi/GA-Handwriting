#!/usr/bin/python3
''' Genetic Algorithm for handwriting recognition '''
import sys
sys.path.append('../data')

from PIL import Image
from genetic import Group, mul
import cymysql
import switchdata
from copy import deepcopy
import math
import multiprocessing

POPSIZE = 50
SIZE = 1024
xrange = 64
yrange = 64
xsize = 32
ysize = 32
globalpixels = []
globalselected = []
globalgeneration = [0]*10
g = []

class Digital:
    ''' Read from each picture and transform the handwriting numbers to 32*32 pixels '''
    def __init__(self, answer, pixels):
        self.answer = answer
        self.pic = pixels
        self.pixels = pixels.load()
        #self.pixinit(xrange, yrange)

    def pixinit(self,x,y):
        for i in range(x):
            for j in range(y):
                if (self.pixels[i,j] == 255):
                    self.pixels[i,j] = 0
                else:
                    self.pixels[i,j] = 1

    def getbound(self):
        self.xstart = 0
        self.xend = xrange-1
        self.ystart = 0
        self.yend = yrange-1
        xdefaultsum = 255*xrange
        ydefaultsum = 255*yrange

        for i in range(xrange):
            sum = 0
            for j in range(yrange):
                sum += self.pixels[i,j]
            if (sum != xdefaultsum):
                self.xstart = i
                break

        for i in range(xrange):
            sum = 0
            for j in range(xrange):
                sum += self.pixels[xrange-1-i, j]
            if (sum != xdefaultsum):
                self.xend = xrange-1-i
                break

        for i in range(yrange):
            sum = 0
            for j in range(xrange):
                sum += self.pixels[j, i]
            if (sum != ydefaultsum):
                self.ystart = i
                break

        for i in range(yrange):
            sum = 0
            for j in range(xrange):
                sum += self.pixels[j, yrange-1-i]
            if (sum != ydefaultsum):
                self.yend = yrange-1-i
                break
        #print(self.xstart,self.xend, self.ystart, self.yend)

    def resize(self):
        xbound = self.xend - self.xstart + 1
        ybound = self.yend - self.ystart + 1
        temp = Image.new(self.pic.mode, [xbound, ybound])
        for i in range(xbound):
            for j in range(ybound):
                temp.putpixel((i,j),
                        self.pic.getpixel((self.xstart+i, self.ystart+j)))
        self.pixels = temp.resize([xsize, ysize]).load()
        #temp.resize([xsize, ysize]).show()

    def getpixel(self):
        self.getbound()
        self.resize()
        self.pixinit(xsize, ysize)
        pixels = []
        for i in range(xsize):
            for j in range(ysize):
                pixels.append(self.pixels[j,i])
        return pixels


def picprint(picarray):
    for i in range(xsize):
        for j in range(ysize):
            print(picarray[i*xsize+j],end=' ')
            #print(picarray[i*xsize+j],end='')
        print('')

def picwrite(picarray, filename):
    for i in range(xsize):
        for j in range(ysize):
            filename.write(str(picarray[i*xsize+j]))
            filename.write(' ')
        filename.write('\n')

def picprint2(picarray, xsize, ysize):
    for i in range(xsize):
        for j in range(ysize):
            if (picarray[i,j] == 0):
                print(0,end='')
            elif (picarray[i,j] == 255):
                print(1, end='')
            else:
                print(' ',end='')
        print('')


def datainitial():
    ''' Read the pictures and save the pixels data to sql database '''
    pixels = []
    filelist = ['../data/appr_0.bmp', '../data/appr_1.bmp', '../data/appr_2.bmp', '../data/appr_3.bmp', '../data/appr_4.bmp', '../data/appr_5.bmp',
            '../data/appr_6.bmp', '../data/appr_7.bmp', '../data/appr_8.bmp', '../data/appr_9.bmp']
    #filelist = ['rec_0.bmp', 'rec_1.bmp', 'rec_2.bmp', 'rec_3.bmp', 'rec_4.bmp', 'rec_5.bmp',
    #        'rec_6.bmp', 'rec_7.bmp', 'rec_8.bmp', 'rec_9.bmp']
    #im = Image.open("./rec_0.bmp")
    conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
    cur = conn.cursor()
    query = 'INSERT INTO picdata(id, pixel, result, density) VALUES (%s, %s, %s, %s)'
    id = 0
    for fileindex in range(10):
        #f = open(filelist[fileindex]+'.txt', 'w')
        im = Image.open(filelist[fileindex])
        id = 1000*fileindex
        for j in range(32):
            print("j:",j,end=' ')
            for i in range(20):
                print("appr_", fileindex, ".bmp","(", j,",",i,")")
                temp = Image.new(im.mode, [xrange, yrange])
                for ix in range(xrange):
                    for iy in range(yrange):
                        temp.putpixel((ix, iy), im.getpixel((i*xrange+ix, j*yrange+iy)))
                dtemp = Digital(fileindex, temp)
                pixels = dtemp.getpixel()
                density = pixels.count(1)
                if (density == 0):
                    continue
                #picprint(pixels)
                #picwrite(pixels, f)
                pimplode = switchdata.implode(pixels)
                cur.execute(query, (id, pimplode, fileindex, density))
                id += 1
            conn.commit()
        #f.close()
    conn.close()

    print("load done")


def dataload():
    ''' Load data from sql '''
    #g = Group(defaultgroup)
    conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
    cur = conn.cursor()
    for i in range(10):
        pixels = []
        cur.execute('SELECT pixel, density FROM picdata where result=%s', (i))
        for r in cur.fetchall():
            pixdata = switchdata.explode(r[0])
            density = int(r[1])
            if (density == 0):
                continue
            pixdata = [pix/density for pix in pixdata]
            pixels.append(pixdata)
        globalpixels.append(pixels)
    #print(len(globalpixels),'*',len(globalpixels[0]), '*', len(globalpixels[0][0]))
    conn.close()


def train(lock, group, defaulttimes = 10):
    ''' Train for one group '''
    #global globalselected
    global globalgeneration
    g = Group(group)
    n = defaulttimes
    generation = globalgeneration[group]
    pixels = globalpixels[group]

    while (n > 0):
        print("Group:", group, "Generation:", generation)
        g.generatescores(pixels)
        g.nextgeneration()
        n -= 1
        generation += 1
    globalgeneration[group] = generation
    lock.acquire()
    g.save()
    lock.release()


def trainall(defaultgeneration = 50):
    ''' Train for all groups '''
    for i in range(defaultgeneration):
        for j in range(10):
            train(j, 1)
        checkglobalerror()


def multitrain(defaultgeneration = 10):
    ''' Using 10 processes to train '''
    multip = []
    lock = multiprocessing.Lock()
    for i in range(10):
        p = multiprocessing.Process(name = 'Group'+str(i), target = train, args = (lock, i, defaultgeneration))
        multip.append(p)
        p.start()
    for p in multip:
        p.join()
    checkglobalerror()


def checkglobalerror():
    ''' Check error rate '''
    print("Check error")
    global globalpixels
    global g
    g = []
    scores = []
    for group in range(10):
        gtemp = Group(group, initial = False, checkerror = True)
        gtemp.generatescores(globalpixels[group])
        g.append(gtemp)

    lock = multiprocessing.Lock()
    multip = []
    for group in range(10):
        pixelgroup = globalpixels[group]
        p = multiprocessing.Process(target = geterror, args = (group, pixelgroup, lock))
        multip.append(p)
        p.start()

    for p in multip:
        p.join()

    for genegroup in g:
        #genegroup.evolution()
        genegroup.nextgeneration()
        genegroup.save()

def geterror(group, pixelgroup, lock):
    global g
    smin = 100
    sminindex = [0, 0]
    for pixels in pixelgroup:
        for i in range(10):
            genegroup = g[i]
            for j in range(POPSIZE):
                stemp = math.fabs(mul(genegroup.arrays[j], pixels)-genegroup.averagescores[j])
                if (stemp < smin):
                    smin = stemp
                    sminindex = [i, j]
        if (sminindex[0] == group):
            lock.acquire()
            g[i].error[j] -= 1
            lock.release()


if __name__ == '__main__':
    datainitial()
    dataload()

    multitrain()
