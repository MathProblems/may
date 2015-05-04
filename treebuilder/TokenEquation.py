class TokenEquation:
    def __init__(self, val, ops):
        self.tokens = val
        self.operators = ops

    def getToken(self, i):
        return self.tokens[i]
    def getOperator(self, i):
        return self.operators[i]
    def getTokens(self):
        return self.tokens[:]
    def getOperators(self):
        return self.operators[:]

    @property
    def toString(self):
        if len(self.tokens) == 1:
            e = self.tokens[0]
        else:
            e = '( ' + self.tokens[0] + ' ) '
            for i in range(1, len(self.tokens)):
                eq = '( ' + self.tokens[i] + ' ) '
                e = '( ' + e + ' ' + self.operators[i-1] + ' ' + eq + ' )'
        return e

    def copyOf(self):
        tokens = self.tokens[:]
        operators = self.operators[:]
        c = TokenEquation(tokens, operators)
        return c