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
    if len(sys.argv)>1:
        wps = open(sys.argv[1]).readlines()
        answs = open(sys.argv[2]).readlines()
    else:
        wps = open("emnlp_noIrrelev_p.txt").readlines()
        answs = open("emnlp_noIrrelev_a.txt").readlines()
    problematic = open('nogoodtrainproblems','w')

    bigtexamples = {x:([],[]) for x in ["+","*",'/','-','=']}
    replacements = {' two ':' 2 '," three ":' 3 ',' four ':' 4 ',' five ':' 5 ',' six ':' 6 ',' seven ':' 7 ',' eight ':' 8 ',' nine ':' 9 ',' ten ':' 10 ',' eleven ':' 11 ',' week ':' 7 days ',' dozen ':' 12 of ', ' dozens ': ' 12 ', ' twice ':' 2 '}

    for k in range(len(wps)):
        print(k)
        problem = wps[k].lower()
        for r in replacements:
            problem = problem.replace(r,replacements[r])
        #extract numbers:
        #problem = ' '.join([x.replace(",","") for x in problem.split()])
        story = nlp.parse(problem)
        numbs = makesets.makesets(story['sentences'])

        numlist = [(cleannum(v.num),v) for k,v in numbs]
        numlist = [x for x in numlist if x[0]!='']

        allnumbs = {str(k):v for k,v in numlist}
        if 'x' not in allnumbs:
            if 'x*' not in allnumbs:
                problematic.write('no x :'+problem); continue
            

        objs = {k:(0,v) for k,v in numlist}

        print('start solving')
        print(numlist)
        if len(numlist)<2:
            problematic.write("not enough numbers : "+problem);continue
            
        ST = Solver([x[0] for x in numlist if x[0]!='x'])
        answers = ST.solveEquations(float(answs[k]))
        print('done solving')
        #filter out where = in middle if simpler eq exists
        simpleranswers = [x for x in answers if x.split(" ")[1] == '=' or x.split(" ")[-2]=="="]
        if not answers:
            continue
        if simpleranswers:
            answers = simpleranswers
        else:
            print(answers)
            problematic.write("not simple : "+problem);continue

        answervals = [x for x in answers[0].split(" ") if x not in ['+','-','/','=',')','(','*']]
        numvals = [x[0] for x in numlist if x[0] in answervals]
        xidx = numvals.index("x")
        rightidx = [i for i,x in enumerate(answers) if [z for z in x.split(" ") if z not in ['+','-','/','=',')','(','*']].index('x')==xidx]
        xrightanswers = [answers[i] for i in rightidx]
        if xrightanswers:
            answers = xrightanswers

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
    pickle.dump(bigtexamples,open('data/dev_training.pickle','wb'))




            




if __name__=="__main__":
    dotrain()
    #mkgoodtrain()


