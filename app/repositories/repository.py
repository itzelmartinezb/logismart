class Repository:
    def __init__(self, db): self.db=db
    def create(self,c,d): return self.db.create(c,d)
    def list(self,c,f=None): return self.db.find(c,f)
    def update(self,c,i,d): return self.db.update(c,i,d)
    def delete(self,c,i): return self.db.delete(c,i)
