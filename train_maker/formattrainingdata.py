import sys, os, pickle

d = pickle.load(open(sys.argv[1],'rb'))
named = {'+':'plus','-':'minus','/':'divide','*':'multiply','=':'equal'}
outf = sys.argv[1].split(".training")[0]+".data"
f = open(outf,'w')

for k,x in enumerate(['+','-','*','/']):
#for k,x in enumerate(['+','-']):
#for k,x in enumerate(['*','/']):
    '''
    if k < 2:
        k=0
    else:
        k=1
    '''
    #k = int(k>1)
    for v in d[x][0]:
        #print(v);input()
        f.write(str(k)+" ")
        for i,j in enumerate(v):
            f.write(str(i+1)+":"+str(j)+" ")
        f.write("\n")
    print(len(v))

f.close()
