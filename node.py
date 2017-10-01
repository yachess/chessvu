
class Node:
    cur_node = None
    def __init__(self, dat):
        self.parent = None
        self.childs = []
        self.data = dat
        self.next_index = 0

    def is_leaf(self):
        return len(self.childs) == 0

    @classmethod
    def clear(cls):
        Node.cur_node = None

    @classmethod
    def append(cls, node):
        if Node.cur_node == None:
            Node.cur_node = node
            node.parent = None
            node.childs = []
        else:
            Node.cur_node.childs.append(node)
            node.parent = Node.cur_node
            Node.cur_node = node

    @classmethod
    def remove(cls):
        node = Node.cur_node 
        Node.cur_node = Node.cur_node.parent
        
        if Node.cur_node :
            Node.cur_node.childs.remove(node)

        node.parent = None

    @classmethod
    def go_next(cls):
        if Node.cur_node == None:
            return
        if len(Node.cur_node.childs) != 0:
            Node.cur_node = Node.cur_node.childs[Node.cur_node.next_index]

    @classmethod
    def go_prev(cls):
        if Node.cur_node == None:
            return
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
    Node.go_next()
    print Node.cur_node
    Node.go_prev()
    print Node.cur_node
    pass

