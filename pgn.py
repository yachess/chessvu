import re
import exceptions
from node import Node

#REG_MOVE = "[RNBQK]?[a-h]?[1-8]?x?[a-h][1-8]=?[RNBQK]?|O-O|O-O-O"


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

class PGN_File(object):
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
                    if lm[0] == src and lm[1] == dst:
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
                    if lm[0] == src and lm[1] == dst:
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
                for lm in lmoves:
                    if lm[1]==dst and pos.pos[lm[0]]==piece:
                        if len(tk)>=3:
                            # Compare source square
                            if src_file != -1:
                                if (lm[0]%8) != src_file:
                                    continue
                            elif src_rank != -1:
                                if 8-lm[0]//8 != src_rank:
                                    continue
                        if promotion != "":
                            lm.append(promotion)
                        model.make(lm)
                        handled = True
                        break
                if not handled:
                    raise PGN_Exception(1, "PGN Error: #"+str(half_move)+" "+tk+" piece:" + \
                            str(piece) + " side:" +str(pos.t))
                    break
#       model.idx = 0
        self.g_idx = idx
