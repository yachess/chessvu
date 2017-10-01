# Chess
# implements traditional chess
# also supports basic PGN encoding and decoding

import re
import exceptions

import os
import copy
import traceback

from node import Node

# Constants
BLK=0
WHT=1

# Chess pieces
PIECES = ["rnbqkp","RNBQKP"]
R = 0
N = 1
B = 2
Q = 3
K = 4
P = 5

# Castling rights masks used in Position.info (Future)
CASTLE_BQ = 1 << 0
CASTLE_BK = 1 << 1
CASTLE_WQ = 1 << 2
CASTLE_WK = 1 << 3
REQ_UPDATE = 1 << 4  # set if update if needed

# Move info masks used in Move.info
MASK_TURN = 1 << 0      # set if it is white's turn
MASK_P = 1 << 1
MASK_N = 1 << 2
MASK_B = 1 << 3
MASK_R = 1 << 4
MASK_Q = 1 << 5
MASK_K = 1 << 6
MASK_EP = 1 << 7
MASK_CAPTURE_P = 1 << 8
MASK_CAPTURE_N = 1 << 9
MASK_CAPTURE_B = 1 << 10
MASK_CAPTURE_R = 1 << 11
MASK_CAPTURE_Q = 1 << 12
MASK_CAPTURE_K = 1 << 13
MASK_CAPTURE = MASK_CAPTURE_P | MASK_CAPTURE_N | \
        MASK_CAPTURE_B | MASK_CAPTURE_R | \
        MASK_CAPTURE_Q | MASK_CAPTURE_K
MASK_CASTLE_SHORT = 1 << 14
MASK_CASTLE_LONG = 1 << 15
MASK_CASTLE = MASK_CASTLE_SHORT | MASK_CASTLE_LONG
MASK_PROMOTE_N = 1 << 16
MASK_PROMOTE_B = 1 << 17
MASK_PROMOTE_R = 1 << 18
MASK_PROMOTE_Q = 1 << 19
MASK_PROMOTE = MASK_PROMOTE_N | MASK_PROMOTE_B | \
        MASK_PROMOTE_R | MASK_PROMOTE_Q
MASK_EN_PASSANT = 1 << 20
MASK_CHECKING = 1 << 21
MASK_CHECKMATING = 1 <<22

MASK_FROM_USER = 1 << 23

# Methods to build commonly used maps
def directional_rays():
    """ build directional rays corresponding to each square  """
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

def pawn_attack_maps():
    """ build pawn attack maps.  """
    bp_atk = [[] for _ in range(64)]
    for sq in range(8, 64-8):
        if sq%8 != 0:
            bp_atk[sq].append(sq + 7)
        if sq%8 != 7:
            bp_atk[sq].append(sq + 9)
    # Map for white is created by rotating black's
    wp_atk=[]
    for i in bp_atk:
        wp_atk.append(map(lambda x:63-x, i))
    wp_atk.reverse()
    return [bp_atk, wp_atk]

def knight_maps():
    """ Knight attack maps. """
    n_maps = [] 
    n_map_r = [-15, -6, 10, 17]     # Right side knight attack map
    n_map_l = map(lambda x: -x, n_map_r)  # Left side kngiht attack map
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

INIT_FEN= "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
#REG_MOVE = "((([RNBQK]([a-h]|[1-8]|)|[a-h])(x|)|)[a-h][1-8]|O-O-O|O-O)"
REG_MOVE = "([RNBQK]([a-h]|[1-8]|)|[a-h])(x|)|[a-h][1-8]|=[RNBQ]"
REG_COMMENT = "\{[^\}]+\}"
REG_TAG = "^\[(.*)\"(.*)\"\]"

class PGN_Exception(exceptions.Exception):
    def __init__(self,errno,msg):
        self.args = (errno,msg)
        self.errno = errno
        self.errmsg = msg

class PGN(object):
    def __init__(self, filename):
        self.f = open(filename)
        # Read PGN file
        # self.games is list of dictionaries which can be retrieved by tag as keys
        # body can be retrieved by "_body_" tag.
        self.games = []
        self.g_idx = 0

        dic = {}
        reading_body = False
        for line in self.f:
            line = line.strip()
            if line == "" or line == "\n":
                continue

            tags = re.match(REG_TAG,line)
            if tags:
                if reading_body:
#                   print "body=",dic["_body_"]
                    self.games.append(dic)
                    dic = {}
                    reading_body = False
                dic[tags.groups()[0].strip()] = tags.groups()[1].strip()
            else:
                try:
                    dic["_body_"] += line.rstrip() + " "
                except KeyError:
                    dic["_body_"] = line.rstrip() + " "
                reading_body = True
        self.games.append(dic)
        dic = {}

    def title(self):
        white = "?"
        black = "?"
        if "White" in self.games[self.g_idx]:
            white = self.games[self.g_idx]["White"]
        if "Black" in self.games[self.g_idx]:
            black = self.games[self.g_idx]["Black"]

        return  "game #"+str(self.g_idx+1)+": "+ \
            white + " - " + black
    

    @staticmethod
    def parse_tokens(body):
        tokens = []
        tk = ""
        reading_cmt = False
        for c in body:
            if c == "{" and not reading_cmt:
                reading_cmt = True
                tk = ""
            elif c == "}" and reading_cmt:
                reading_cmt = False
                tk += c
                tokens.append(tk)
                tk = ""

            if not reading_cmt:
                if "\n\t\r. ".find(c) != -1:
                    if tk != "":
                        tokens.append( tk )
                        tk = ""
                    continue
                elif "()".find(c) != -1:
                    tokens.append( c )
                    tk = ""
                else:
                    tk += c
            else:
                tk += c
        if tk != "":
            tokens.append( c )
        return tokens

    def read_into_model(self, idx, model):
        if idx < 0 or idx >= len(self.games):
            return
        
        try: 
            fen = self.games[idx]["FEN"]
        except KeyError:
            fen = INIT_FEN
        body = self.games[idx]["_body_"]

        model.setup(fen)
        tokens = self.parse_tokens(body)

        half_move = 0
        regex = re.compile(REG_MOVE)
        branches = []
        for tk in tokens:
            print tk
            half_move += 1
            src = -1
            dst = -1
            pos = model.get_position()
            lmoves = pos.get_legal_moves()
            
            if tk == "(":
                branches.append(Node.cur_node)
                Node.go_prev()
            elif tk == ")":
                Node.cur_node = branches.pop()
            elif tk == "O-O-O":
                legal = False
                if pos.t == 0:
                    src = 4
                    dst = 2
                else:
                    src = 60
                    dst = 58
                for lm in lmoves:
                    if lm.src == src and lm.dst == dst:
                        model.make(lm)
                        legal = True             
                if legal: 
                    continue
                else:
                    for tk in lmoves: print tk
                    print model.nodes[model.idx].pos.crights000[0]
                    raise PGN_Exception(1, "Wrong castling at #"+str(half_move))
            elif tk == "O-O":
                legal = False
                if pos.t == 0:
                    src = 4
                    dst = 6
                else:
                    src = 60
                    dst = 62
                for lm in lmoves:
                    if lm.src == src and lm.dst == dst:
                        model.make(lm)
                        legal = True
                if legal:
                    continue
                else:
                    for tk in lmoves: print tk
                    raise PGN_Exception(1, "Wrong castling at #"+str(half_move))
            elif tk[0] == "{":
                Node.cur_node.data.last_move.comment = tk
            elif regex.match(tk):
                piece = "P"
                promotion = ""

                # remove +,# at the end of move
                tk = tk.rstrip("+-#!?")

                # Get promotion piece
                eqp = tk.find("=")
                if eqp != -1:
                    promotion = tk[eqp+1]
                    tk = tk[0:eqp]
                # Now handle body part
                if "RNBQK".find(tk[0]) != -1:
                    piece = tk[0]
                    tk=tk[1:]

                # get source file for pawn move
                src_file = -1
                src_rank = -1
#   if piece == "P":
                if len(tk)>2:
                    if "abcdefgh".find(tk[0]) != -1:
                        src_file = ord(tk[0])-ord("a")
                    elif "12345678".find(tk[0]) != -1:
                        src_rank = int(tk[0])

                if pos.t==0:
                    piece = piece.lower()

                sq= tk[-2:]
                dst = (8-int(sq[1]))*8+ord(sq[0])-ord("a")  

                handled = False
                print "legal move size="+str(len(lmoves))
                for lm in lmoves:
                    if lm.dst==dst and pos.pos[lm.src]==piece:
                        if len(tk)>=3:
                            # Compare source square
                            if src_file != -1:
                                if (lm.src%8) != src_file:
                                    continue
                            elif src_rank != -1:
                                if 8-lm.src//8 != src_rank:
                                    continue
                        if promotion != "":
                            lm.set_promotion_piece(promotion)
                        model.make(lm)
                        handled = True
                        break
                if not handled:
                    raise PGN_Exception(1, "PGN Error: #"+str(half_move)+" "+tk+" piece:" + \
                            str(piece) + " side:" +str(pos.t))
                    break
#       model.idx = 0
        self.g_idx = idx

#PGN encode 
    lvl = 0
    new_context = True

    @staticmethod
    def init_encode():
        lvl = 0
        new_context = True

    @staticmethod
    def encode_node(node):
        if node == None:
            return ""
        s = ""
        for i,v in enumerate(node.childs, 1):
            if i != 1:
                s += "("
                PGN.new_context = True
                PGN.lvl += 1
            if PGN.new_context or v.data.last_move.is_white(): 
                s += str(v.data.last_move.number)
                s += ". " if v.data.last_move.is_white() else "... "
            s += v.data.last_move.pgn
            if len(v.childs) > 0:           # last move doesn't need space
                s += " "
            PGN.new_context = False
        for n in reversed(node.childs):
            s += PGN.encode_node(n)
        if len(node.childs) == 0:
            if PGN.lvl > 0 :
                s += ") "
            PGN.new_context = True
            PGN.lvl -= 1
        return s


class Move:
    """ Extended move class. simple move is presented as (src,dst) 
        Move class has all the information needed from outer world, which is 
        1. number (full move)
        2. color (B/W)
        3. source square
        4. destination square
        5. PGN Notation (either it is built or not)
        6. En Passant,Capture,Promotion,Check,Checkmate status (info field)
    """

    def __init__(self, src_sq, dst_sq):
        self.number = 0
        self.src = src_sq
        self.dst = dst_sq
        self.pgn = ""
        self.info = 0L
        self.comment = ""
        pass
    
    def set_turn(self, is_white):
        if is_white:
            self.info |= MASK_TURN
        else:
            self.info &= ~MASK_TURN

    def set_captured_piece(self,cap_piece):
        if cap_piece == 'P':
            self.info |= MASK_CAPTURE_P
        elif cap_piece == 'N':
            self.info |= MASK_CAPTURE_N
        elif cap_piece == 'B':
            self.info |= MASK_CAPTURE_B
        elif cap_piece == 'R':
            self.info |= MASK_CAPTURE_R
        elif cap_piece == 'Q':
            self.info |= MASK_CAPTURE_Q
        elif cap_piece == 'K':
            self.info |= MASK_CAPTURE_K
        else:
            pass
            #print "wrong capture:"+str(self.src)+"-"+str(self.dst)+":"+cap_piece
            #traceback.print_exc(file=sys.stdout)

    def get_captured_piece(self):
        if self.info & MASK_CAPTURE_P:
            return 'P'
        elif self.info & MASK_CAPTURE_N:
            return 'N'
        elif self.info & MASK_CAPTURE_B:
            return 'B'
        elif self.info & MASK_CAPTURE_R:
            return 'R'
        elif self.info & MASK_CAPTURE_Q:
            return 'Q'
        elif self.info & MASK_CAPTURE_K:
            return 'K'
        else:
            pass

    def set_castling(self,is_short):
        if is_short:
            self.info |= MASK_CASTLE_SHORT
        else:
            self.info |= MASK_CASTLE_LONG

    def set_promotion_piece(self,pc):
        if pc == 'N':
            self.info |= MASK_PROMOTE_N
        elif pc == 'B':
            self.info |= MASK_PROMOTE_B
        elif pc == 'R':
            self.info |= MASK_PROMOTE_R
        elif pc == 'Q':
            self.info |= MASK_PROMOTE_Q

    def get_promotion_piece(self):
        if self.info & MASK_PROMOTE_N != 0:
            return 'N'
        elif self.info & MASK_PROMOTE_B != 0:
            return 'B'
        elif self.info & MASK_PROMOTE_R != 0:
            return 'R'
        elif self.info & MASK_PROMOTE_Q != 0:
            return 'Q'
        print "wrong promotion piece"
        return None

    def set_en_passant(self):
        self.info |= MASK_EN_PASSANT
        #self.info |= MASK_CAPTURE_P

    def set_checking(self):
        self.info |= MASK_CHECKING

    def set_checkmating(self):
        self.info |= MASK_CHECKMATING    
    
    def set_from_user(self):
        self.info |= MASK_FROM_USER
    def is_from_user(self):
        return (self.info & MASK_FROM_USER)

    def is_white(self):
        return (self.info & MASK_TURN)

    def is_capture(self):
        return (self.info & MASK_CAPTURE != 0)

    def is_en_passant(self):
        return (self.info & MASK_EN_PASSANT != 0)

    def is_promotion(self):
        return (self.info & MASK_PROMOTE != 0)

    def is_castling_short(self):
        return (self.info & MASK_CASTLE_SHORT != 0)

    def is_castling_long(self):
        return (self.info & MASK_CASTLE_LONG != 0)
    def is_checking(self):

        return (self.info & MASK_CHECKING)
    def is_checkmating(self):
        return (self.info & MASK_CHECKMATING)

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
            self.last_move = None
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
                    self.crights00[WHT] = 1
                elif c == "Q":
                    self.crights000[WHT] = 1
                elif c == "k":
                    self.crights00[BLK] = 1
                elif c == "q":
                    self.crights000[BLK] = 1
            
            if len(fs[3])==2:
                self.ep_sq = int(fs[3][1])*8+(ord(fs[3][0])-ord("a"))
            else: 
                self.ep_sq = -1
            self.move_number = int(fs[5])
            self.occ = [-1, -1, -1]
            self.last_move = None

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

    def get_legal_moves(self):
        # Get my moves
        mvs = self._get_moves(self.t)

        # Get a attaking map by foe
        foe_mvs = self._get_moves(self.t^1)
        foe_attk = 0L
        for atk in foe_mvs:
            foe_attk |= 1L << atk.dst

        # Add castling moves
        all_occ = self.occ[BLK] | self.occ[WHT]
        king_sqs=[4,60]
        if self.crights00[self.t] \
            and not (all_occ & (1L<<king_sqs[self.t]+1| 
                1L<<king_sqs[self.t]+2)) \
            and not (foe_attk & (1L<<king_sqs[self.t]| 
                1L<<king_sqs[self.t]+1|
                1L<<king_sqs[self.t]+2)):
            mvs.append(Move(king_sqs[self.t],king_sqs[self.t]+2))
        if self.crights000[self.t] \
            and not (all_occ & (1L<<king_sqs[self.t]-1| 
                1L<<king_sqs[self.t]-2| \
                1L<<king_sqs[self.t]-3)) \
            and not (foe_attk & (1L<<king_sqs[self.t]|
                1L<<king_sqs[self.t]-1| 
                1L<<king_sqs[self.t]-2)):
            mvs.append(Move(king_sqs[self.t],king_sqs[self.t]-2))

        # Return only non-self-checking moves
        return filter(self.king_safe_after, mvs)    
    
    # Returns true if the square isn't attacked after given move
    def king_safe_after(self, mv):
        new_p = copy.deepcopy(self)
        #turn off pgn encoding temproarily.
        new_p.move(mv)
        
        # check if king is in check in new position
        king_c = "k" if self.t==0 else "K"
        king_sq = "".join(new_p.pos).find(king_c)
        mvs = new_p._get_moves(new_p.t)
        for m in mvs:
            if m.dst == king_sq:
                return False
        return True


    def move(self,mv):
        """  Make a move: caller is responsible for checking legality.
        handles promotion, en-passant, capture and castling and pgn encoding """

        assert mv.src>=0 and mv.src<64 \
            and mv.dst>=0 and mv.dst<64
        src = mv.src
        dst = mv.dst
        src_p = self.pos[src]
        dst_p = self.pos[dst]
        self.pos[dst] = self.pos[src]
        self.pos[src] = " "

#       move = Move(src,dst)
        mv.number = self.move_number
#       print "move:"+str(src) + "-" + str(dst)

        if src_p.islower():
            mv.set_turn(False)  #  0 is black 1 is white
        else:
            mv.set_turn(True)

        # En passant capture
        if src_p == "p" and dst == self.ep_sq:
            self.pos[dst-8] = " "
            mv.set_en_passant()
        elif src_p == "P" and dst == self.ep_sq:
            self.pos[dst+8] = " "
            mv.set_en_passant()
        elif dst_p != ' ':
            mv.set_captured_piece(dst_p.upper())

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
            mv.set_castling(False)  # false: long castling  true: short castling
            self.crights000[BLK] = False
        elif src_p == "k" and src ==4 and dst == 6:
            self.pos[7] = " "
            self.pos[5] = "r"
            mv.set_castling(True)
            self.crights00[BLK] = False
        elif src_p == "K" and src==60 and dst == 58:
            self.pos[56] = " "
            self.pos[59] = "R"
            mv.set_castling(False)
            self.crights000[WHT] = False
        elif src_p == "K" and src==60 and dst == 62:
            self.pos[63] = " "
            self.pos[61] = "R"
            mv.set_castling(True)
            self.crights00[WHT] = False

        # If king or rook moves void castling rights
        if src_p == "k":
            self.crights000[BLK] = False
            self.crights00[BLK] = False
        elif src_p == "K":
            self.crights000[WHT] = False
            self.crights00[WHT] = False
        if  src_p == "r" and src == 0 and self.crights000[BLK]:
            self.crights000[BLK] = False
        elif src_p == "r" and src == 7 and self.crights00[BLK]:
            self.crights00[BLK] = False
        if  src_p == "R" and src == 56 and self.crights000[WHT]:
            self.crights000[WHT] = False
        elif src_p == "R" and src == 63 and self.crights00[WHT]:
            self.crights00[WHT] = False

        # Promotion
        if (src_p == "p" and dst//8 == 7) or \
                (src_p == "P" and dst//8 == 0) :
            if mv.is_from_user():
                self.pos[dst] = "q"
                if src_p == "P": self.pos[dst] = "Q"
           # mv.set_promotion_piece(self.pos[dst].upper())
            else:
                if mv.is_promotion():
                    self.pos[dst] = mv.get_promotion_piece()
                if src_p == "P": 
                    self.pos[dst] = self.pos[dst].upper()
                else:
                    self.pos[dst] = self.pos[dst].lower()
#          #     self.pos[dst] = self.on_ask_promotion(src_p == "P")
            mv.set_promotion_piece(self.pos[dst].upper())
        if self.t==BLK:
            self.move_number += 1
        self.t ^= 1                 # Toggle color
        self.occ[0] = -1            # Invalidate occupied maps to recalculate

        return mv

    def _get_moves(self,side):
        """ get all moves of side regardless of checked king"""
        mvs = []

        # calculate occupied map """
        if self.occ[0] == -1:
            self.occ[BLK]=0L
            self.occ[WHT]=0L
            # first assume black's move then swap if it's white's
            for piece in enumerate(self.pos):
                if piece[1] in "rnbqkp":
                    self.occ[BLK] |= 1 << piece[0]
                elif piece[1] in "RNBQKP":
                    self.occ[WHT] |= 1 << piece[0]
       
        all_occ = self.occ[BLK] | self.occ[WHT]
        for p in enumerate(self.pos):
            if p[1] == PIECES[side][R]:
                for i in range(0,8,2):  # east,south,west,north
                    for sq in Position.rays[p[0]][i]:
                        if all_occ & 1 << sq == 0:
                            mvs.append(Move(p[0], sq))
                        elif self.occ[side^1] & 1 << sq != 0:
                            mvs.append(Move(p[0], sq))
                            break
                        else:
                            break
            elif p[1] == PIECES[side][B]:
                for i in range(1,8,2):  
                    for sq in Position.rays[p[0]][i]:
                        if all_occ & 1 << sq == 0:
                            mvs.append(Move(p[0], sq))
                        elif self.occ[side^1] & 1 << sq != 0:
                            mvs.append(Move(p[0], sq))
                            break
                        else:
                            break
            elif p[1] == PIECES[side][Q]:
                for i in range(8):  
                    for sq in Position.rays[p[0]][i]:
                        if all_occ & 1 << sq == 0:
                            mvs.append(Move(p[0], sq))
                        elif self.occ[side^1] & 1 << sq != 0:
                            mvs.append(Move(p[0], sq))
                            break
                        else:
                            break
            elif p[1] == PIECES[side][K]:
                for i in range(8):
                    sqs = Position.rays[p[0]][i]
                    if len(sqs)==0:
                        continue
                    sq = sqs[0]
                    if all_occ & 1 << sq == 0:
                        mvs.append(Move(p[0], sq))
                    elif self.occ[side^1] & 1 << sq != 0:
                        mvs.append(Move(p[0], sq))
            elif p[1] == PIECES[side][N]:
                for sq in Position.n_maps[p[0]]:
                    if all_occ & 1 << sq == 0:
                        mvs.append(Move(p[0], sq))
                    elif self.occ[side^1] & 1 << sq != 0:
                        mvs.append(Move(p[0], sq))
            elif p[1] == PIECES[side][P]:
                dir = 1 if side == BLK else -1  # pawn move direction
                dsq = p[0] + 8 * dir
                if all_occ & 1 << dsq == 0:
                    mvs.append(Move(p[0], dsq))
                    if (p[0]/8 == 1 and side == BLK) or \
                            (p[0]/8 == 6 and side == WHT): # Check if pawn hasn't moved
                        dsq += 8*dir
                        if all_occ & 1 << dsq == 0:
                            mvs.append(Move(p[0], dsq))
                # capture
                for dsq in Position.p_atk_maps[side][p[0]]:
                    if self.occ[side^1] & 1 << dsq != 0 or dsq == self.ep_sq:
                        mvs.append(Move(p[0],dsq))
        return mvs            
    

class Chess:
    """ Manages tree of positions """
    def __init__(self):
#       self.nodes = []
#       self.idx= -1
        Node.clear()
        return

    # Initialize data as default chess model
    def setup(self,fen = None):
#       del self.nodes[:]
#       self.idx = 0

        Node.clear()

        p = Position(fen)
        Node.append(Node(p))
#       self.nodes.append(Node(p))

        try:
            self.on_setup(p.pos)
        except AttributeError:
            pass
        return

    def get_position(self):
#       return self.nodes[self.idx].pos
        return Node.cur_node.data

    def first(self):
        while Node.cur_node.parent != None:
            n = Node.cur_node
            Node.go_prev()
            try: 
                self.on_unmake(n.data.last_move)
            except AttributeError:
                pass
    
    def last(self):
        while len(Node.cur_node.childs) != 0:
            Node.go_next()
            try: 
                self.on_make(Node.cur_node.data.last_move)
            except AttributeError:
                pass

    def prev(self):
        if Node.cur_node.parent == None:
            return
        n = Node.cur_node
        Node.go_prev()
        try: 
            self.on_unmake(n.data.last_move)
        except AttributeError:
            pass

    def next(self):
        if len(Node.cur_node.childs)==0:
            return
        Node.go_next()
        try: 
            self.on_make(Node.cur_node.data.last_move)
        except AttributeError:
            pass

    def make(self, move):
        

        pos = Node.cur_node.data #self.nodes[self.idx].pos

        legal_moves = pos.get_legal_moves()
        for m in legal_moves:
            if m.src == move.src and m.dst == move.dst:
                next_position = copy.deepcopy(pos)
                last_move = next_position.move(move)

                encode_pgn(pos,legal_moves,next_position,last_move)    
                # Truncate moves
#               while len(self.nodes) > self.idx+1:
#                   del self.nodes[-1]

                next_position.last_move = last_move
                 
                Node.append(Node(next_position))
#               self.idx += 1

                try:
                    self.on_make(last_move)
                except AttributeError:
                    pass
                return True
        return False

def encode_pgn(pos,lmvs,new_pos,move):
    # encode pgn 
    src_p = pos.pos[move.src]
    dst_p = pos.pos[move.dst]

    src_written = False
    move.pgn = ""
    if move.is_castling_short():
        move.pgn = "O-O"
    elif move.is_castling_long():
        move.pgn = "O-O-O"
    else:
        is_pawn_move = src_p.upper() == 'P'
        is_capture = move.is_capture()
        sqr_conflict = False
        if is_pawn_move and  is_capture:
            move.pgn += chr(ord('a')+ (move.src % 8))
            src_written = True
        elif not is_pawn_move:
            move.pgn += src_p.upper()
        #check if source square is ambiguos
        if not src_written:
            for mv in lmvs:
                if mv.dst == move.dst:
                    if mv.src == move.src: # desregard same move
                        continue
                    elif pos.pos[mv.src] == src_p:
                        if (move.src % 8 == mv.src % 8): # file is same
                            move.pgn += str(8-move.src // 8)
                        else:
                            move.pgn += chr(ord('a') + (move.src % 8))
                        break
        if is_capture:
            move.pgn += 'x'

        #dest sq
        move.pgn += chr(ord('a') + (move.dst % 8))
        move.pgn += str(8 - move.dst // 8)

        #if promotion add promotion notation
        if move.is_promotion():
            move.pgn += '='
            move.pgn += move.get_promotion_piece()
    #if check add check notation
#   if new_pos.king_in_check(0 if pos.t == 1 else 1 ): 
                
    #check if opponent king is to be checked
    attk = 0L  # attack map
    check = False
    t = 1 if move.is_white() else 0
    mvs = new_pos._get_moves(t)
    for m in mvs:
        attk |= 1 << m.dst
    op_king_sq = "".join(new_pos.pos).find("K" if t==0 else "k")
    
    #find if opponent king is checked or checkmated
    if op_king_sq != -1 and attk & 1 << op_king_sq:
        foe_mvs = new_pos.get_legal_moves()
        if len(foe_mvs) == 0:
            move.set_checkmating()
            move.pgn += '#'
        else:
            move.set_checking()
            move.pgn += '+'
       



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

