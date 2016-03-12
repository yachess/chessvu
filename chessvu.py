import os
import re
import chess
import board

board.tsize = 45

def parse_moves(body):
    move_ptrn = "((([RNBQK]([a-h]|[1-8]|)|[a-h])(x|)|)[a-h][1-8]|O-O-O|O-O)"
    comment_ptrn = "\{[^\}]+\}"
    r = re.compile(move_ptrn)
    return r.findall(body) 

# Create View and Model
app = board.App()
model = chess.Chess()

# Bind event handlers
app.on_move_piece  = model.make
model.on_get_promotion = app.get_promotion
model.on_setup = app.setup
model.on_make = app.handle_make
app.on_prev_btn = model.prev
app.on_next_btn = model.next
app.on_first_btn = model.first
app.on_last_btn = model.last
model.on_nav = app.setup

# Read PGN file
games = []
dic = {}
reading_body = False
f = open("1001bwtc.pgn")
#f = open("art_of_attack.pgn")

for line in f:
    line = line.strip()
    if line == "" or line == "\n":
        continue

    tags = re.match("^\[(.*)\"(.*)\"\]",line)
    if tags:
        if reading_body:
            print "body=",dic["_body_"]
            games.append(dic)
            dic = {}
            reading_body = False
        dic[tags.groups()[0].strip()] = tags.groups()[1].strip()
    else:
        try:
            dic["_body_"] += line.rstrip() + " "
        except KeyError:
            dic["_body_"] = line.rstrip() + " "
        reading_body = True

# Strip comments and variations

print len(dic)," games read"

# setup board
#app.flip = True

try: 
    fen = games[500]["FEN"]
except KeyError:
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkg _ 0 1"

body = games[500]["_body_"]


model.setup(fen)
moves = parse_moves(body)
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
#   model.make((src,dst))
app.mainloop()
