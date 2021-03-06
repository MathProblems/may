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
sys.path.insert(0, '../treebuilder')
from StringTemplate import StringTemplate
from svmutil import *
import makesets
from sympy.solvers.solvers import solve

multi = None

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()


def compute(p,op,e,target,problem):
    vec = makesets.vector((0,p),(0,e),problem,target)
    #if p.ent == e.ent and op in ['*','/']:
    #    val = 0
    #else:
    if True:
        op_label, op_acc, op_val = svm_predict([-1], [vec], multi ,'-q -b 1')
        #pmop_label, pmop_acc, pmop_val = svm_predict([-1], [vec], pm ,'-q -b 1')
        #mmop_label, mmop_acc, mmop_val = svm_predict([-1], [vec], md ,'-q -b 1')
        op_val=op_val[0]
        #pmop_val = pmop_val[0]
        #mmop_val = mmop_val[0]
        if op == '+':
            val = op_val[0]#*pmop_val[0]
        if op == '-':
            val = op_val[1]#*pmop_val[1]
        if op == '*':
            val = op_val[2]#*mmop_val[0]
        if op == '/':
            val = op_val[3]#*mmop_val[1]


    c = makesets.combine(p,e,op)
    return (val,c)

def cleannum(n):
    return ''.join([x for x in n if x.isdigit() or x=='.' or x=='x' or x=='x*'])


def infer(q,a,VERBOSE):
    wps = open(q).readlines()
    answs = open(a).readlines()
    problematic = open('somethingWrongProblems','a')

    ar = [0,0]
    sr = [0,0]
    mr = [0,0]
    dr = [0,0]

    replacements = {' two ':' 2 '," three ":' 3 ',' four ':' 4 ',' five ':' 5 ',' six ':' 6 ',' seven ':' 7 ',' eight ':' 8 ',' nine ':' 9 ',' ten ':' 10 ',' eleven ':' 11 ', ' twice ':' 2 '}
    right = 0
    guesses = 0
    ad = []
    wrong = []
    multiops = 0
    multiopsright = 0
    
    replacements = {' two ':' 2 '," three ":' 3 ',' four ':' 4 ',' five ':' 5 ',' six ':' 6 ',' seven ':' 7 ',' eight ':' 8 ',' nine ':' 9 ',' ten ':' 10 ',' eleven ':' 11 ', ' twice ':' 2 '}

    for k in range(len(wps)):
        if VERBOSE:
            for i in range(len(wps)):
                print(i,wps[i])
            k = int(input())
        print(k)
        problem = wps[k].lower()
        #First preprocessing, tokenize slightly
        problem = problem.strip().split(" ")
        for i,x in enumerate(problem):
            if len(x)==0:continue
            if x[-1] in [',','.','?']:
                problem[i] = x[:-1]+" "+x[-1]
        problem = ' '.join(problem)
        problem = " " + problem + " "
        print(problem)

        for r in replacements:
            problem = problem.replace(r,replacements[r])

        story = nlp.parse(problem)
        sets = makesets.makesets(story['sentences'])
            #REMOVE DUPS THIS IS BAD:
        i = 0
        while i < len(sets):
            x = sets[i]
            dups = [y for y in sets if y[1].num == x[1].num]
            if len(dups)>1:
                for x in dups[1:]:
                    sets.remove(x)
            i+=1

        print("Sets detected: ")
        for x in sets:
            x[1].details()
        numlist = [(cleannum(v.num),v) for k,v in sets]
        numlist = [x for x in numlist if x[0]!='']
        if VERBOSE:
            for z,v in numlist:
                v.details()
            input()

        allnumbs = {str(k):v for k,v in numlist}
            

        objs = {k:(0,v) for k,v in numlist}


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
            wrong.append(k)
            continue
        

        integerproblem = all([float(x[0]).is_integer() for x in numlist if x[0]!='x'])
        multi = False
        if len(objs)>3:
            multiops+=1
            multi = True
        if VERBOSE:
            print(objs,numlist,[v.num for k,v in sets])
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
        print('\n Top scoring 3 equations: ')
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
            # wrapped in a "check for complex number" try statement :/
            try:
                if guess < 0:
                    continue
            except:
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
            ops = [x for x in ST.equations[i].toString() if x in ['+','-','*','/']]
            if guess == answ: 
                print("\nCORRECT")
                tright=1
                ar[0] += ops.count('+')
                sr[0] += ops.count('-')
                mr[0] += ops.count('*')
                dr[0] += ops.count('/')
            else:
                print("\nINCORRECT")
            ar[1] += ops.count('+')
            sr[1] += ops.count('-')
            mr[1] += ops.count('*')
            dr[1] += ops.count('/')
            print("Guessed Equation : ",ST.equations[i].toString() )

            print("Guess : ",guess,"\nTrue Answer :", answ, '\n\n')
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
    print(ar,sr,mr,dr)


if __name__=="__main__":
    q, a, mfile = sys.argv[1:4]
    multi = svm_load_model(mfile)
    VERBOSE=False
    TRAIN=False
    if len(sys.argv)>4:
        if sys.argv[4]=='v':
            VERBOSE=True
    infer(q,a,VERBOSE)


