import signal
import sys
import json
import jsonrpclib
sys.path.insert(0, '../')
import makesets
import pickle
sys.path.insert(0, '../treebuilder')
from Solver import Solver
from sympy.solvers.solvers import solve
from random import randint

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()

def cleannum(n):
    return ''.join([x for x in n if x.isdigit() or x=='.' or x=='x' or x=='x*'])

def kill(signum, frame):
    raise Exception("end of time")

def training(trips,problem,target):
    #this function take the trips and creates positive and negative training instances from them
    
    texamples = {x:([],[]) for x in ["+","*",'/','-','=']}
    for op,a,b in trips:
        vec = makesets.vector(a,b,problem,target)
        texamples[op][0].append(vec)

    return texamples

def parse(q):
    eqs = []
    wps = []
    with open(q) as f:
        g = f.read()
        g = g.split("___")
        for line in g:
            line = line.split('\n')
            eq = [x for x in line if '=' in x]
            prblm = [x for x in line if ' how ' in x or ' what ' in x]
            print(prblm,eq)
            eqs.append(eq)
            wps.append(prblm)
    return wps,eqs


def make_eq(q):
    bigtexamples = {x:([],[]) for x in ["+","*",'/','-','=']}
    wps,eqs= parse(q)
    

    for k in range(len(wps)):
        if len(wps[k])==0:continue
        problem = wps[k][0].lower()
        story = nlp.parse(problem)
        sets = makesets.makesets(story['sentences'])
        i = 0
        print(sets)
        while i < len(sets):
            dups = [y for y in sets if y[1].idx != None]
            dups = [y for y in dups if y[1].idx == sets[i][1].idx]
            if len(dups)>1:
                good = [y for y in dups if len([x for x in y[1].num if x.isdigit()])>0]
                if good:
                    others = [x for x in dups if x!=good[0]]
                    for x in others:
                        sets.remove(x)
                else:
                    # just pick 1
                    for x in dups[1:]:
                        sets.remove(x)
            i+=1


        xidx = [x for x in sets if x[1].num=='x']
        if not xidx:
            problematic.write('no x :'+problem); continue

        #TODO look for 2 xes
        '''
        xidx = xidx[0][0]
        postx = [x for x in numbs if x[0]>=xidx]
        if len(postx)>1:
            # 2 vals to right
            twoToRight = True
        else:
            twoToRight = False
        '''

        



        numlist = [(cleannum(v.num),v) for k,v in sets]
        numlist = [x for x in numlist if x[0]!='']

        allnumbs = {str(k):v for k,v in numlist}
            

        objs = {k:(0,v) for k,v in numlist}
        answers = eqs[k]

        for j,eq in enumerate(answers):
            trips = []
            print(j,eq)
            l,r = [x.strip().split(' ') for x in eq.split('=')]
            
            compound = r if len(l)==1 else l
            simplex = l if len(l)==1 else r
            target = simplex[0]
            target = (target,objs[target])

            #find innermost parens?
            while len(compound)>1:
                if "(" in compound:
                    rpidx = (len(compound) - 1) - compound[::-1].index('(')
                    lpidx = rpidx+compound[rpidx:].index(")")
                    subeq = compound[rpidx+1:lpidx]
                    substr = "("+''.join(subeq)+")"
                    compound = compound[:rpidx]+[substr]+compound[lpidx+1:]
                else:
                    subeq = compound[0:3]
                    substr = "("+''.join(subeq)+")"
                    compound = [substr]+compound[3:]
                if True:
                    p,op,e = subeq
                    #print(p,op,e)
                    p = objs[p]
                    e = objs[e]
                    op = op.strip()
                    trips.append((op,p,e))
                    pute = (0,makesets.combine(p[1],e[1],op))
                    #print("OPERATION SELECTED: ",op)
                    #p.details()
                    #e.details()
                    #print(substr,pute[1].num)
                    objs[substr]=pute
                if pute == -1:
                    exit()
            if simplex == l:
                trips.append(("=",objs[simplex[0]],objs[compound[0]]))
            else:
                trips.append(("=",objs[compound[0]],objs[simplex[0]]))
            t = training(trips,problem,target)
            for op in t:
                bigtexamples[op][0].extend(t[op][0])
                bigtexamples[op][1].extend(t[op][1])
            print(op,len(bigtexamples[op][0]))
    pickle.dump(bigtexamples,open('data/gold_training.pickle','wb'))




if __name__=="__main__":
    q = sys.argv[1]
    make_eq(q)


