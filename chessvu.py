import os
import re
import chess
import board
import pgn

board.tsize = 45
g_idx = 0

def read_prev():
    global g_idx, model, pf,app
    if g_idx <=0:
        return
    g_idx-=1
    pf.read_into_model(g_idx,model)
    app.master.title(str(g_idx+1))

def read_next():
    global g_idx, model, pf,app
    if g_idx > len(pf.games):
        return
    g_idx+=1
    pf.read_into_model(g_idx,model)
    app.master.title(str(g_idx+1))

def open_pgn(filename):
    global pf,g_idx,model
    g_idx=0
    pf = pgn.PGN_File(filename)
    pf.read_into_model(g_idx,model)
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
app.on_prev_game_btn = read_prev
app.on_next_game_btn = read_next
app.on_open_pgn = open_pgn
model.on_nav = app.setup

app.master.title("Chessvu")
app.mainloop()
