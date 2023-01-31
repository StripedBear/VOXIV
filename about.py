import customtkinter
import tkinter  


class About(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.label = customtkinter.CTkLabel(self,
                                            text='Monitoring system with face registration, person detection, alert',
                                            font=('', 13))
        self.label.grid(row=0, column=4, padx=[60, 0], pady=[20, 0])

        self.label = customtkinter.CTkLabel(self, text='GitHub', font=('', 13))
        self.label.grid(row=1, column=4, padx=[60, 0], pady=[20,0])
        text_var1 = tkinter.StringVar(value='https://github.com/StripedBear/DSys')
        self.label2 = customtkinter.CTkEntry(self, width=270, state='readonly', textvariable=text_var1, font=('', 10))
        self.label2.grid(row=2, column=4, pady=[10, 40], padx=[50, 0])
        
        self.label = customtkinter.CTkLabel(self, text='If you have any questions:', font=('', 13))
        self.label.grid(row=3, column=4, pady=[20, 0], padx=[60, 0])
        text_var2 = tkinter.StringVar(value='stripedbear@tutanota.com')
        self.label2 = customtkinter.CTkEntry(self, width=190, state='readonly', textvariable=text_var2, font=('', 10))
        self.label2.grid(row=4, column=4, pady=[10, 0], padx=[55, 0])
 
