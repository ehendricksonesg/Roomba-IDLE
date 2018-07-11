from Tkinter import *

class Text2( Frame ):
    # Now width and height are in pixels. They are not now the number of columns and the number of lines respectively
    #Text2(root, width=90,height=120).pack()
    def __init__(self, master, width=0, height=0, **kwargs):
        self.width = width
        self.height = height

        Frame.__init__(self, master, width=self.width, height=self.height)
        self.text_widget = Text(self, **kwargs)
        self.text_widget.insert(END, "G")
        self.text_widget.pack(expand=YES, fill=BOTH)

    def pack(self, *args, **kwargs):
        Frame.pack(self, *args, **kwargs)
        self.pack_propagate(False)

    def grid(self, *args, **kwargs):
        Frame.grid(self, *args, **kwargs)
        self.grid_propagate(False)

root = Tk()

Text2(root, width=90,height=120).pack()

root.mainloop()
