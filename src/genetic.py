#!/usr/bin/python3

''' Pattern Recognition using Genetic Algorithm '''
import sys
sys.path.append('../data')

import random,math
import cymysql
import switchdata
from copy import deepcopy

POPSIZE = 50 # Population size
SELECTED = 26 # Selected for each generation
DSIZE = 1024 # Genetic vector size 1*1024
GROUPSIZE = 10 # Each group represents one number
arrayrand = [0,0,0,0,0,1,2,3,4,5] # Genetic vector number range
defaultcrate = 0.1 # Default cross rate
CROSSOVERTIME = 50 # Cross times for each generation
defaultmrate = 0.1 # Default mutation rate

class Group:
    def __init__(self, result, initial = False, checkerror = False):
        self.result = result
        self.average = 0
        self.scores = []
        self.averagescores = []
        self.arrays = []
        self.checkerror = checkerror
        self.error = [0]*POPSIZE
        self.globaldata = [-5]*GROUPSIZE
        if initial:
            self.initial()
        else:
            self.read()

    def initial(self):
        p = POPSIZE
        while (p > 0):
            n = DSIZE
            array = []
            while (n > 0):
                array.append(random.choice(arrayrand))
                n = n-1
            self.arrays.append(array)
            p = p-1


    def groupcrossover(self, crossrate = defaultcrate):
        ''' Crossover process '''
        n = CROSSOVERTIME
        while (n > 0):
            p1 = random.randint(0, POPSIZE-1)
            p2 = random.randint(0, POPSIZE-1)
            if (p1 != p2):
                self.arrays[p1], self.arrays[p2] = crossover(self.arrays[p1], self.arrays[p2])
            n = n-1

    def mutate(self, mutaterate = defaultmrate):
        ''' Mutation process '''
        for p in self.arrays:
            for i in range(DSIZE):
                r = random.random()
                if (r > mutaterate):
                    continue
                elif (r > 2 * mutaterate/3):
                    p[i] = 0
                elif (r > mutaterate/3):
                    if (p[i] != 5):
                        p[i] += 1
                else:
                    if (p[i] != 0):
                        p[i] -= 1

    def defaultsortfunction(self, i):
        ''' Sort function '''
        currentaverage = self.averagescores[i]
        distance = math.fabs(currentaverage - self.average)
        if (self.checkerror):
            return distance +self.error[i]
        else:
            return distance

    def evolution(self):
        tobesorted = [(self.defaultsortfunction(i), i) for i in range(POPSIZE)]
        tobesorted.sort()
        self.arrays = [self.arrays[i] for (f, i) in tobesorted]
        self.arrays = self.arrays[:SELECTED]
        while (len(self.arrays) < POPSIZE):
            for i in range(SELECTED):
                size = len(self.arrays)
                if (size >= POPSIZE):
                    break;
                p1, p2 = crossover(self.arrays[i], self.arrays[SELECTED-1-i])
                self.arrays.append(p1)
                self.arrays.append(p2)

    def generatescores(self, pixels):
        size = len(pixels)
        if (size == 0):
            return
        scores = []
        averagescores = []
        for i in range(POPSIZE):
            score = []
            for j in range(size):
                score.append(mul(self.arrays[i], pixels[j]))
            scores.append(score)
            averagescores.append(sum(score)/len(score))
        self.scores = scores
        self.averagescores = averagescores
        self.average = sum(averagescores)/len(averagescores)
        self.globaldata[self.result] = self.average

    def nextgeneration(self):
        ''' Generate next generation '''
        self.evolution()
        self.groupcrossover()
        self.mutate()
        self.error = [0]*POPSIZE
        print(self.globaldata)

    def getresult(self, i, array):
        score = mul(self.arrays[i], array)
        distances = [math.fabs(score - globalscore) for globalscore in self.globaldata]
        return distances.index(min(distances))

    def perror(self, i, pixels):
        ncount = len(pixels)
        if (ncount == 0):
            return 0
        nerror = 0
        for pixel in pixels:
            if (self.getresult(i, pixel) == self.result):
                nerror += 1
        return nerror/ncount

    def geterror(self, selectedpixels):
        for i in range(POPSIZE):
            perror = 0
            for pixels in selectedpixels:
                perror += self.perror(i, pixels)
            self.error.append(perror/3)

    def save(self):
        ''' Save the generation data to sql database '''
        conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
        cur = conn.cursor()
        cur.execute('DELETE FROM genedata WHERE result=%s', (self.result))
        conn.commit()
        query = 'INSERT INTO genedata(array, result) VALUES (%s, %s)'
        query2 = 'INSERT INTO globaldata(g0,g1,g2,g3,g4,g5,g6,g7,g8,g9) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        for array in self.arrays:
            cur.execute(query, (switchdata.implode(array), self.result))
        conn.commit()
        temp = [-5]*GROUPSIZE
        cur.execute('SELECT * FROM globaldata')
        fetchall = cur.fetchall()
        size = len(fetchall) - 1
        if (size != -1):
            temp = [float(data) for data in fetchall[size]]
        for i in range(GROUPSIZE):
            if ((i != self.result) and (self.globaldata[i] != temp[i])):
                self.globaldata[i] = temp[i]
        cur.execute(query2, tuple(self.globaldata))
        conn.commit()
        conn.close()

    def read(self):
        ''' Load data from sql '''
        conn = cymysql.connect(user = 'foolchi', passwd = '1', db = 'pic')
        cur = conn.cursor()
        cur.execute('SELECT array FROM genedata WHERE result=%s', (self.result))
        fetchall = cur.fetchall()
        size = len(fetchall) - 1
        pop = 0
        if (size < POPSIZE-1):
            self.initial()
        else:
            while (size >= 0):
                self.arrays.append(switchdata.explode(fetchall[size][0]))
                size -= 1
                pop += 1
                if (pop >= POPSIZE):
                    break

            print('Group:', self.result,', read array success')

        cur.execute('SELECT * FROM globaldata')
        fetchall = cur.fetchall()
        size = len(fetchall) - 1
        if (size != -1):
            array = fetchall[size]
            self.globaldata = [float(data) for data in array]
        conn.close()


def crossover(p1, p2):
    crosspoint = random.randint(1, DSIZE-2)
    ptemp = deepcopy(p1)
    p1[:crosspoint] = p2[:crosspoint]
    p2[:crosspoint] = ptemp[:crosspoint]
    return p1, p2

def mul(a1, a2):
    size = len(a1)
    #if (size != len(a2)):
     #   return 0
    mulsum = 0
    for i in range(size):
        mulsum += a1[i]*a2[i]
    return mulsum
