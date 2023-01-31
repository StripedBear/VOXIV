import dlib
import numpy as np
import cv2
import os
import shutil
import time
import logging
import tkinter as tk
from tkinter import messagebox as mb, filedialog
from PIL import Image, ImageTk
import codecs

import configparser
import customtkinter

import processing

detector = dlib.get_frontal_face_detector()

config = configparser.ConfigParser()
config.read_file(codecs.open("config.ini", 'r', 'utf8'))


class FaceRegister(customtkinter.CTk):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.current_frame_faces_cnt = 0  # cnt for counting faces in current frame
        self.existing_faces_cnt = 0  # cnt for counting saved faces
        self.ss_cnt = 0  # cnt for screenshots

        self.title(config["Reg"]['title'])
        self.geometry(config["Reg"]['size'])

        # # GUI left part
        self.frame_left_camera = tk.Frame(self)
        self.label = tk.Label(self)
        self.label.pack(side=tk.LEFT)
        self.frame_left_camera.pack()

        # # GUI right part
        self.frame_right_info = customtkinter.CTkFrame(self, fg_color="transparent",
                                                       border_color='black',
                                                       border_width=1)
        self.label_cnt_face_in_database = customtkinter.CTkLabel(self.frame_right_info,
                                                                 text=str(self.existing_faces_cnt),
                                                                 fg_color='transparent')
        self.label_fps_info = customtkinter.CTkLabel(self.frame_right_info, text="", fg_color='transparent')
        self.input_name = customtkinter.CTkEntry(self.frame_right_info)
        self.input_name_char = ""
        self.label_warning = customtkinter.CTkLabel(self.frame_right_info, text='')
        self.label_face_cnt = customtkinter.CTkLabel(self.frame_right_info, text="", fg_color='transparent')
        self.log_all = customtkinter.CTkLabel(self.frame_right_info, text="")

        self.font_title = customtkinter.CTkFont(family='Helvetica', size=20, weight='bold')
        self.font_step_title = customtkinter.CTkFont(family='Helvetica', size=15, weight='bold')
        self.font_warning = customtkinter.CTkFont(family='Helvetica', size=15, weight='bold')

        self.path_photos_from_camera = config['Reg']['photo_path']
        self.current_face_dir = ""
        self.font = cv2.FONT_ITALIC

        self.current_frame = np.ndarray
        self.face_ROI_image = np.ndarray
        self.face_ROI_width_start = 0
        self.face_ROI_height_start = 0
        self.face_ROI_width = 0
        self.face_ROI_height = 0
        self.ww = 0
        self.hh = 0

        self.out_of_range_flag = False
        self.face_folder_created_flag = False

        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0
        self.fps_show = 0
        self.start_time = time.time()
        self.cap = cv2.VideoCapture(self.camera)  # Get video stream from camera
        # self.cap = cv2.VideoCapture("test.mp4")   # Input local video

    def delete_db(self):
        if mb.askokcancel(config['Ask_win']['title'], config['Ask_win']['question']):
            folders_rd = os.listdir(self.path_photos_from_camera)
            for i in range(len(folders_rd)):
                shutil.rmtree(self.path_photos_from_camera + folders_rd[i])
            if os.path.isfile("data/features_all.csv"):
                os.remove("data/features_all.csv")
            self.label_cnt_face_in_database.configure(text="0")
            self.existing_faces_cnt = 0
            self.log_all.configure(text=config['Text']['db_removed'])

    def gui_get_input_name(self):
        self.input_name_char = self.input_name.get()
        if len(self.input_name_char) > 1:
            self.create_face_folder()
            self.label_cnt_face_in_database.configure(text=str(self.existing_faces_cnt))
        else:
            self.log_all.configure(text=config['Text']['name_er'])

    def gui_info(self):
        customtkinter.CTkLabel(self.frame_right_info,
                               text=config['Text']['registration'],
                               font=self.font_title).grid(row=0, column=1, columnspan=1, padx=2, pady=20)

        customtkinter.CTkLabel(self.frame_right_info,
                               text=config['Text']['FPS']).grid(row=1, column=0, 
                                                                columnspan=2, sticky=tk.W, 
                                                                padx=5, pady=2)
        self.label_fps_info.grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)

        customtkinter.CTkLabel(self.frame_right_info,
                               text=config['Text']['DB_size']).grid(row=2, 
                                                                    column=0, 
                                                                    columnspan=2, 
                                                                    sticky=tk.W, 
                                                                    padx=5, 
                                                                    pady=2)
        self.label_cnt_face_in_database.grid(row=2, column=2, columnspan=3, sticky=tk.W, padx=5, pady=2)

        customtkinter.CTkLabel(self.frame_right_info,
                               text=config['Text']['face_pframe']).grid(row=3,
                                                                        column=0, 
                                                                        columnspan=2, 
                                                                        sticky=tk.W, 
                                                                        padx=5, 
                                                                        pady=2)
        self.label_face_cnt.grid(row=3, column=2, columnspan=3, sticky=tk.W, padx=5, pady=2)

        self.label_warning.grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)

        # Step 1: Input name and create folders for face
        customtkinter.CTkLabel(self.frame_right_info, 
                               font=self.font_step_title, 
                               text=config['Text']['step_1']).grid(row=7, column=0, columnspan=2, 
                                                                   sticky=tk.W, padx=5, pady=20)

        customtkinter.CTkLabel(self.frame_right_info, text=config['Text']['name']).grid(row=8, column=0, 
                                                                                        sticky=tk.W, padx=5, pady=0)
        self.input_name.grid(row=8, column=1, sticky=tk.W, padx=0, pady=2)

        customtkinter.CTkButton(self.frame_right_info,
                                text=config['Text']['ok'],
                                command=self.gui_get_input_name).grid(row=8, column=2, padx=5)

        # Step 2: Save current face in frame
        customtkinter.CTkLabel(self.frame_right_info, 
                               font=self.font_step_title,
                               text=config['Text']['step_2']).grid(row=9, column=0, columnspan=2, 
                                                                   sticky=tk.W, padx=5, pady=[20, 5])

        self.shot = customtkinter.CTkButton(self.frame_right_info,
                                text=config['Text']['save'],
                                command=self.save_current_face)
        self.shot.grid(row=10, column=1)
        customtkinter.CTkButton(self.frame_right_info, 
                                text=config['Text']['load'],
                                command=self.load_photo).grid(row=10, column=2)

        # Show log in GUI
        self.log_all.grid(row=14, column=0, columnspan=4, sticky=tk.W, padx=5, pady=[10, 10])

        customtkinter.CTkButton(self.frame_right_info,
                                text=config['Text']['delete'],
                                command=self.delete_db, fg_color='red').grid(row=12, column=2)
        customtkinter.CTkButton(self.frame_right_info,
                                text=config['Text']['processing'],
                                command=self.processing, fg_color='blue').grid(row=12, column=1, pady=[10, 10])

        self.frame_right_info.pack(pady=[35, 0])

    def load_photo(self):
        self.filepath = filedialog.askopenfilename()
        if os.path.exists(self.current_face_dir) and self.filepath != "":
            if self.filepath.split('.')[-1] == 'jpg':
                shutil.copy(self.filepath, self.current_face_dir)
                self.log_all.configure(text=config['Text']['photo_saved'])
            else:
                self.log_all.configure(text=config['Text']['load_er'])
        else:
            self.log_all.configure(text=config['Text']['pl_step1'])

    def processing(self):
        try:
            processing.main()
            self.log_all.configure(text=config['Text']['processing_d'])
        except Exception as e:
            self.log_all.configure(text=config['Text']['processing_nd'])

    # Mkdir for saving photos and csv
    def pre_work_mkdir(self):
        # Create folders to save face images and csv
        if os.path.isdir(self.path_photos_from_camera):
            pass
        else:
            os.mkdir(self.path_photos_from_camera)

    # Start from person_x+1
    def check_existing_faces_cnt(self):
        if os.listdir():
            #  Get the order of latest person
            person_list = os.listdir(config['Reg']['photo_path'])
            person_num_list = []
            for person in person_list:
                person_order = person.split('_')[1].split('_')[0]
                person_num_list.append(int(person_order.replace('id', '')))
            self.existing_faces_cnt = max(person_num_list, default=0)

        #  Start from person_1
        else:
            self.existing_faces_cnt = 0

    #  Update FPS of Video stream
    def update_fps(self):
        now = time.time()
        # / Refresh fps per second
        if str(self.start_time).split(".")[0] != str(now).split(".")[0]:
            self.fps_show = self.fps
        self.start_time = now
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now

        self.label_fps_info.configure(text=str(self.fps.__round__(2)))

    def create_face_folder(self):
        #  Create the folders for saving faces
        self.existing_faces_cnt += 1
        if self.input_name_char:
            self.current_face_dir = self.path_photos_from_camera + \
                                    "person_id" + str(self.existing_faces_cnt) + "_" + \
                                    self.input_name_char.replace(' ', '-')
        else:
            self.current_face_dir = self.path_photos_from_camera + \
                                    "person_" + str(self.existing_faces_cnt)
        os.makedirs(self.current_face_dir)
        self.log_all.configure(text=config['Text']['record_created'])
        logging.info("\n%-40s %s", "Create folders:", self.current_face_dir)

        self.ss_cnt = 0  # Clear the cnt of screenshots
        self.face_folder_created_flag = True  # Face folder already created

    def save_current_face(self):
        if self.face_folder_created_flag:
            if self.current_frame_faces_cnt == 1:
                if not self.out_of_range_flag:
                    self.ss_cnt += 1
                    # Create blank image according to the size of face detected
                    self.face_ROI_image = np.zeros((int(self.face_ROI_height * 2), self.face_ROI_width * 2, 3),
                                                   np.uint8)
                    for ii in range(self.face_ROI_height * 2):
                        for jj in range(self.face_ROI_width * 2):
                            self.face_ROI_image[ii][jj] = self.current_frame[self.face_ROI_height_start - self.hh + ii][
                                self.face_ROI_width_start - self.ww + jj]
                    self.log_all.configure(text=config['Text']['photo_saved'])
                    self.face_ROI_image = cv2.cvtColor(self.face_ROI_image, cv2.COLOR_BGR2RGB)

                    cv2.imwrite(self.current_face_dir + "/img_face_" + str(self.ss_cnt) + ".jpg", self.face_ROI_image)
                    logging.info("%-40s %s/img_face_%s.jpg", "Save into：",
                                 str(self.current_face_dir), str(self.ss_cnt) + ".jpg")
                else:
                    self.log_all.configure(text=config['Text']['pl_outofrage'])
            else:
                self.log_all.configure(text=config['Text']['pl_face'])
        else:
            self.log_all.configure(text=config['Text']['pl_step1'])

    def get_frame(self):
        try:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except:
            print(config['Text']['error_no_video'])

    # Main process of face detection and saving
    def process(self):
        try:
            ret, self.current_frame = self.get_frame()
            faces = detector(self.current_frame, 0)
            # Get frame
            if ret:
                self.update_fps()
                self.label_face_cnt.configure(text=str(len(faces)))
                #  Face detected
                if len(faces) != 0:
                    # Show the ROI of faces
                    for k, d in enumerate(faces):
                        self.face_ROI_width_start = d.left()
                        self.face_ROI_height_start = d.top()
                        # Compute the size of rectangle box
                        self.face_ROI_height = (d.bottom() - d.top())
                        self.face_ROI_width = (d.right() - d.left())
                        self.hh = int(self.face_ROI_height / 2)
                        self.ww = int(self.face_ROI_width / 2)

                        # If the size of ROI > 480x640
                        if (d.right() + self.ww) > 640 or (d.bottom() + self.hh > 480) or (d.left() - self.ww < 0) or (
                                d.top() - self.hh < 0):
                            self.label_warning.configure(text=config['Text']['out_ofrage'], text_color='red')
                            self.out_of_range_flag = True
                            color_rectangle = (255, 0, 0)
                        else:
                            self.out_of_range_flag = False
                            self.label_warning.configure(text="")
                            color_rectangle = (0, 255, 0)
                        self.current_frame = cv2.rectangle(self.current_frame,
                                                           tuple([d.left() - self.ww, d.top() - self.hh]),
                                                           tuple([d.right() + self.ww, d.bottom() + self.hh]),
                                                           color_rectangle, 2)
                self.current_frame_faces_cnt = len(faces)

                # Convert PIL.Image.Image to PIL.Image.PhotoImage
                self.img_Image = Image.fromarray(self.current_frame)
                self.img_PhotoImage = ImageTk.PhotoImage(image=self.img_Image)
                self.label.img_tk = self.img_PhotoImage
                self.label.configure(image=self.img_PhotoImage)

            # Refresh frame
            self.after(20, self.process)
        except Exception:
            print('no camera')
            self.geometry(config['Reg']['size_nocam'])
            self.shot.configure(fg_color='grey', state='disabled')


    def run(self):
        self.pre_work_mkdir()
        self.check_existing_faces_cnt()
        self.gui_info()
        self.process()
        self.mainloop()


def main(camera):
    logging.basicConfig(level=logging.INFO)
    customtkinter.set_appearance_mode("light")
    customtkinter.set_default_color_theme("blue")
    face_reg_con = FaceRegister(camera=camera)
    face_reg_con.run()


if __name__ == '__main__':
    main(0)

