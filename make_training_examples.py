import signal
import sys
import json
import jsonrpclib
import makesets
import pickle
sys.path.insert(0, './treebuilder')
from Solver import Solver
from sympy.solvers.solvers import solve

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()


def training(trips,problem,target):
    #this function take the trips and creates positive and negative training instances from them
    
    texamples = {x:([],[]) for x in ["+","*",'/','-','=']}
    for op,a,b in trips:
        vec = makesets.vector(a,b,problem,target)
        texamples[op][0].append(vec)

    return texamples

def cleannum(n):
    return ''.join([x for x in n if x.isdigit() or x=='.' or x=='x' or x=='x*'])

def kill(signum, frame):
    raise Exception("end of time")

def dotrain():
    fn = sys.argv[1]
    with open(fn) as f:
        f = f.split("___")
        for c in f:
            p,a,t,n,

        for j,eq in enumerate(answers):
            trips = []
            print(j,eq)
            l,r = [x.strip().split(' ') for x in eq.split('=')]
            
            compound = l if len(r)==1 else r
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
    pickle.dump(bigtexamples,open('data/training.pickle','wb'))




            




if __name__=="__main__":
    dotrain()



