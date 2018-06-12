from Tkinter import *
#from connectfour import *
#from minimax import *
#from player import *
import tkMessageBox

class ConnectFourGUI:
    def DrawGrid(self):
        for i in range(0,self.cols+1):
            self.c.create_line((i+1)*self.mag,self.mag,\
                            (i+1)*self.mag,(self.rows+1)*self.mag)
        for i in range(0,self.rows+1):
            self.c.create_line(self.mag,(i+1)*self.mag,\
                            self.mag*(1+self.cols),(i+1)*self.mag)
    def __init__(self,wdw):
        wdw.title("Connect Four")
        self.mag = 60
        self.rows = 6
        self.cols = 7
        self.c = Canvas(wdw,\
         width=self.mag*self.cols+2*self.mag,\
         height = self.mag*self.rows+2*self.mag,\
         bg='white')
        self.c.grid(row=1,column=1,columnspan=2)
        rlabel=Label(root, text="Player1:")
        rlabel.grid(row=0,column=0)
        self.player1_type=StringVar(root)
        options= ["Human", "Random", "Minimax"]
        self.player1_type.set(options[2])
        self.rowbox=OptionMenu(root, self.player1_type, *options)
        self.rowbox.grid(row=0, column=1)
        rlabel2=Label(root, text="Player2:")
        rlabel2.grid(row=0,column=2)
        self.player2_type=StringVar(root)
        self.player2_type.set(options[0])
        self.rowbox=OptionMenu(root, self.player2_type, *options)
        self.rowbox.grid(row=0, column=3)
        begin=Button(root, text="Start", command=self.game_start)
        begin.grid(row=0, column=4)
        self.c.grid(row=1, column=0, columnspan=7)
        play_col=[]
        for i in range(self.cols):
            play_col.append(Button(root, text= "Col %d" %i, command=lambda col= i: self.human_play(col)))
            play_col[i].grid(row=10,column="%d"%i)
##      self.DrawCircle(1,1,1) self.DrawCircle(2,2,1) self.DrawCircle(5,3,2)
            self.DrawGrid()
            #self.brd = ConnectFour()
            
    def game_start(self):
        self.board=ConnectFour()
        print self.player1_type.get()
        print self.player2_type.get()
        if self.player1_type.get()=="Random":
            self.player1 = RandomPlayer(playernum=1)
            if self.player2_type.get()== "Random" or self.player2_type.get() == "Minimax":
                tkMessageBox.showinfo("Bad Choice", "You Have to choose At least 1 Human Player")
            else:
                self.player
        elif self.player1_type.get()=="Minimax":
            self.player1=MinimaxPlayer(playernum=2, ply_depth=4, utility=SimpleUtility(5,1))
            if self.player2_type.get()== "Random" or self.player2_type.get() == "Minimax":
                tkMessageBox.showinfo("Bad Choice", "You Have to choose At least 1 Human Player")
        elif self.player1_type.get()=="Human":
            self.player1=Human(playernum=1)
        if self.player2_type.get()=="Human":
            self.player2=Human(playernum=2)
        elif self.player2_type.get()=="Random":
            self.player2=RandomPlayer(playernum=2)
        elif self.player2_type.get()=="Minimax":
            self.player2=MinimaxPlayer(playernum=2, ply_depth=4, utility=SimpleUitlity(5,1))
        #self.currentplayer==1 self.draw()
            
    def human_play(self, col):
        if self.player1_type.get()=="Human" and self.player2_type.get() =="Human":
            while True:
                self.DrawCircle(row,col,1)
                if self.brd.is_game_over() is None:
                    self.DrawCircle(row,col,2)
                    if self.brd.is_game_over() is None:
                        pass
                    else:
                        print "Player 2 wins!"
                        break
                else:
                    print "Player 1 wins!"
                    break
                
    def DrawCircle(self,row,col,player_num):
        if player_num == 1:
            fill_color = 'red'
        elif player_num == 2:
            fill_color = 'black'
        #(startx, starty, endx, endy)
        self.c.create_oval(col*self.mag,row*self.mag,(col+1)*self.mag,(row+1)*self.mag,fill=fill_color) 

root=Tk()
ConnectFourGUI(root)
root.mainloop()
