# Model class

import os
import copy

# for color table look up:`xfce4-terminal --color-table`

Blk=0
Wht=1

R=0
N=1
B=2
Q=3
K=4
P=5

UNCERTAIN=-1
    
# Returns directional rays of 64 squares
def directional_rays():
    rays = []           # Three dimensional lists of directional rays.
    for sq in range(64):
        rays.append([
            [i for i in range (sq+1, 64, +1) if sq/8 == i/8 and i < 64], 
            [i for i in range (sq+9, 64, +9) if sq%8 < i%8 and i < 64],
            [i for i in range (sq+8, 64, +8) if i<64],
            [i for i in range (sq+7, 64, +7) if sq%8> i% 8 and i < 64],
            [i for i in range (sq-1, -1, -1) if sq/8 == i/8 and i >= 0],
            [i for i in range (sq-9, -1, -9) if sq%8 > i%8 and i >= 0],
            [i for i in range (sq-8, -1, -8) if i >= 0],
            [i for i in range (sq-7, -1, -7) if sq%8 < i%8 and i >= 0], 
        ])
    return rays

# Returns pawn attack maps of 64 squares
def pawn_attack_maps():
    # Create black pawn attack map then rotate 180deg to make white's attack
    bp_atk = [[] for _ in range(64)]
    for sq in range(8, 64-8):
        if sq%8 != 0:
            bp_atk[sq].append(sq + 7)
        if sq%8 != 7:
            bp_atk[sq].append(sq + 9)
    wp_atk=[]
    for i in bp_atk:
        wp_atk.append(map(lambda x:63-x, i))
    wp_atk.reverse()
    return [bp_atk, wp_atk]

def knight_maps():
    """ Returns night attack maps of 64 squares. """
    n_maps = [] 
    n_map_r = [-16+1,-8+2,8+2,16+1]     # Right side knight attack map
    n_map_l = map(lambda x:-x,n_map_r)  # Left side kngiht attack map
    cnt =0
    for sq in range(64):
        rl = map(lambda x: x+sq, n_map_r)
        ll = map(lambda x: x+sq, n_map_l)
        tl = filter(lambda x: x%8 > sq%8 and x >= 0 and x < 64,rl)
        tl += filter(lambda x: x%8 < sq%8 and x >= 0 and x < 64,ll)
        n_maps.append(tl)
        cnt += len(tl)
    print "n map size:",cnt
    return n_maps

class Position:
    """ Position class represents chess position """
    rays = directional_rays()
    p_atk_maps = pawn_attack_maps() 
    n_maps = knight_maps()

    def __init__(self,fen = None):
        if fen == None:
            self.pos = list(
                    "rnbqkbnr"
                    "pppppppp"
                    "        "
                    "        "
                    "        "
                    "        "
                    "PPPPPPPP"
                    "RNBQKBNR"
                    )
            self.crights00=[1, 1]
            self.crights000=[1, 1]
            self.t = 1  # 1:White's turn 0:Black's turn
            self.move_number = 1 # full move number
            self.ep_sq = -1  # en-passant square
            self.occ = [-1, -1, -1] #occupied map
        else:                       
            #initialize with fen
#           self.pos = copy.deepcopy(orig.pos)
#           self.crights00 = orig.crights00[:]
#           self.crights000 = orig.crights000[:]
#           self.t = orig.t
#           self.move_number = orig.move_number
#           self.ep_sq = orig.ep_sq
#           self.occ = [-1, -1, -1]
            fs = fen.split()
            assert len(fs) == 6
            
            self.pos = []
            for c in fs[0]:
                if "12345678".find(c) != -1:
                    for i in range(int(c)):
                        self.pos.append(" ")
                elif "rnbqkpRNBQKP".find(c) != -1:
                    self.pos.append(c)
            assert len(self.pos) == 64
            self.t = 1 if fs[1]=="w" else 0

            self.crights00=[0, 0]
            self.crights000=[0, 0]
            for c in fs[2]:
                if c == "K":
                    self.crights00[Wht]=1
                elif c == "Q":
                    self.crights000[Wht] = 1
                elif c == "k":
                    self.crights00[Blk] = 1
                elif c == "q":
                    self.crights000[Blk] = 1
            
            if len(fs[3])==2:
                self.ep_sq = int(fs[3][1])*8+(ord(fs[3][0])-ord("a"))
            else: 
                self.ep_sq = -1
            self.move_number = int(fs[5])
            self.occ = [-1, -1, -1]


    def __repr__(self):
        st = ""
        for i in range(len(self.pos)):
            st += self.pos[i]+" "
            if i%8==7:
                st += "\n"
        st += repr(self.move_number) + "\n"
        return st

    @staticmethod
    def print_n_maps(sq):
        for i in range(64):
            if i in Position.n_maps[sq]:
                print "X",
            else:
                print "_",
            if i%8 == 7:
                print ""
        print "size:",len(Position.n_maps[sq])

    @staticmethod
    def print_rays(sq):
        rays = Position.rays[sq]
        r = reduce(operator.add,rays)
        for i in range(64):
            if i in r:
                print "X",
            else:
                print "_",
            if i%8 == 7:
                print ""

    @staticmethod
    def print_map(l):
        for i in range(64):
            if l & 1<<i:
                print "X",
            else:
                print "_",
            if i%8==7:
                print ""

    def calc_occ(self):
        if self.occ[0] != -1: return

        self.occ[Blk]=0L
        self.occ[Wht]=0L

        # Calculate occupied map 
        # first assume black's move then swap if it's white's
        for piece in enumerate(self.pos):
            if piece[1].islower():
                self.occ[Blk] |= 1 << piece[0]
            elif piece[1].isupper():
                self.occ[Wht] |= 1 << piece[0]
        return

    def get_moves(self,side):
        """ get all moves """
        mvs = []
        self.calc_occ()
       
        pieces = ["rnbqkp","RNBQKP"]
        all_occ = self.occ[Blk] | self.occ[Wht]
        for p in enumerate(self.pos):
            if p[1] == pieces[side][R]:
                for i in range(0,8,2):  # east,south,west,north
                    for sq in Position.rays[p[0]][i]:
                        if all_occ & 1 << sq == 0:
                            mvs.append((p[0], sq))
                        elif self.occ[side^1] & 1 << sq != 0:
                            mvs.append((p[0], sq))
                            break
                        else:
                            break
            elif p[1] == pieces[side][B]:
                for i in range(1,8,2):  
                    for sq in Position.rays[p[0]][i]:
                        if all_occ & 1 << sq == 0:
                            mvs.append((p[0], sq))
                        elif self.occ[side^1] & 1 << sq != 0:
                            mvs.append((p[0], sq))
                            break
                        else:
                            break
            elif p[1] == pieces[side][Q]:
                for i in range(8):  
                    for sq in Position.rays[p[0]][i]:
                        if all_occ & 1 << sq == 0:
                            mvs.append((p[0], sq))
                        elif self.occ[side^1] & 1 << sq != 0:
                            mvs.append((p[0], sq))
                            break
                        else:
                            break
            elif p[1] == pieces[side][K]:
                for i in range(8):
                    sqs = Position.rays[p[0]][i]
                    if len(sqs)==0:
                        continue
                    sq = sqs[0]
                    if all_occ & 1 << sq == 0:
                        mvs.append((p[0], sq))
                    elif self.occ[side^1] & 1 << sq != 0:
                        mvs.append((p[0], sq))
            elif p[1] == pieces[side][N]:
                for sq in Position.n_maps[p[0]]:
                    if all_occ & 1 << sq == 0:
                        mvs.append((p[0], sq))
                    elif self.occ[side^1] & 1 << sq != 0:
                        mvs.append((p[0], sq))
            elif p[1] == pieces[side][P]:
                dir=-1
                if side==Blk: dir=1;                      # Set pawn move direction.
                dsq = p[0]+8*dir
                if all_occ & 1 << dsq == 0:
                    mvs.append((p[0], dsq))
                    if (p[0]/8 == 1 and side == Blk) or \
                            (p[0]/8 == 6 and side == Wht): # Check if pawn hasn't moved
                        dsq += 8*dir
                        if all_occ & 1 << dsq == 0:
                            mvs.append((p[0], dsq))
                # capture
                for dsq in Position.p_atk_maps[side][p[0]]:
                    if self.occ[side^1] & 1 << dsq != 0 or dsq == self.ep_sq:
                        mvs.append((p[0],dsq))
        return mvs            
    

    def get_legal_moves(self):
        # Get my moves
        mvs = self.get_moves(self.t)

        # Get a attaking map by foe
        foe_mvs = self.get_moves(self.t^1)
        foe_attk = 0L
        for atk in foe_mvs:
            foe_attk |= 1L << atk[1]

        # Add castling moves
        all_occ = self.occ[Blk] | self.occ[Wht]
        king_sqs=[4,60]
        if self.crights00[self.t] \
            and not (all_occ & (1L<<king_sqs[self.t]+1| 
                1L<<king_sqs[self.t]+2)) \
            and not (foe_attk & (1L<<king_sqs[self.t]| 
                1L<<king_sqs[self.t]+1|
                1L<<king_sqs[self.t]+2)):
            mvs.append((king_sqs[self.t],king_sqs[self.t]+2))
        if self.crights000[self.t] \
            and not (all_occ & (1L<<king_sqs[self.t]-1| 
                1L<<king_sqs[self.t]-2| \
                1L<<king_sqs[self.t]-3)) \
            and not (foe_attk & (1L<<king_sqs[self.t]|
                1L<<king_sqs[self.t]-1| 
                1L<<king_sqs[self.t]-2)):
            mvs.append((king_sqs[self.t],king_sqs[self.t]-2))


        # Return only non-self-checking moves
        return filter(self.king_safe_after, mvs)    
    
    # Returns true if the square isn't attacked after given move
    def king_safe_after(self, move):
        np = copy.deepcopy(self)
        np.move(move)

        king_c = "k" if self.t==0 else "K"
        king_sq = "".join(np.pos).find(king_c)
        # check king is in check
        mvs = np.get_moves(np.t)
        for m in mvs:
            if m[1]==king_sq:
                return False
        return True

    # Make a move: caller is responsible for legality.
    # handles promotion, en-passant, capture and castling
    def move(self,mv):
        move_type = ""
        assert mv[0]>=0 and mv[0]<64 \
            and mv[1]>=0 and mv[1]<64
        src = mv[0]
        dst = mv[1]
        src_p = self.pos[src]
        dst_p = self.pos[dst]
        self.pos[dst] = self.pos[src]
        self.pos[src] = " "

        # En passant capture
        if src_p == "p" and dst == self.ep_sq:
            self.pos[dst-8] = " "
            move_type = "epc"
        elif src_p == "P" and dst == self.ep_sq:
            self.pos[dst+8] = " "
            move_type = "EPC"

        # Set enpassant square
        if src_p == "p" and dst-src == 16:
            self.ep_sq = src + 8
        elif src_p == "P" and src-dst == 16:
            self.ep_sq = src - 8
        else:  # Clear enpassant square
            self.ep_sq = -1    

        # Move rooks if castling
        if src_p == "k" and src==4 and dst == 2:
            self.pos[0]=" "
            self.pos[3]="r"
            move_type = "ooo"
            self.crights000[Blk] = False
        elif src_p == "k" and src ==4 and dst == 6:
            self.pos[7] = " "
            self.pos[5] = "r"
            move_type = "oo"
            self.crights00[Blk] = False
        elif src_p == "K" and src==60 and dst == 58:
            self.pos[56] = " "
            self.pos[59] = "R"
            move_type = "OOO"
            self.crights000[Wht] = False
        elif src_p == "K" and src==60 and dst == 62:
            self.pos[63] = " "
            self.pos[61] = "R"
            move_type = "OO"
            self.crights00[Wht] = False

        # If king or rook moves void castling rights
        if src_p == "k":
            self.crights000[Blk] = False
            self.crights00[Blk] = False
        elif src_p == "K":
            self.crights000[Wht] = False
            self.crights00[Wht] = False
        if  src_p == "r" and src == 0 and self.crights000[Blk]:
            self.crights000[Blk] = False
        elif src_p == "r" and src == 7 and self.crights00[Blk]:
            self.crights00[Blk] = False
        if  src_p == "R" and src == 56 and self.crights000[Wht]:
            self.crights000[Wht] = False
        elif src_p == "R" and src == 63 and self.crights00[Wht]:
            self.crights00[Wht] = False

        # Promotion
        if (src_p == "p" and dst//8 == 7) or \
                (src_p == "P" and dst//8 == 0) :
            try:
                self.pos[dst] = self.on_get_promotion(src_p == "P")
            except AttributeError:
                self.pos[dst] = "q"
                if src_p == "P": self.pos[dst] = "Q"
            move_type = "="+self.pos[dst]

        if self.t==Blk:
            self.move_number += 1
        self.t ^= 1                 # Toggle color
        self.occ[0] = -1            # Invalidate occupied maps

#       print self
        return move_type

class Node:
    def __init__(self, pos = None):
        self.pos = pos
        return

class Chess:
    """ Manages Position """
    def __init__(self):
        self.nodes = []
        self.idx=-1
        return

    # Initialize data as default chess model
    def setup(self,fen = None):
        del self.nodes[:]
        self.idx = 0

        p = Position(fen)
        self.nodes.append(Node(p))

        try:
            self.on_setup(p.pos)
        except AttributeError:
            pass
        return

    def get_position(self):
        return self.nodes[self.idx].pos

    def first(self):
        if self.idx > 0:
            self.idx = 0
            try:
                self.on_nav(self.nodes[self.idx].pos.pos)
            except AttributeError:
                pass
        return

    def last(self):
        if self.idx > 0:
            self.idx = len(self.nodes)-1
            try:
                self.on_nav(self.nodes[self.idx].pos.pos)
            except AttributeError:
                pass
        return

    def prev(self):
        print "prev button"
        if self.idx > 0:
            self.idx -= 1
            try:
                self.on_nav(self.nodes[self.idx].pos.pos)
            except AttributeError:
                pass
        return

    def next(self):
        if self.idx < len(self.nodes)-1:
            self.idx += 1
            try:
                self.on_nav(self.nodes[self.idx].pos.pos)
            except AttributeError:
                pass
        return

    def make(self, move):
        pos = self.nodes[self.idx].pos
        legal_moves = pos.get_legal_moves()
        for m in legal_moves:
            if m[0] == move[0] and m[1] == move[1]:
                p2 = copy.deepcopy(pos)
                move_type = p2.move(m)
                
                # Truncate moves
                while len(self.nodes) > self.idx+1:
                    del self.nodes[-1]

                self.nodes.append(Node(p2))
                self.idx += 1

                try:
                    self.on_make(m, move_type)
                except AttributeError:
                    pass
                return True
        return False

# Test unit
def print_coords():
    for i in range(64):
        print "%02d" %i,
        if i%8==7:
            print ""


if __name__ == "__main__":
    p = Position()
    mvs = p.get_legal_moves()

    c=""
    print p
    print_coords()
    while c != "quit":
        print mvs
        c = raw_input(">>")
        s = c.split()
        p.move((int(s[0]),int(s[1])))
        print p.get_legal_moves()
        print p
        print_coords()

