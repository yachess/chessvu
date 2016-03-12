import os

class Node(object):
    def __init__(self,parent = None):
        self.parent = parent
        self.children = []
    def add(self, node):
        self.children.append(node)
        node.parent = self
    def remove(self, node):
        self.children.remove(node)
    def promote(self, node):
        self.remove(node)
        self.children.push(node)
    def __repr__(self):
        if not self.children:
            return self.data
        elif len(self.children)==1:
            return self.data + " " + self.children[0].__repr__()
        else:
            s = self.data + " " + self.children[0].data +"("
            for i,v in enumerate(self.children):
                if i==0 : continue
                s += v.__repr__()
            s += ")"
            s += self.children[0].__repr__()
            return s
    @staticmethod
    def print_node(node):
        print(node),
        if not node.children: return
        Node.print_node(node.children[0])
        for i,v in enumerate(node.children):
            if i==0: continue
            Node.print_node(v)
        
if __name__ == "__main__":
    n=Node()
    n.data = "node1"
    n2=Node()
    n2.data = "node2"
    n.add(n2)
    n3=Node()
    n3.data = "node3"
    n.add(n3)
    n4 = Node()
    n4.data = "node4"
    n2.add(n4)

#   print(n)
    Node.print_node(n)    
