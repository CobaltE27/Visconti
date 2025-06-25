class staticish:
    val = 1
    def meth(self):
        return self.val
    
print(staticish().meth())