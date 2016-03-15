import re
move_ptrn = "((([RNBQK]([a-h]|[1-8]|)|[a-h])(x|)|)[a-h][1-8]|O-O-O|O-O)"
comment_ptrn = "\{[^\}]+\}"
IPOS_FEN= "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkg _ 0 1"

class PGN_File(object):
    
    def __init__(self, filename):
        self.f = open(filename)
        # Read PGN file
        self.games = []
        dic = {}
        reading_body = False
        for line in self.f:
            line = line.strip()
            if line == "" or line == "\n":
                continue

            tags = re.match("^\[(.*)\"(.*)\"\]",line)
            if tags:
                if reading_body:
                    print "body=",dic["_body_"]
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

    def parse_moves(self,body):
        r = re.compile(move_ptrn)
        return r.findall(body) 

    def read_into_model(self, idx, model):
        if idx < 0 or idx >= len(self.games):
            return
        try: 
            fen = self.games[idx]["FEN"]
        except KeyError:
            fen = IPOS_FEN
        body = self.games[idx]["_body_"]

        model.setup(fen)

        moves = self.parse_moves(body)
        for mv in moves:
#   print "handling "+mv[0]
            src = -1
            dst = -1
            pos = model.get_position()

            m = mv[0]
            # handle castling
            if m == "O-O-O":
                if pos.t == 0:
                    src = 4
                    dst = 2
                else:
                    src = 60
                    dst = 58
                model.make((src,dst))
                continue
            elif m == "O-O":
                if pos.t==0:
                    src = 4
                    dst = 6
                else:
                    src = 60
                    dst = 62
                model.make((src,dst))
                continue
            piece = "P"
            promotion = ""

            # Get promotion piece
            eqp = m.find("=")
            if eqp != -1:
                promotion = m[eqp+1]
                m = m[0:eqp]
            # Now handle body part
            if "RNBQK".find(m[0]) != -1:
                piece = m[0]
                m=m[1:]

            # get source file for pawn move
            src_file = -1
            src_rank = -1
#   if piece == "P":
            if len(m)>2:
                if "abcdefgh".find(m[0]) != -1:
                    src_file = ord(m[0])-ord("a")
                elif "12345678".find(m[0]) != -1:
                    src_rank = int(m[0])

            if pos.t==0:
                piece = piece.lower()
            sq= m[-2:]
            dst = (8-int(sq[1]))*8+ord(sq[0])-ord("a")  
            lmoves = pos.get_legal_moves()
            handled = False
            for lm in lmoves:
                if lm[1]==dst and pos.pos[lm[0]]==piece:
                    if len(m)>=3:
                        # Compare source square
                        if src_file != -1:
                            if (lm[0]%8) != src_file:
                                continue
                        elif src_rank != -1:
                            if 8-lm[0]//8 != src_rank:
                                continue
                    model.make(lm)
#           print "handled: "+m+" supposed dst: "+ str(dst)+" piece:" + str(piece)
                    handled = True
                    break
            if not handled:
                print "not handled: "+m+" piece:" + str(piece) + " side:" +str(pos.t)
                break

