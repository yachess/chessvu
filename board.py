# board.py
# Graphical representation of chess board


from PIL import Image,ImageTk
import Tkinter as tk
import tkFileDialog

padding = 2 # distance from edge of the time to edge of piece

oldx = -1
oldy = -1
drag_sq = -1

class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self,master)
        self.pack()
        self.master.geometry("%dx%d"%(sq_size*8+2, sq_size*8+20))
        self.canvas = tk.Canvas(self, width=sq_size*8, height=sq_size*8)
        self.create_widgets()
       
        self.first_btn = tk.Button(text="|<",command=self.first)
        self.last_btn = tk.Button(text=">|",command=self.last) 
        self.prev_btn = tk.Button(text="<",command=self.prev)
        self.next_btn = tk.Button(text=">", command=self.next)
        self.prev_game_btn = tk.Button(text="prev",command=self.prev_game)
        self.next_game_btn = tk.Button(text="next",command=self.next_game)
        
        self.revert_btn = tk.Button(text="Revert",command=self.revert)
        self.quit_btn = tk.Button(text="Quit",command=self.quit)
 #      self.prev_btn.grid(row = 1, column = 0)
 #      self.next_btn.grid(row = 1, column = 1)
 #      self.quit_btn.grid(row = 1, column = 2)
        self.first_btn.pack(side=tk.LEFT)
        self.prev_btn.pack(side=tk.LEFT)
        self.next_btn.pack(side=tk.LEFT)
        self.last_btn.pack(side=tk.LEFT)
        self.prev_game_btn.pack(side=tk.LEFT)
        self.next_game_btn.pack(side=tk.LEFT)
        self.revert_btn.pack(side=tk.LEFT)
        self.quit_btn.pack(side=tk.LEFT)
        
        mb = tk.Menu(self.master)
        self.master.config(menu=mb)
    
        filemenu = tk.Menu(mb)
        filemenu.add_command(label = "Open",command = self.open_pgn)
        filemenu.add_command(label = "Quit",command = self.quit)
        mb.add_cascade(label="File",menu = filemenu)

        self.piece_objs = {}    # Canvas object indices of.piece_objs 
        
        self.canvas.bind("<Button-1>", self.mouse_click)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_release)
        self.canvas.bind("<B1-Motion>", self.mouse_move)
#       self.bind("<Key>", self.key_press)        
        self.rotate = False

    def open_pgn(self):
        self.opt = opt = {}
        opt["defaultextension"] = ".pgn"
        opt["initialdir"] = "~"
        opt['parent'] = 'root'
        opt['title'] = 'Choose PGN file'
        path = tkFileDialog.askopenfilename()
        
        self.on_open_pgn(path)
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
        self.canvas.pack()

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
        move actually if the move is legal
        """
        global drag_sq
        if drag_sq != -1:
#           dst_sq = (event.y // sq_size) * 8+ (event.x // sq_size)
            dst_sq = self.coord_to_sq((event.x, event.y))
            if self.on_move_piece((drag_sq, dst_sq)):
                self.move((drag_sq,dst_sq))        
            else:
                # Withdraw the piece to original spot
                print "not legal move"
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
        self.piece_objs[sq] = self.canvas.create_image(
                xy[0],
                xy[1],
                anchor=tk.NW, 
                image=self.canvas.pc_imgs[p])

    def remove(self,sq):
        if sq < 0 or sq >= 64: return
        if sq in self.piece_objs:
            self.canvas.delete(self.piece_objs[sq])
            del self.piece_objs[sq]

    # Public interfaces
    # pos_str can be either FEN or raw position data
    def setup(self,pos_str):
        # Remove images from board
#       for val in self.piece_objs:
#           self.canvas.delete(val)
#       # Clear the data
#       self.piece_objs.clear()
    
        for sq in range(64):
            self.remove(sq)

        sq=0
        for p in pos_str:
            if "12345678".find(p) != -1:
                c = int(p)
                sq += c
            elif "RNBQKP".find(p.upper()) != -1:
                self.put(sq,p)   
                sq += 1
            elif p == " ":
                sq += 1

    def move(self,move):
        src = move[0]
        dst = move[1]
        if src < 0 or dst < 0: return

        # Delete captured if exists
        self.remove(dst)

        # Move
        self.canvas.coords(self.piece_objs[src],
                self.sq_to_coord(dst))
#               ((dst % 8) * sq_size,(dst // 8) * sq_size))
        self.piece_objs[dst] = self.piece_objs[src]
        del self.piece_objs[src]
        print "board:move"

    # Post process after make move
    # Note that this method is called before board:move
    def handle_make(self, move):
        # Delete enpassant capture
        if move.is_en_passant():
            self.remove(move.dst + (8 if move.is_white() else -8))
        elif move.is_short_castling() and move.is_white():
            self.move((63,61))
        elif move.is_long_castling() and move.is_white():
            self.move((56, 59))
        elif move.is_short_castling() and move.is_black():
            self.move((7, 5))
        elif move.is_long_castling() and move.is_black():
            self.move((0, 3))
        elif move.is_promotion():
            # replace srs_sq piece (since piece hsn't moved yet we use source square)
            self.remove(move.src)
            pc = move.get_promotion_piece()
            if move.is_black():
                pc = pc.lower()
            self.put(move.src,pc)
#       print "board:handle_make ", mtype
    
    def ask_promotion(self,side):
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

    def revert(self):
        print "revert"


if __name__ == "__main__":
    app = App(tk.Tk())
    app.master.title("Chess board")
    app.setup("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
#   app.handle_move((60,50))
    app.mainloop()

