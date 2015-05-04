import copy
from sympy.solvers import solve
from sympy import Symbol

class StringEquation:
    def __init__(self, val):
        self.equation = str(val)
        self.parens = False
        self.equals = False
        # add boolean for parenthesis used or = used

    def addOperator(self, op):
        self.equation = self.equation + ' ' + op

    def addVal(self, val):
        self.equation = self.equation + ' ' + str(val)

    def addNext(self, op, val):
        if op is '=':
            self.equals = True
        self.equation = self.equation + ' ' + op + ' ' + str(val)

    def toString(self):
        return self.equation

    def solve(self):
        splitEquation = self.equation.split('=')
        equation = splitEquation[0] + '- (' + splitEquation[1] + ')'

        x = Symbol('x')
        solutions = []
        try:
            solutions = solve(equation, x)
        except:
            pass
        return solutions
