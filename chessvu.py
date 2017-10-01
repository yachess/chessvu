import os
import re
import chess
import board
from node import Node
from chess import PGN

board.sq_size = 72

#game index in pgn file  -1 means it is not from pgn file

def read_prev():
    global  model, pf, app
    if pf.g_idx <=0:
        return
    pf.read_into_model(pf.g_idx-1, model)
    model.first()
    app.setup(Node.cur_node.data)
    app.master.title(pf.title())

def read_next():
    global model, pf,app
    if pf.g_idx > len(pf.games):
        return
    pf.read_into_model(pf.g_idx+1, model)
    model.first()    
    app.setup(Node.cur_node.data)
    app.master.title(pf.title())

def open_pgn(filename):
    global pf,model,app
    pf = PGN(filename)
    pf.read_into_model(0, model)
    model.first()
    app.setup(Node.cur_node.data)
    app.master.title(pf.title())

def leftkey(e):
    ctrl = (e.state & 0x4) != 0
    if ctrl:
        read_prev()
    else:
        model.prev()

def rightkey(e):
    ctrl = (e.state & 0x4) != 0
    if ctrl:
        read_next()
    else:
        model.next()

def rotatekey(e):
    ctrl = (e.state & 0x4) != 0
    if ctrl:
        app.rotate_board()

# Create View and Model
app = board.App()
#app.setup("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

model = chess.Chess()

# Wire event handlers

# handle from input from interface. model will actually make a move if it is legal. if not it will do nothing
# and return false.  app class will handle the cancelling procedure.
app.on_move_piece  = model.make

# model asks promotion piece to the interface(app)
model.on_ask_promotion = app.ask_promotion

# 
model.on_setup = app.setup

# on_make is called to handle additional work (rook move in castling,ep capture
# and promotion piece.
model.on_make = app.handle_make
model.on_unmake = app.handle_unmake

# Wire widgets
app.on_prev_btn = model.prev
app.on_next_btn = model.next
app.on_first_btn = model.first
app.on_last_btn = model.last
app.on_prev_game_btn = read_prev
app.on_next_game_btn = read_next

app.master.bind('<Left>', leftkey)
app.master.bind('<Right>', rightkey)
app.master.bind('r', rotatekey)

app.on_open_pgn = open_pgn
#model.on_nav = app.setup
model.on_nav = app.handle_make

app.master.title("Chessvu")
app.mainloop()

