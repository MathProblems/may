from StringTemplate import StringTemplate
from copy import deepcopy

class Solver:
    def __init__(self, b):
        self.b = b
        self.template = StringTemplate(b)


    def solveEquations(self, val):
        answers = self.template.solveEquations(val)
        if len(answers) == 0:
            if len(self.b) > 1:
                answers = self.leaveOneOut(val)
        return answers

    def leaveOneOut(self, val):
        answers = []
        i = -1
        j = -1

        # first check 1.0
        if 1.0 in self.b:
            b = deepcopy(self.b)
            i = b.index(1.0)
            n = b[:i] + b[i+1:]
            t = StringTemplate(n)
            answers += t.solveEquations(val)
        if len(answers) > 0:
            return answers
        if 2.0 in self.b:
            b = deepcopy(self.b)
            j = b.index(2.0)
            n = b[:j] + b[j+1:]
            t = StringTemplate(n)
            answers += t.solveEquations(val)
        if len(answers) > 0:
            return answers
        for k in range(len(self.b)):
            if k != i and k != j:
                b = deepcopy(self.b)
                n = b[:k] + b[k+1:]
                t = StringTemplate(n)
                answers += t.solveEquations(val)
        if len(answers) == 0:
            answers = self.leaveTwoOut(val)
        return answers

    def leaveTwoOut(self, val):
        answers = []
        if(len(self.b) > 2):
            for i in range(len(self.b)):
                for j in range(i+1, len(self.b)):
                    if i != j:
                        b = deepcopy(self.b)
                        n = b[:i] + b[i+1:j] + b[j+1:]
                        t = StringTemplate(n)
                        answers += t.solveEquations(val)
        return answers
