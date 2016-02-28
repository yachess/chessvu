import os
import re
import chess
import board

board.tsize = 35

def parse_moves(body):
    move_ptrn = "((([RNBQK]([a-h]|[1-8]|)|[a-h])(x|)|)[a-h][1-8])"
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
model.on_nav = app.setup

# Read PGN file
games = []
dic = {}
reading_body = False
f = open("round13.pgn")

for line in f:
    tags = re.match("^\[(.*)\"(.*)\"\]",line)
    if line == "" or line == "\n":
        continue
    if tags:
        if reading_body:
            print "Event=",dic["Event"]
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
model.setup("rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
app.mainloop()
