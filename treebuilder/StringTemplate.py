from TokenEquation import TokenEquation
from StringEquation import StringEquation

class StringTemplate:
    def __init__(self, b, inf=False):
        self.b = b
        self.vals = []
        self.operators = ['+', '-', '/', '*']
        self.eqOperators = ['+', '-', '/', '*', '=']
        self.baseEqs = []
        self.equations = []

        if inf:
            self.createEquationsInf()
        else:
            self.createEquations()
        self.addParens()

    def addParens(self):
        for eq in self.baseEqs:
            splitEquation = eq.equation.split(' = ')
            l = self.createTokens(splitEquation[0])
            r = self.createTokens(splitEquation[1])
            left = self.parenthesis(l)
            right = self.parenthesis(r)
            for l in left:
                for r in right:
                    self.equations += [StringEquation(l.toString + ' = ' + r.toString)]

    def createTokens(self, eq):
        eqs = []
        curr = eq.split(' ')
        tokens = []
        operators = []
        for i in range(len(curr)):
            if i%2 == 0:
                tokens.append(str(curr[i]))
            else:
                operators.append(str(curr[i]))
        return TokenEquation(tokens, operators)

    def parenthesis(self, eq):
        eqs = []
        operators = eq.getOperators()
        tokens = eq.getTokens()
        if len(eq.tokens) > 2:
            for t in range(len(eq.tokens)-1):
                i = '( ' + tokens[t] + ' ' + operators[t] + ' ' + tokens[t+1] + ' )'
                values = tokens[0:t] + [i] + tokens[t+2:len(tokens)]
                ops = operators[0:t] + operators[t+1:len(operators)]
                tEquation = TokenEquation(values, ops)
                eqs += self.parenthesis(tEquation)
            return eqs
        else:
            if len(operators) > 0:
                t = '' + tokens[0] + ' ' + operators[0] + ' ' + tokens[1] + ''
                return [TokenEquation([t], [])]
            else:
                return [TokenEquation([tokens[0]], [])]

    def createEquations(self):
        '''
        self.vals = self.b
        self.initialize()
        
        '''
        # x can be in any location
        self.vals = ['x'] + self.b
        for i in range(len(self.b)+1):
            self.vals = self.b[0:i] + ['x'] + self.b[i:len(self.b)]
            self.initialize()
        
        
    def createEquationsInf(self):
        self.vals = self.b
        self.initialize()

    def initialize(self):
        if len(self.vals) is 2:
            e = StringEquation(self.vals[0])
            e.addNext('=', self.vals[1])
            self.baseEqs = [e]
        else:
            baseEquations = [StringEquation(self.vals[0])]
            for i in range(1, len(self.vals)):
                tempEquations = []
                for eq in baseEquations:
                    if eq.equals:
                        for op in self.operators:
                            e = StringEquation(eq.equation)
                            e.equals = eq.equals
                            e.addNext(op, self.vals[i])
                            if (op is '*') and (self.vals[i] == 1.0 or self.vals[i-1] == 1.0):
                                pass
                            elif (op is '/') and self.vals[i] == 1.0:
                                pass
                            else:
                                tempEquations.append(e)
                    else:
                        if i == (len(self.vals) - 1):
                            e = StringEquation(eq.equation)
                            e.addNext('=', self.vals[i])
                            tempEquations.append(e)
                        else:
                            for op in self.eqOperators:
                                e = StringEquation(eq.equation)
                                e.equals = eq.equals
                                e.addNext(op, self.vals[i])
                                if (op is '*') and (self.vals[i] == 1.0 or self.vals[i-1] == 1.0):
                                    pass
                                elif (op is '/') and self.vals[i] == 1.0:
                                    pass
                                else:
                                    tempEquations.append(e)
                baseEquations = tempEquations

            self.baseEqs += baseEquations

    def solveEquations(self, val):
        answers = []
        for eq in self.equations:
            a = eq.solve()
            if len(a) > 0:
                if a[0] == val:
                    answers += [eq.toString()]
        return answers

    def printBase(self):
        result =[]
        for eq in self.baseEqs:
            result += [eq.toString]
        return result

    #@property
    def toString(self):
        result = []
        for eq in self.equations:
            result += [eq.toString()]
        return result
