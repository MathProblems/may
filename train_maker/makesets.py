import sys
import json
import jsonrpclib
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
import pickle
brown_ic = wordnet_ic.ic('ic-brown.dat')
import unitConversion as uc


class aset:

    def __init__(self,num=None,entity=None,surface=None,idx=None):
        self.num = num
        self.entity = entity
        self.surface = surface
        self.idx = idx
        self.widx = (idx%1000)+1 if idx is not None else None
        self.container = None
        self.verbs = None
        self.adjs = None
        self.location = None
        self.contains = None

    def details(self,sf=True):

        string = "_____________\n"
        ordrd = sorted(self.__dict__.items())
        for x,y in ordrd:
            string += str(x)+" : "+str(y)+"\n"
        string += "_____________\n"
        if sf:
            print(string)
        else:
            return string


def vector(a,b,problem,target,feats=False):
    a = a[1]
    b = b[1]

    vec = []
    features = []

    features.append("acontainer bentity match")
    if a.container == None and b.entity == None: vec.append(0)
    elif a.container == b.entity: vec.append(1)
    else: vec.append(-1)

    features.append("acontainer bentity match")
    if b.container == None and a.entity == None: vec.append(0)
    elif b.container == a.entity: vec.append(1)
    else: vec.append(-1)

    features.append("bcontainer aentity match")
    if b.container == None and a.container == None: vec.append(0)
    elif b.container == a.container: vec.append(1)
    else: vec.append(-1)

    features.append("entity match")
    if b.entity == None and a.entity == None: vec.append(0)
    elif b.entity == a.entity: vec.append(1)
    else: vec.append(-1)

    features.append("adj match")
    if b.adjs == None and a.adjs == None: vec.append(0)
    elif b.adjs == a.adjs: vec.append(1)
    else: vec.append(-1)

    features.append("loc match")
    if b.location == None and a.location == None: vec.append(0)
    elif b.location == a.location: vec.append(1)
    else: vec.append(-1)

    features.append('number distances')
    try:
        distance = int(a.idx)-int(b.idx)
        distance = 1 / ( 10000 - distance )
    except: distance = 1
    vec.append(distance)


    features.append('a is target')
    if a.num == 'x': vec.append(1)
    else: vec.append(0)
    features.append('b is target')
    if b.num == 'x': vec.append(1)
    else: vec.append(0)

    features.append('a target match')
    if a.entity==target: vec.append(1)
    else: vec.append(0)
    features.append('b target match')
    if b.entity==target: vec.append(1)
    else: vec.append(0)


    #target features
    problem = problem.lower()
    asidx = a.idx//1000
    bsidx = b.idx//1000
    problem = problem.split(" . ")
    asent = problem[asidx].split(" ")
    bsent = problem[bsidx].split(" ")

    features.extend(["a times",'b times',"a total",'b total',"a together",'b together',"a more", 'b more' ,"a less",'b less',"a add",'b add',"a divide",'b divide',"a split",'b split',"a equal",'b equal',"a equally",'b equally'])
    for li in ["times","total","together","more","less","add","divide","split","equal","equally"]:
        if li in asent:
            vec.append(1)
        else:
            vec.append(0)
        if li in bsent: vec.append(1)
        else: vec.append(0)

    problem = problem[-1]
    if " how " in problem:
        problem = problem.split(" how ")[-1]
    elif " what " in problem:
        problem = problem.split(" what ")[-1]

    if " , " in problem:
        problem = problem.split(" , ")[0]
    features.append("in all")
    if "in all" in problem: vec.append(1)
    else: vec.append(0)
    features.append("end with")
    if "end with" in problem: vec.append(1)
    else: vec.append(0)
    problem = problem.split()
    features.extend(["times","total","together","more","less","add","divide","split","left","equal","equally","now",'left','start'])
    for li in ["times","total","together","more","less","add","divide","split","left","equal","equally","now",'left','start']:
        if li in problem:
            vec.append(1)
        else:
            vec.append(0)


    if a.verbs == None or b.verbs == None:
        dist = 1
    else:
        avl = a.verbs.split(" ")
        bvl = b.verbs.split(" ")

        if len([x for x in avl if x in bvl ])>0:
            dist = 0
        else:
            dist = 1
            for aw in avl:
                asyns = wn.synsets(aw)
                for asyn in asyns:
                    for bw in bvl:
                        bsyns = wn.synsets(bw)
                        for bsyn in bsyns:
                            if asyn._pos == bsyn._pos: 
                                try:
                                    sim = 1/(1+bsyn.res_similarity(asyn,brown_ic))
                                except:
                                    sim = 2
                                if sim < dist:
                                    dist = sim
    features.append("Verb distance")
    vec.append(dist)

    #verb similarity
    verbs = ['be', 'do', 'go', 'have', 'leave', 'keep', 'get', 'make', 'tell', 'place', 'lose', 'change', 'give', 'hand', 'take', 'buy', 'receive', 'put', 'set', 'like', 'want', 'call', 'divide', 'split']

    for v in verbs:
        features.append(v)
        vsyns = wn.synsets(v, pos='v')

        dist = 1
        if b.verbs is not None:
            for verb in b.verbs.split(' '):
                bsyns = wn.synsets(verb, pos='v')
                if verb == v:
                    dist = 0
                else:
                    for vsyn in vsyns:
                        for bsyn in bsyns:
                            try:
                                sim = 1/(1+vsyn.lin_similarity(bsyn,brown_ic))
                            except:
                                sim = 2
                            if sim < dist:
                                dist = sim
        vec.append(dist)
    if feats:
        return (features, vec)
    else:
        return vec



def combine(a,b,op):
    #takes two entities and returns a combo of them.
    c = aset()
    if a.container == b.entity or op == '-':
        #multiplication or subtraction swap
        t = a
        a = b
        b = t



    for k in a.__dict__:
        if k == "num":
            c.num = "("+str(a.__dict__[k])+op+str(b.__dict__[k])+")"
        else:
            c.__dict__[k]= b.__dict__[k]
    #print(c.__dict__)
    return c



def entityextract(story):
    sets = []
    #this function makes the preliminary sets, finding the quantified entities. 
    for j,s in enumerate(story):
        deps = s['indexeddependencies']
        words = s['words']
        surfaces = [x[0] for x in words]
        
        nums = [(x[1],x[2]) for x in deps if x[0]=='num' or x[0]=='number' or x[0]=='det']
        nums.extend([(x[2],x[1]) for x in deps if x[0]=="prep_of" and (x[1].split("-")[0].isdigit() or x[1].rsplit("-",maxsplit=1)[0] in ['half','third','quarter'])])
        for w,n in nums:
            n,nidx = n.split("-")
            nidx = int(nidx)-1
            w,widx = w.rsplit("-",maxsplit=1)
            widx = int(widx)-1
            if words[widx][1]["PartOfSpeech"] in ["NN","NNS"]:
                if n=='each' and w=='cost':
                    #let this slip through
                    continue
                lemma = words[widx][1]["Lemma"]
                sets.append(((j*1000)+nidx,aset(n,lemma,w,j*1000+widx)))
    
        #deal with each where parse fails AND IS BAD:
        if 'each' in surfaces:
            eachi = surfaces.index('each')
            if (j*1000)+eachi in [x[0] for x in sets]:
                continue
            nextword = words[eachi+1]
            if nextword[0] in [',','.']:
                nns = [x for x in words if x[1]["PartOfSpeech"]=="NNS"]
                if nns:
                    nextword = nns[-1]
            lemma = nextword[1]["Lemma"]
            sets.append(((j*1000)+eachi,aset('each',lemma,nextword[0],j*1000+eachi+1)))

    ents = [x[1].entity for x in sets]
    #get question entity
    q = story[-1]
    j = len(story)-1
    words = q["words"]
    deps = q['indexeddependencies']
    if "what" in [x[0] for x in words]:
        targets = [x[2] for x in deps if 'what' in x[1] and x[0]=='nsubj']
        if len(targets)==1:
            t,tidx = targets[0].rsplit("-",maxsplit=1)
            tidx = int(tidx)-1
            lemma = words[tidx][1]["Lemma"]
            sets.append((j*1000+tidx,aset('x',lemma,t,j*1000+tidx)))
    if "how" in [x[0] for x in words]:
        targets = [x[1] for x in deps if x[2].rsplit("-",maxsplit=1)[0] in ['many','much']]
        if len(targets)==1:
            t,tidx = targets[0].rsplit("-",maxsplit=1)
            tidx = int(tidx)-1
            if words[tidx][1]["PartOfSpeech"] in ["NN","NNS"]:
                lemma = words[tidx][1]["Lemma"]
                sets.append((j*1000+tidx,aset('x',lemma,t,j*1000+tidx)))
            else:
                good = 0
                if t == "more":
                    targets = [x[1] for x in deps if x[2].rsplit("-",maxsplit=1)[0] in ['more']]
                    if targets:
                        t,tidx = targets[0].rsplit("-",maxsplit=1)
                        tidx = int(tidx)-1
                        if words[tidx][1]["PartOfSpeech"] in ["NN","NNS"]:
                            lemma = words[tidx][1]["Lemma"]
                            sets.append((j*1000+tidx,aset('x',lemma,t,j*1000+tidx)))
                            good = 1
                if good == 0:
                    sets.append((j*1000+tidx,aset('x','NONE','NONE',None)))
        else:
            '''
            targets = [x[1] for x in deps if x[2].rsplit("-",maxsplit=1)[0]=='how']
            if targets:
                t,tidx = targets[0].rsplit('-',maxsplit=1)
                tidx = int(tidx)-1
                if t == 'far':
                    sets.append((j*1000+tidx,aset('x','DISTANCE','DISTANCE')))
                if t == 'long':
                    sets.append((j*1000+tidx,aset('x','LENGTH','LENGTH')))
            '''
            howidx = [i for i,x in enumerate(words) if x[0]=='how'][0]
            nextword = words[howidx+1]
            if nextword[0] == 'far':
                sets.append((j*1000+howidx+1,aset('x','DISTANCE','DISTANCE',None)))
            if nextword[0] == 'long':
                sets.append((j*1000+howidx+1,aset('x','LENGTH','LENGTH',None)))




            
    for j,s in enumerate(story):
        deps = s['indexeddependencies']
        words = s['words']
        othernums = [((j*1000+i), x[0]) for i,x in enumerate(words) if x[1]["PartOfSpeech"]=="CD"]
        othernums = [x for x in othernums if x[0] not in [y[0] for y in sets]]
        if othernums:
            for idx,n in othernums:
                prev=1
                #this is a hack To fix the "and" bug
                if 'and' in [x[0] for x in words[idx%1000:idx%1000+7]]:
                    #use next jawn
                    nextjawn = [x for x in sets if x[0]>idx and x[0]<(((idx//1000)+1)*1000)]
                    if nextjawn:
                        nextjawn = nextjawn[0][1]
                        sets.append((idx,aset(n,nextjawn.entity,nextjawn.surface,None)))
                        prev=0
                if prev==1:
                    prevjawn = [x for x in sets if x[0]<idx]
                    if prevjawn:
                        prevjawn = prevjawn[-1][1]
                        sets.append((idx,aset(n,prevjawn.entity,prevjawn.surface,None)))
                    else:
                        #find the NNSess
                        #print(idx,n)
                        nns = []
                        for j,s in enumerate(story):
                            nns.extend([(j*1000+i,w) for i,w in enumerate(s['words']) if w[1]["PartOfSpeech"] == "NNS"])
                        #print(nns)
                        if nns:
                            prev = [x[1] for x in nns if x[0]<idx]
                            if prev:
                                prevjawn = prev[-1]
                                sets.append((idx,aset(n,prevjawn[1]["Lemma"],prevjawn[0],None)))
                            else:
                                prevjawn = nns[0][1]
                                sets.append((idx,aset(n,prevjawn[1]["Lemma"],prevjawn[0],None)))


    
    xset = [x for x in sets if x[1].num=='x']
    if xset:
        xset = xset[0]
        if xset[1].entity=="NONE":
            #is there a NNS near to the question?
            words = story[-1]['words']
            idx = [x[0] for x in words].index('how')
            prev = 1
            if idx>=0:
                words = words[idx:idx+4]
                nns = [x for x in words if x[1]['PartOfSpeech']=='NNS']
                if nns:
                    xset[1].entity = nns[0][1]["Lemma"]
                    xset[1].surface = nns[0][0]
                    prev = 0

            if prev:
                prev = [x for x in sets if x[0]<xset[0]]
                prev = prev[-1][1]
                xset[1].entity = prev.entity
                xset[1].surface = prev.surface



    #REMOVE DUPS THIS IS BAD:
    i = 0
    #print(sets)
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
    #print(sets)
    '''
    seen = []
    for i,x in enumerate(sets):
        if x[0] in seen:
            with open("data/"+str(x[0])+'dups.txt','w') as f:
                dups = [y for y in sets if y[0] == x[0]]
                string = ''
                for x in dups:
                    string += x[1].details(False)
                f.write(string)
            del(sets[i])
        else:
            seen.append(x[0])
    '''
    sets = sorted(sets)
    return sets
    

def distance(a,b,story):
    pass
    

def containers(sets,story):
    for j,s in enumerate(story):
        deps = s['indexeddependencies']
        thissentsets = [x for x in sets if x[0]//1000 == j]
        thiseach = [x for x in thissentsets if x[1].num in ['each','a','an','the','every','per','one','1']]
        if len(thiseach)>0:
            thisothers = [x for x in thissentsets if x not in thiseach]
            if thisothers:
                for eidx,e in thiseach:
                    #which is closer: next ent or prev?
                    if e.num in ['a','an','per']:
                        prev = [x for x in thisothers if x[0]<eidx and x[0]>eidx-5]
                        if prev:
                            target=prev[-1]
                            target[1].container = e.num+' '+e.entity
                            e.contains = target[1].entity
                    else:
                        prev = [x for x in thisothers if x[0]<eidx]
                        nexxt = [x for x in thisothers if x[0]>eidx]
                        if not nexxt:
                            target = prev[-1]
                        else:
                            #really should check distances, but for now lets not
                            target = nexxt[0]
                        target[1].container = e.num+' '+e.entity
                        e.contains = target[1].entity
                    

        for e in thissentsets:

            #get verbs, adj, location
            esurface = e[1].surface+'-'+str(e[1].widx)
            #print(esurface)
            vbs = [x for x in deps if x[2]==esurface and x[0]=='dobj']
            if vbs:
                e[1].verbs = ' '.join([x[1].split('-')[0] for x in vbs])

            adjs = [x for x in deps if x[1]==esurface and x[0]=='amod']
            if adjs:
                e[1].adjs = ' '.join([x[2].split('-')[0] for x in adjs])

            # container is location
            elocs = [x[2].split("-")[0] for x in deps if x[0] in ['prep_in','prep_on','prep_at'] and x[1] == esurface]
            if elocs:
                e[1].location = ' '.join(elocs)

            if e[1].container:
                continue


            # container is nsubj
            if vbs:
                for x in vbs:
                    verb = x[1]
                    #find subj, this is container
                    vsubj = [x for x in deps if x[1]==verb and x[0] in ['nsubj','nsubjpass']]
                    if vsubj:
                        e[1].container = ' '.join([x[2].split('-')[0] for x in vsubj])

    return sets

def floatcheck(n):
    try:
        n = float(n)
        return True
    except:
        return False
    
def fix_each(sets):
    for i in range(len(sets)):
        idx,e = sets[i]
        #if e.num in ['each','a','an','the','every']:
        if e.contains is not None:
            if e.num in ['each','every','per','a','an','per','one','1']:
            #others = [x for x in sets if x[1].entity == e.entity and x[0] != idx and len([y for y in x[1].num if y.isdigit()])>0]
            #if len(others)>=1:
                if len(sets)>i+1:
                    if sets[i+1][1].entity == e.contains:
                        idx = sets[i+1][0]+1
                        sets[i] = (idx,e)
                        
                #e.num = '1'
            others = [x for x in sets if x[1].entity == e.entity and x[0] != idx]
            others = [x for x in others if x[1].num=='x' or floatcheck(x[1].num)]
            onum = [x[1].num for x in others]
            if 'x' in onum:
                e.num = 'x'
            elif others:
                prev = [x for x in others if x[0]<idx]
                if prev:
                    e.num = prev[-1][1].num
                    prev[-1][1].num = "USED"
                else:
                    e.num = others[0][1].num
                    others[0][1].num="USED"
            
                
    return sets

        
def circumscription(sets,story):
    setssofar = []
    for j,s in enumerate(story):
        deps = s['indexeddependencies']
        words = s['words']
        setssofar.extend([x for x in sets if x[0]//1000 == j])
        thissentnums = [(i,x) for i,x in enumerate(words) if x[1]["PartOfSpeech"]=='CD']


def rewrite(sets,story):
    newstory=''
    for j,s in enumerate(story):
        newsent = ''
        thissentsets = {x[0]%1000:x for x in sets if x[0]//1000 == j and x[1].widx is None}
        for i,w in enumerate(s['words']):
            if i in thissentsets:
                newsent += w[0] + " " + thissentsets[i][1].surface + " "
            else:
                newsent += w[0] + " " 
        newstory += newsent + " " 
    print(newstory)

    
def makesets(story):
    sets = entityextract(story)
    #print([(x[0],x[1].entity,x[1].num) for x in sets])
    sets = containers(sets,story)
    #print([(x[0],x[1].entity,x[1].num) for x in sets])
    #sets = circumscription(sets,story)
    sets = uc.main(sets)
    #print([(x[0],x[1].entity,x[1].num) for x in sets])
    sets = fix_each(sets)
    #print([(x[0],x[1].entity,x[1].num) for x in sets])
    #rewrite(sets,story)
    

    '''
    THIS CODE PRODUCES ? ENTITIES WHICH ARE NOT O.W. CAPTURED BY PREVIOUS RULES
    
    ents = set([x[1].entity for x in sets])
    idxs = [x[1].idx for x in sets]
    for j,s in enumerate(story):
        deps = s['indexeddependencies']
        lemmas = [x[1]["Lemma"] for x in s['words']]
        for e in ents:
            for i,l in enumerate(lemmas):
                if l == e:
                    eidx = j*1000+i
                    if eidx in idxs:
                        # this occurrence is already accounted for
                        continue
                    else:
                        print(j*1000+i)
                        surface = s['words'][i][0]
                        edeprep = surface+'-'+str(i+1)
                        edep = [x[2].split("-")[0] for x in deps if x[1] == edeprep and x[0] == 'det']
                        if edep:
                            num = edep[0]
                        else:
                            num = "?"
                        sets.append(((j*1000)+i,aset(num,l,surface,j*1000+i)))
    '''
    
    i=0
    while i < len(sets):
        x = sets[i]
        i+=1
        dups = [y for y in sets if y[0]==x[0]]
        if len(dups)>1:
            for y in dups[1:]:
                sets.remove(y)
        
    #fix idx
    for idx,x in sets:
        x.idx = idx
    try:
        sets = sorted(sets)               
    except:
        print(sets)
        exec(input())
    return sets

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

def bug():
    print("bug")
    ip = 0
    while ip==0:
        inp = input()
        if inp == 0:
            ip=1
        else:
            exec(inp)

if __name__ == "__main__":
    nlp = StanfordNLP()
    wps = open(sys.argv[1]).readlines()
    wps = list(reversed(wps))
    for k in range(len(wps)):
        print(k)
        problem = wps[k].lower()
        print(problem)
        story = nlp.parse(problem)
        sets = makesets(story["sentences"])

        for x in sets:
            x[1].details()
        if len(sets)<2:
            print("few sets")
            bug()
        input()

        sets = [x[1] for x in sets]
        nums = [x.num for x in sets]
        if 'x' not in nums:
            bug()



