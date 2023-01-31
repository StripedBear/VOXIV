import configparser
from tkinter import END
import codecs
import customtkinter
import face_detect
import registration
import about

config = configparser.ConfigParser()
config.read_file(codecs.open("config.ini", 'r', 'utf8'))


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title(config['Main']['title'])
        self.geometry('550x380')

        self.tabview = customtkinter.CTkTabview(self, height=370, width=530)
        self.tabview.pack()

        self.tabview.add("Connect")
        self.tabview.add("Settings")
        self.tabview.add("About")

        self.label2 = customtkinter.CTkLabel(self.tabview.tab('Connect'), text=config['Main']['title_con'], font=('', 18))
        self.label2.grid(row=2, column=1, pady=[10, 20], padx=[150, 0])

        self.checkbox = customtkinter.CTkCheckBox(self.tabview.tab('Connect'), text=config['Main']['webcam'])
        self.checkbox.grid(row=3, column=1, padx=[150, 0])
        self.label3 = customtkinter.CTkLabel(self.tabview.tab('Connect'), text=config['Main']['or'])
        self.label3.grid(row=4, column=1, padx=[150, 0])

        self.entry = customtkinter.CTkTextbox(self.tabview.tab('Connect'), width=500, height=110)
        self.entry.grid(row=5, column=0, columnspan=3, pady=[0, 30], padx=[10, 0])
        self.entry.insert("0.0", config['Main']['in_add'])

        self.connect_b = customtkinter.CTkButton(self.tabview.tab('Connect'),
                                                 text=config['Main']['connect'],
                                                 fg_color='green',
                                                 command=self.connect)
        self.connect_b.grid(row=6, column=2, pady=[0, 10])

        self.registration = customtkinter.CTkButton(self.tabview.tab('Connect'),
                                                    text=config['Main']['registration'],
                                                    fg_color='green',
                                                    command=self.registr)
        self.registration.grid(row=7, column=2, pady=[0, 10])

        self.settings_frame_1 = EntryFrame(self.tabview.tab('Settings'),
                                           header_name="Window Size",
                                           label_h='height',
                                           label_w='width')
        self.settings_frame_1.grid(row=0, column=0, padx=20, pady=20)

        self.settings_frame_2 = EntryFrame(self.tabview.tab('Settings'),
                                           header_name="Frame Size",
                                           label_h='height',
                                           label_w='width'
                                           )
        self.settings_frame_2.grid(row=0, column=1, padx=20, pady=20)

        self.settings_frame_3 = ButtonFrame(self.tabview.tab('Settings'), header_name="FPS")
        self.settings_frame_3.grid(row=0, column=2, padx=20, pady=20)

        self.frame_1_button = customtkinter.CTkButton(self.tabview.tab('Settings'),
                                                      text="Apply",
                                                      command=lambda: self.set_size(self.settings_frame_1,
                                                                                    'window_size_h',
                                                                                    'window_size_w'))
        self.frame_1_button.grid(row=1, column=0, padx=20, pady=10)
        self.frame_2_button = customtkinter.CTkButton(self.tabview.tab('Settings'), text="Apply",
                                                      command=lambda: self.set_size(self.settings_frame_2,
                                                                                    'size_h',
                                                                                    'size_w'))
        self.frame_2_button.grid(row=1, column=1, padx=20, pady=10)
        self.frame_3_button = customtkinter.CTkButton(self.tabview.tab('Settings'), text="Apply", command=self.set_fps)
        self.frame_3_button.grid(row=1, column=2, padx=20, pady=10)

        about.About(self.tabview.tab("About")).pack(fill='both', expand=True)

    def set_size(self, settings_frame, arg_h, arg_w):
        try:
            height, width = settings_frame.get_value()
            if height is not None and width is not None:
                config['Stream'][arg_h] = str(height)
                config['Stream'][arg_w] = str(width)
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
        except Exception:
            print('Wrong input')

    def set_fps(self):
        if (fps := self.settings_frame_3.set_value()) != '':
            config['Stream']['fps_f'] = fps
            with open('config.ini', 'w') as configfile:
                config.write(configfile)

    def registr(self):
        program.destroy()
        new_win = registration.FaceRegister(0)
        new_win.run()

    def connect(self):
        if self.checkbox.get():
            program.destroy()
            face_recogn_con = face_detect.FaceRecognizer()
            face_recogn_con.run(0)
        else:
            address = self.entry.get('0.0', END).rstrip()
            if address not in [' Add address', '', 'Add address']:
                print(f'connect to: {address}')
                program.destroy()
                face_recogn_con = face_detect.FaceRecognizer()
                face_recogn_con.run(address)
            else:
                print('Wrong input')


class EntryFrame(customtkinter.CTkFrame):
    def __init__(self, *args, header_name="EntryFrame", label_h='label1', label_w='label2', **kwargs):
        super().__init__(*args, **kwargs)

        self.header_name = header_name
        self.label1 = label_h
        self.label2 = label_w

        self.header = customtkinter.CTkLabel(self, text=self.header_name)
        self.header.grid(row=0, column=0, padx=10, pady=10)

        self.label_height = customtkinter.CTkLabel(self, text=self.label1)
        self.label_height.grid(row=1, padx=10, pady=[10, 0])

        self.entry_set = customtkinter.CTkEntry(self, width=100)
        self.entry_set.grid(row=2, column=0, padx=10, pady=[5, 10])

        self.label_width = customtkinter.CTkLabel(self, text=self.label2)
        self.label_width.grid(row=3, padx=10, pady=[10, 0])

        self.entry_set2 = customtkinter.CTkEntry(self,  width=100)
        self.entry_set2.grid(row=4, column=0, padx=10, pady=[5, 10])

    def get_value(self):
        try:
            return int(self.entry_set.get()), int(self.entry_set2.get())
        except Exception:
            print('Wrong input')


class ButtonFrame(customtkinter.CTkFrame):
        def __init__(self, *args, header_name="ButtonFrame", **kwargs):
            super().__init__(*args, **kwargs)

            self.header_name = header_name

            self.radio_button_var = customtkinter.StringVar(value="")
            self.header = customtkinter.CTkLabel(self, text=self.header_name)
            self.header.grid(row=0, column=0, padx=10, pady=10)

            self.radio_button_var = customtkinter.StringVar(value="")

            self.radio_button_1 = customtkinter.CTkRadioButton(self, text="Default", value="Option 1",
                                                               variable=self.radio_button_var)
            self.radio_button_1.grid(row=1, column=0, padx=10, pady=10)
            self.radio_button_2 = customtkinter.CTkRadioButton(self, text="Each 2d frame", value="Option 2",
                                                               variable=self.radio_button_var)
            self.radio_button_2.grid(row=2, column=0, padx=10, pady=10)
            self.radio_button_3 = customtkinter.CTkRadioButton(self, text="Each 5th frame", value="Option 3",
                                                               variable=self.radio_button_var)
            self.radio_button_3.grid(row=3, column=0, padx=10, pady=(10, 45))

        def set_value(self):
            return self.radio_button_var.get()


def close_window():
    program.destroy()


if __name__ == '__main__':
    customtkinter.set_appearance_mode("light")
    customtkinter.set_default_color_theme("green")
    program = App()
    program.protocol('WM_DELETE_WINDOW', close_window)
    program.mainloop()