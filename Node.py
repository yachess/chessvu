import os

class Node(object):
    def __init__(self,parent = None):
        self.parent = parent
        self.children = []
    def add(node):
        self.children.append(node)
        node.parent = self
    def remove(node):
        self.children.remove(node)
    def promote(node):
        self.remove(node)
        self.children.push(node)
if __name__ == "__main__":
    print "test"
