import sys
import json
import jsonrpclib
#from nltk.corpus import wordnet as wn
#from nltk.corpus import wordnet_ic
import pickle
import numpy as np
#sys.path.insert(0, '/Users/rikka/liblinear-1.94/python')
#from liblinearutil import *
sys.path.insert(0, '/Users/rikka/libsvm-3.18/python')
sys.path.insert(0, './treebuilder')
from StringTemplate import StringTemplate
from svmutil import *
import makesets
from sympy.solvers.solvers import solve

model = svm_load_model("5.2.m")

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()


def training(trips,problem,target):
    #this function take the trips and creates positive and negative training instances from them
    
    texamples = {x:([],[]) for x in ["+","*"]}
    for op,a,b in trips:
        vec = makesets.vector(a,b,problem,target)
        for k in texamples:
            if op == k:
                texamples[k][0].append(vec)
            else:
                texamples[k][1].append(vec)

    return texamples


def compute(p,op,e,target,problem):
    vec = makesets.vector((0,p),(0,e),problem,target)
    #if p.ent == e.ent and op in ['*','/']:
    #    val = 0
    #else:
    if True:
        op_label, op_acc, op_val = svm_predict([-1], [vec], model ,'-q -b 1')
        #sop_label, sop_acc, sop_val = svm_predict([-1], [vec], smodel ,'-q -b 1')
        #print(op_label,op_acc,op_val)
        op_val=op_val[0]
        #sop_val=sop_val[0]
        #op_val = [op_val[0]*sop_val[0],op_val[1]*sop_val[0],op_val[2]*sop_val[1],op_val[3]*sop_val[1]]
        if op == '+':
            val = op_val[0]
        if op == '-':
            val = op_val[1]
        if op == '*':
            val = op_val[2]
        if op == '/':
            val = op_val[3]


    c = makesets.combine(p,e,op)
    return (val,c)

def cleannum(n):
    return ''.join([x for x in n if x.isdigit() or x=='.' or x=='x' or x=='x*'])

if __name__ == "__main__":

    VERBOSE = False
    if len(sys.argv)>2:
        VERBOSE = True

    wps = open("emnlp_evenLess.p").readlines()
    answs = open("emnlp_evenLess.a").readlines()
    right = 0
    guesses = 0
    ad = []
    wrong = []
    multiops = 0
    multiopsright = 0
    replacements = {' two ':' 2 '," three ":' 3 ',' four ':' 4 ',' five ':' 5 ',' six ':' 6 ',' seven ':' 7 ',' eight ':' 8 ',' nine ':' 9 ',' ten ':' 10 ',' eleven ':' 11 ',' week ':' 7 days ',' dozen ':' 12 of ', ' dozens ': ' 12 ', ' twice ':' 2 '}
    for k in range(len(wps)):
        if VERBOSE:
            for i in range(len(wps)):
                print(i,wps[i])
            k = int(input())
        print(wps[k])
        problem = wps[k].lower()
        for r in replacements:
            problem = problem.replace(r,replacements[r])
        #extract numbers:
        problem = ' '.join([x.replace(",","") for x in problem.split()])



        story = nlp.parse(problem)
        numbs = makesets.makesets(story['sentences'])
        numlist = [(cleannum(v.num),v) for k,v in numbs]
        numlist = [x for x in numlist if x[0]!='']

        allnumbs = {str(k):v for k,v in numlist}
        for v,x in numlist:
            x.details()
        constraints = []
        for i in range(len(numlist)):
            if numlist[i][0][-1] == "*":
                if i==0:continue
                constraints.append(numlist[i-1][0]+" * "+numlist[i][0][:-1])
                numlist[i] = (''.join([x for x in numlist[i][0] if x not in ['*','/']]),numlist[i][1])
                numlist[i][1].num = numlist[i][0]
            elif numlist[i][0][0] == "*":
                if i==0:continue
                numlist[i] = (''.join([x for x in numlist[i][0] if x not in ['*','/']]),numlist[i][1])
                tmp = numlist[i-1]
                numlist[i-1]=numlist[i]
                numlist[i]=tmp
                constraints.append(numlist[i-1][0]+" * "+numlist[i][0][1:])
            elif numlist[i][0][-1] == "/":
                if i==0:continue
                constraints.append(" / "+numlist[i][0][:-1])
                numlist[i] = (''.join([x for x in numlist[i][0] if x not in ['*','/']]),numlist[i][1])
        objs = {k:(0,v) for k,v in numlist}
        if len(objs)<2:
            wrong.append(k)
            continue
        if 'x' not in objs:
            continue
        integerproblem = all([float(x[0]).is_integer() for x in numlist if x[0]!='x'])
        multi = False
        if len(objs)>3:
            multiops+=1
            multi = True
        if VERBOSE:
            print(objs,numlist,[v.num for k,v in numbs])
        #print(allnumbs)


        state = []
        #print(numlist)

        

        #for e in allnumbs.items():
        #print(numlist)
        numidxlist = [x[0] for x in numlist]
        ST = StringTemplate(numidxlist, inf=True)
        scores = []
        for j,eq in enumerate(ST.equations):
            #print(j,eq.toString())
            good = False
            if len(constraints)==0:
                good = True
            else:
                for constraint in constraints:
                    if constraint in eq.toString():
                        good = True
            if not good:
                scores.append(-0.2)
                continue
            
                    
            thisscore = []
            #print(eq.toString())
            #determine score for this eq
            l,r = [x.strip().split(' ') for x in eq.toString().split('=')]
            #print(l,r)
            
            if len(r)>1 and len(l)>1:
                scores.append(-0.2);continue
            if len(r)>1: 

                compound = r
                target = l[0]
            else:
                #print(constraints)
                compound = l
                target = r[0]
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
                if substr in objs:
                    pute = objs[substr]
                    #print(pute[0],pute[1].num)
                else:
                    p,op,e = subeq
                    #print(p,op,e)
                    p = objs[p][1]
                    e = objs[e][1]
                    op = op.strip()
                    pute = compute(p,op,e,target,problem)
                    #print("OPERATION SELECTED: ",op)
                    #p.details()
                    #e.details()
                    #print(substr,pute[1].num)
                    objs[substr]=pute
                if pute == -1:
                    exit()
                score,c = pute
                thisscore.append(score)
            if target[1][1].entity != c.entity:
                thisscore.append(-0.2)
            #print("WAT",thisscore,c.ent,c.num)
            
            scores.append(sum(thisscore))

            #print(compound)
        m = np.argmax(scores)
        #print(scores[m],ST.equations[m].toString())
        srt = sorted([(x,i) for i,x in enumerate(scores)],reverse=True)
        print('\n Top 3 equations: ')
        for x,i in srt[:3]:
            print(x,ST.equations[i].toString())

        '''
        try:
            if target.ent=='dozen':
                guess = solve('('+numlist[0].num+'/12)'+"-"+target.num,'x')[0]
                print(numlist[0].num+"/12="+target.num)
            else:
                guess = solve(numlist[0].num+"-"+target.num,'x')[0]
                print(numlist[0].num+"="+target.num)
        '''
        eqidxs = [y[0] for y in sorted(enumerate(scores),key=lambda x:x[1],reverse=True)]
        eqnidsx = [x[1] for x in srt]
        seen = []
        tright = 0
        for i in eqidxs:
            if len(seen)>=1:break
            eq = ST.equations[i].toString()
            #eq = eq.replace("=",'-')
            splitEquation = eq.split('=')
            eq = splitEquation[0] + '- (' + splitEquation[1] + ')'
            #print(scores[i], eq)
            try:
                guess = solve(eq,'x')[0]
            except: guess = -1

            # This is the non-negative constraint
            if guess < 0:
                continue

            #this is a constraint agianst fractional answers when the problem is integers
            if not guess.is_integer:
                if integerproblem:
                    continue

            if guess not in seen:
                seen.append(guess)
            else: 
                continue
            answ = float(answs[k])
            if guess == answ: 
                print("\n CORRECT")
                tright=1
            else:
                print("\n INCORRECT")

            print("Guess : ",guess,"\nAnswer :", answ, '\n\n')
        guesses += len(seen)
        if tright==1:
            if multi:
                multiopsright += 1
            right +=1
        else:
            wrong.append(k)

        #break
        if VERBOSE: input()
        continue
    print(right,guesses)
    print(multiops,multiopsright)

