
class Node:
    cur_node = None
    def __init__(self, dat):
        self.parent = None
        self.childs = []
        self.data = dat

    def is_leaf(self):
        return len(self.childs) == 0

    def append(self,node):
        self.childs.append(node)
        node.parent = self

    def remove(self,node):
        childs.remove(node)
        node.parent = None

    @staticmethod
    def forward():
        if len(Node.cur_node.childs) != 0:
            Node.cur_node = Node.cur_node.childs[0]
    

    @staticmethod
    def backward():
        if Node.cur_node.parent != None:
            Node.cur_node = Node.cur_node.parent

    def __repr__(self):
        a = self.data
        a += " "
        for i,node in enumerate(self.childs, 1):
            if i==2:
                a += "( "
            a += node.__repr__()
        if len(self.childs) >= 2:
            a += ") "
        return a

if __name__ == "__main__":
    a = Node("e4")
    b = Node("e6")
    c = Node("d4")

    a.append(b)
    b.append(c)
    b.append(Node("Nf3"))

    Node.cur_node = a
    print Node.cur_node
    Node.forward()
    print Node.cur_node
    Node.backward()
    print Node.cur_node
    pass

