# board.py
# Graphical representation of chess board

from PIL import Image,ImageTk
import Tkinter as tk
import tkFileDialog

from node import Node
from chess import Move
from chess import PGN
padding = 2 # distance from edge of the time to edge of piece

oldx = -1
oldy = -1
drag_sq = -1

"""
class PGN:
    lvl = 0
    new_context = True
    @staticmethod

    def init():
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
"""

class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self,master)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(3, weight=1)
       
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=2)
        self.master.grid_columnconfigure(2, weight=3)
        self.master.grid_columnconfigure(3, weight=4)

        self.canvas = tk.Canvas(self.master, width=sq_size*8, height=sq_size*8)
        self.create_widgets()
        self.canvas.pack()
       
        self.first_btn = tk.Button(text="|<",command=self.first,width = 15)
        self.last_btn = tk.Button(text=">|",command=self.last,width = 15) 
        self.prev_btn = tk.Button(text="<",command=self.prev,width = 15)
        self.next_btn = tk.Button(text=">", command=self.next,width = 15)
        self.prev_game_btn = tk.Button(text="prev",command=self.prev_game)
        self.next_game_btn = tk.Button(text="next",command=self.next_game)
        
        self.vars_list = tk.Listbox(master, width = 15, height = 5)
        self.vars_list.bind('<<ListboxSelect>>', self.on_vars_list_select)
        self.del_var_btn = tk.Button(text="Del var",command=self.del_var)
        self.comment_tbox = tk.Text(width = 30, height =18)       
        self.canvas.grid(column=0,row=0,rowspan=3,columnspan=4)

        self.first_btn.grid(row=3, column=0, padx = 1, pady = 1)
        self.prev_btn.grid(row=3, column=1, padx = 1, pady = 1)
        self.next_btn.grid(row=3, column=2, padx = 1, pady = 1)
        self.last_btn.grid(row=3, column=3, padx = 1, pady = 1)
        self.prev_game_btn.grid(row=3, column=4)
        self.next_game_btn.grid(row=3, column=5)
        self.vars_list.grid(row=0, columnspan=2, column=4)
        self.comment_tbox.grid(row=2, columnspan=2, column=4)
        self.del_var_btn.grid(row=1, column=4)

        mb = tk.Menu(self.master)
        self.master.config(menu=mb)
    
        filemenu = tk.Menu(mb)
        filemenu.add_command(label = "Open",command = self.open_pgn)
        filemenu.add_command(label = "Quit",command = self.quit)
        mb.add_cascade(label="File",menu = filemenu)

        editmenu = tk.Menu(mb)
        editmenu.add_command(label = "Copy position",command = self.copy_position)
        editmenu.add_command(label = "Copy game", command = self.copy_game)
        mb.add_cascade(label="Edit",menu = editmenu)
    
        self.piece_objs = {}    # Canvas object indices of.piece_objs 
        
        self.canvas.bind("<Button-1>", self.mouse_click)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_release)
        self.canvas.bind("<B1-Motion>", self.mouse_move)
#       self.bind("<Key>", self.key_press)        
        self.rotate = False

    def on_vars_list_select(self,e):
        w = e.widget
        s = w.curselection()
        if len(s)>0:
            Node.cur_node.next_index = int(s[0])

    def open_pgn(self):
        self.opt = opt = {}
        opt["defaultextension"] = ".pgn"
        opt["initialdir"] = "~"
        opt['parent'] = 'root'
        opt['title'] = 'Choose PGN file'
        path = tkFileDialog.askopenfilename()
        self.on_open_pgn(path)
        pass
    
    def copy_position(self):
        pass

    def copy_game(self):
        save_node = Node.cur_node
        n = Node.cur_node
        while n.parent != None:
            n = n.parent
        PGN.init_encode()
        s = PGN.encode_node(n)
        
        print s
        Node.cur_node = save_node
        pass

    def coord_to_sq(self,coord):
        sq = (coord[1] // sq_size) * 8 + (coord[0] // sq_size)
        if self.rotate:
            sq = 63-sq
        return sq

    def sq_to_coord(self, sq):
        if self.rotate:
            sq = 63-sq
        return ((sq % 8) * sq_size,(sq // 8) * sq_size)
        
    def read_piece_image(self,pc, darker):
        path = "Data/PIECE/Dyche/"
        image = Image.open(path+pc+".png")
        image = image.resize((sq_size,sq_size), Image.ANTIALIAS)
        if darker: image = self.darker_image(image)
        img = ImageTk.PhotoImage(image)
        return img

    # Returns tinted image
    def darker_image(self, img):
        pxls = img.load()
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                alpha = 0.7   # 0..1 :  0 is darkest
                beta = -30
                pxls[i,j] = (
                        int(pxls[i,j][0] * alpha + beta),
                        int(pxls[i,j][1] * alpha + beta),
                        int(pxls[i,j][2] * alpha + beta),
                        pxls[i,j][3])
        return img

    def create_widgets(self):
        # Create square objects
        self.canvas.squares = []
        for sq in range(64):
            x=sq%8
            y=sq//8
            color="#00A040" if (x+y)%2 == 1 else "#00D015" 
            sq = self.canvas.create_rectangle(
                    x * sq_size, 
                    y * sq_size,
                    (x * sq_size + sq_size, y * sq_size + sq_size), 
                    fill = color)
            self.canvas.squares.append(sq)

        # Read piece picture (dictionary:keys are r,n,b,q,k,p,R,N,B,Q,K)
        pc_names = ["R","N","B","Q","K","P"]
        pc_imgs = {}
        for i in pc_names:
            pc_imgs[i] = self.read_piece_image(i,False)

        #create darker images for black
        for pn in pc_names:
            pc_imgs[pn.lower()] = self.read_piece_image(pn, True)
      
        self.canvas.pc_imgs = pc_imgs
#       self.canvas.pack()

    def mouse_click(self,event):
        """ Called when user mouse click,
        Starts dragging piece if square is clicked """
        global drag_sq
#       print "click at {0} {1}".format(event.x,event.y)
#       sq = (event.y // sq_size) * 8 + event.x // sq_size
        sq = self.coord_to_sq((event.x, event.y))
        if sq in self.piece_objs:
            drag_sq = sq
            self.canvas.tag_raise(self.piece_objs[sq])
        return
   
    def mouse_release(self,event):
        """ Called when mouse is released,
        Stop dragging piece and ask if the move is legal
        """
        global drag_sq
        if drag_sq != -1:
#           dst_sq = (event.y // sq_size) * 8+ (event.x // sq_size)
            dst_sq = self.coord_to_sq((event.x, event.y))
            
            m = Move(drag_sq, dst_sq)
            m.set_from_user()  # this is input from user (not file)
        
            if not self.on_move_piece(m):
                # Withdraw the piece to original spot
                obj = self.piece_objs[drag_sq]
                
                self.canvas.coords(obj, 
                        self.sq_to_coord(drag_sq))
#                       ((drag_sq%8)*sq_size, (drag_sq//8)*sq_size))
            drag_sq = -1
        return

    def mouse_move(self,event):
        global oldx,oldy,drag_sq
        if drag_sq == -1: return
#       print "move by {0} {1}".format(event.x-oldx, event.y-oldy)
        obj = self.piece_objs[drag_sq]
        self.canvas.coords(obj, (event.x-sq_size//2, event.y-sq_size//2))
        oldx = event.x 
        oldy = event.y
        return
    
    def key_press(self, event):
        print "key press",repr(event.char)
        return

    def first(self):
        try:
            self.on_first_btn()
        except AttributeError:
            pass

    def last(self):
        try:
            self.on_last_btn()
        except AttributeError:
            pass

    def prev(self):
        try:
            self.on_prev_btn()
        except AttributeError:
            pass

    def next(self):
        try:
            self.on_next_btn()
        except AttributeError:
            pass

    def prev_game(self):
        try:
            self.on_prev_game_btn()
        except AttributeError:
            pass
    
    def next_game(self):
        try:
            self.on_next_game_btn()
        except AttributeError:
            pass

    def nav(self,dir):
        print "nav button"
        pass
    
    def put(self,sq,p):         # Simply put piece on a square
        if p==" ": return
        xy = self.sq_to_coord(sq)
        try:
            self.piece_objs[sq] = self.canvas.create_image(
                xy[0],
                xy[1],
                anchor=tk.NW, 
                image=self.canvas.pc_imgs[p])
        except KeyError:
            print "doesn't have piece image:"+p

    def remove(self,sq):
        if sq < 0 or sq >= 64: return
        try:
            if sq in self.piece_objs:
                self.canvas.delete(self.piece_objs[sq])
                del self.piece_objs[sq]
        except KeyError:
            print "probably wrong square at remove point"
    
    def setup(self,pos):
        # Remove images from board
        for sq in range(64):
            self.remove(sq)

        sq=0
        for p in pos.pos:
            if "12345678".find(p) != -1:
                c = int(p)
                sq += c
            elif "RNBQKP".find(p.upper()) != -1:
                self.put(sq,p)   
                sq += 1
            elif p == " ":
                sq += 1
        self.update_vars_list()

    def move(self,move):
        src = move[0]
        dst = move[1]
        if src < 0 or dst < 0: return
        if not src in  self.piece_objs:
#           print "wrong move" + str(src) + "-" + str(dst)
            return
        # Change coordinate to destination
        self.canvas.coords(self.piece_objs[src],
                self.sq_to_coord(dst))
        # Update dictinary
        self.piece_objs[dst] = self.piece_objs[src]
        del self.piece_objs[src]

    def handle_make(self, move):
        """ Post process after actually model has changed """
#       print "handle make-"+str(move.src)+":"+str(move.dst)
        if not move: return
        # remove en passant capture
        if move.is_en_passant():
            self.remove(move.dst + (8 if move.is_white() else -8))
        if move.is_capture():
            self.remove(move.dst)

        # move rook when castling
        if move.is_castling_short():
            if move.is_white():
                self.move((63,61))
            else:
                self.move((7,5))
        if move.is_castling_long():
            if move.is_white():
                self.move((56, 59))
            else:
                self.move((0, 3))
        # Actual move itself.
        self.move((move.src, move.dst))

        # Replace promoted piece.
        if move.is_promotion():
            self.remove(move.dst)
            p_piece = move.get_promotion_piece()
            if not move.is_white(): p_piece = p_piece.lower()
#           print "promoting to "+p_piece+" at "+move.dst
            self.put(move.dst, p_piece)
        self.update_vars_list() 
        
    def handle_unmake(self, move):
        """ Post process after actually model has changed """
#       print "board:handle_make pgn = " + move.pgn
        if not move: return
        # remove en passant capture
        if move.is_en_passant():
            self.put(move.dst + (8 if move.is_white() else -8), \
                'p' if move.is_white() else 'P')

        # move rook when castling
        if move.is_castling_short():
            if move.is_white():
                self.move((61,63))
            else:
                self.move((5,7))
        if move.is_castling_long():
            if move.is_white():
                self.move((59, 56))
            else:
                self.move((3, 0))

        # now move itself
        self.move((move.dst, move.src))
        
        # recover capture
        if move.is_capture():
            p = move.get_captured_piece()
            if move.is_white(): p = p.lower()
            self.put(move.dst, p)

        # Recover promoted piece
        if move.is_promotion():
            self.remove(move.src)
            self.put(move.src, 'P' if move.is_white() else 'p')
        self.update_vars_list() 
    
    def update_vars_list(self):
        self.vars_list.delete(0, tk.END)
        if Node.cur_node == None:
            return
        for n in Node.cur_node.childs:
            s = str(n.data.last_move.number) 
            s += ". " if n.data.last_move.is_white() else "... "
            s += n.data.last_move.pgn
            self.vars_list.insert(tk.END, s)
#       print "var num:"+str(len(Node.cur_node.childs))

    def ask_promotion(self,side):
        print "returning Q"
        if side==1: return "Q"
        return "q"

    def rotate_board(self):
        # rotate pieces individually
        for src in range(64):
            if src in self.piece_objs:
                dst = 63-src 
                self.canvas.coords(self.piece_objs[src],
                        self.sq_to_coord(dst))
        self.rotate = not self.rotate

    def del_var(self):
        """ delete current variation """
#       print "board:move"
        while Node.cur_node.parent != None:
            self.prev()
            if len(Node.cur_node.childs) > 1:
                break

if __name__ == "__main__":
    app = App(tk.Tk())
    app.master.title("Chess board")
    app.setup("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
#   app.handle_move((60,50))
    app.mainloop()

