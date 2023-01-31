import tkinter.messagebox
import codecs
from playsound import playsound
import configparser
import imutils
from telethon.sync import TelegramClient

import dlib
import numpy as np
import cv2
import os
import pandas as pd
import time
import logging

# Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()

# Get face landmarks
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

# Use Dlib resnet50 model to get 128D face descriptor
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

config = configparser.ConfigParser()
config.read_file(codecs.open("config.ini", 'r', 'utf8'))

client = TelegramClient(config['Telegram']['number'], int(config['Telegram']['api_id']), config['Telegram']['api_hash'])


class FaceRecognizer:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_COMPLEX
        # FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0
        self.fps_show = 0
        self.start_time = time.time()
        # cnt for frame
        self.frame_cnt = 0
        # Save the features of faces in the database
        self.face_features_known_list = []
        #  Save the name of faces in the database
        self.face_name_known_list = []
        #  List to save centroid positions of ROI in frame N-1 and N
        self.last_frame_face_centroid_list = []
        self.current_frame_face_centroid_list = []
        # List to save names of objects in frame N-1 and N
        self.last_frame_face_name_list = []
        self.current_frame_face_name_list = []
        #  cnt for faces in frame N-1 and N
        self.last_frame_face_cnt = 0
        self.current_frame_face_cnt = 0
        #  Save the e-distance for faceX when recognizing
        self.current_frame_face_X_e_distance_list = []
        #  Save the positions and names of current faces captured
        self.current_frame_face_position_list = []
        #  Save the features of people in current frame
        self.current_frame_face_feature_list = []
        # e distance between centroid of ROI in last and current frame
        self.last_current_frame_centroid_e_distance = 0
        # Reclassify after 'reclassify_interval' frames
        self.reclassify_interval_cnt = 0
        self.reclassify_interval = 10
        self.flist_lim = config['Capture']['flist_limit']
        self.pc_unknown = config['Capture']['pc_unknown']
        self.faces = []
        self.quit_key = config['Stream']['quit']

        self.fps_formula = {'Option 1': '1',
                            'Option 2': 'count1 % 10 == 5 or count1 % 10 == 0',
                            'Option 3': 'count1 % 2 == 0'}

    # Get known faces from "features_all.csv"
    def get_face_database(self):
        if os.path.exists("data/features_all.csv"):
            path_features_known_csv = "data/features_all.csv"
            csv_rd = pd.read_csv(path_features_known_csv, header=None)
            for i in range(csv_rd.shape[0]):
                features_someone_arr = []
                self.face_name_known_list.append(csv_rd.iloc[i][0])
                for j in range(1, 129):
                    if csv_rd.iloc[i][j] == '':
                        features_someone_arr.append('0')
                    else:
                        features_someone_arr.append(csv_rd.iloc[i][j])
                self.face_features_known_list.append(features_someone_arr)
            logging.info("Faces in Database： %d", len(self.face_features_known_list))
            return 1
        else:
            logging.warning("'features_all.csv' not found!")
            return 0

    def update_fps(self):
        now = time.time()
        # Refresh fps per second
        if str(self.start_time).split(".")[0] != str(now).split(".")[0]:
            self.fps_show = self.fps
        self.start_time = now
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now

    @staticmethod
    #  Compute the e-distance between two 128D features
    def return_euclidean_distance(feature_1, feature_2):
        feature_1 = np.array(feature_1)
        feature_2 = np.array(feature_2)
        dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
        return dist

    #  Use centroid tracker to link face_x in current frame with person_x in last frame
    def centroid_tracker(self):
        for i in range(len(self.current_frame_face_centroid_list)):
            e_distance_current_frame_person_x_list = []
            # For object 1 in current_frame, compute e-distance with object 1/2/3/4/... in last frame
            for j in range(len(self.last_frame_face_centroid_list)):
                self.last_current_frame_centroid_e_distance = self.return_euclidean_distance(
                    self.current_frame_face_centroid_list[i], self.last_frame_face_centroid_list[j])
                e_distance_current_frame_person_x_list.append(
                    self.last_current_frame_centroid_e_distance)
            last_frame_num = e_distance_current_frame_person_x_list.index(
                min(e_distance_current_frame_person_x_list))
            self.current_frame_face_name_list[i] = self.last_frame_face_name_list[last_frame_num]

    def draw_note(self, img_rd):
        #  Add some info on windows
        cv2.putText(img_rd, f"{config['Text']['frame']}  " + str(self.frame_cnt),
                    (20, 100), self.font, 0.8, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img_rd, "FPS:    " + str(self.fps.__round__(2)),
                    (20, 130), self.font, 0.8, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img_rd, f"{config['Text']['faces']}  " + str(self.current_frame_face_cnt),
                    (20, 160), self.font, 0.8, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(img_rd, f"{self.quit_key.upper()}: {config['Text']['exit']}",
                    (20, 450), self.font, 0.8, (0, 255, 0), 1, cv2.LINE_AA)

    def alarm(self, img_rd):
        c_time = time.ctime()
        message = f"{config['Text']['alarm_text']}, {c_time}"
        playsound(config['Sound']['alarm'], block=False)
        path_tosave = f"{config['Directory']['captured']}{c_time}.jpg"
        cv2.imwrite(path_tosave, img_rd)
        tkinter.messagebox.showerror(config['Text']['unknown'], message=message)
        with client:
            client.send_file(config['Telegram']['receiver_nickname'], path_tosave, caption=message)
        self.faces.clear()

    #  Face detection and recognition wit OT from input video stream
    def process(self, stream):
        # 1.  Get faces known from "features.all.csv"
        if self.get_face_database():
            count1 = 0
            while stream.isOpened():
                count1 += 1
                self.frame_cnt += 1
                logging.debug("Frame " + str(self.frame_cnt) + " starts")

                flag, img_rd = stream.read()
                img_rd = imutils.resize(
                                        img_rd,
                                        width=int(config['Stream']['size_w']),
                                        height=int(config['Stream']['size_h'])
                                        )
                kk = cv2.waitKey(1)
                if eval(self.fps_formula[config['Stream']['fps_f']]):
                    # 2.  Detect faces for frame X
                    faces = detector(img_rd, 0)

                    # 3.  / Update cnt for faces in frames
                    self.last_frame_face_cnt = self.current_frame_face_cnt
                    self.current_frame_face_cnt = len(faces)

                    # 4.  Update the face name list in last frame
                    self.last_frame_face_name_list = self.current_frame_face_name_list[:]
                    self.faces += self.last_frame_face_name_list
                    if len(self.faces) > 2 and self.faces[-1] != config['Text']['unknown']:
                        self.faces.remove(self.faces[-2])

                    if len(self.faces) >= int(self.flist_lim):
                        percent = self.faces.count(config['Text']['unknown']) / (len(self.faces) / 100)
                        print(percent)
                        if percent >= int(self.pc_unknown):
                             self.alarm(img_rd)
                        self.faces.clear()

                    # 5.  update frame centroid list
                    self.last_frame_face_centroid_list = self.current_frame_face_centroid_list
                    self.current_frame_face_centroid_list = []

                    # 6.1  if cnt not changes
                    if (self.current_frame_face_cnt == self.last_frame_face_cnt) and (
                            self.reclassify_interval_cnt != self.reclassify_interval):
                        logging.debug("scene 1:  No face cnt changes in this frame!!!")
                        self.current_frame_face_position_list = []
                        if config['Text']['unknown'] in self.current_frame_face_name_list:
                            self.reclassify_interval_cnt += 1

                        if self.current_frame_face_cnt != 0:
                            for k, d in enumerate(faces):
                                self.current_frame_face_position_list.append(tuple(
                                    [faces[k].left(), int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4)]))
                                self.current_frame_face_centroid_list.append(
                                    [int(faces[k].left() + faces[k].right()) / 2,
                                     int(faces[k].top() + faces[k].bottom()) / 2])
                                img_rd = cv2.rectangle(img_rd,
                                                       tuple([d.left(), d.top()]),
                                                       tuple([d.right(), d.bottom()]),
                                                       (255, 255, 255), 2)
                        # Multi-faces in current frame, use centroid-tracker to track
                        if self.current_frame_face_cnt != 1:
                            self.centroid_tracker()
                        for i in range(self.current_frame_face_cnt):
                            # 6.2 Write names under ROI
                            img_rd = cv2.putText(img_rd, self.current_frame_face_name_list[i],
                                                 self.current_frame_face_position_list[i], self.font, 0.8, (0, 255, 255), 1,
                                                 cv2.LINE_AA)
                        self.draw_note(img_rd)

                    # 6.2  If cnt of faces changes, 0->1 or 1->0 or ...
                    else:
                        logging.debug("scene 2:  Faces cnt changes in this frame")
                        self.current_frame_face_position_list = []
                        self.current_frame_face_X_e_distance_list = []
                        self.current_frame_face_feature_list = []
                        self.reclassify_interval_cnt = 0

                        # 6.2.1  Face cnt decreases: 1->0, 2->1, ...
                        if self.current_frame_face_cnt == 0:
                            # clear list of names and features0.
                            self.current_frame_face_name_list = []

                        # 6.2.2 Face cnt increase: 0->1, 0->2, ..., 1->2, ...
                        else:
                            # scene 2.2 Get faces in this frame and do face recognition"
                            self.current_frame_face_name_list = []
                            for i in range(len(faces)):
                                shape = predictor(img_rd, faces[i])
                                self.current_frame_face_feature_list.append(
                                    face_reco_model.compute_face_descriptor(img_rd, shape))
                                self.current_frame_face_name_list.append(config['Text']['unknown'])

                            # 6.2.2.1  Traversal all the faces in the database
                            for k in range(len(faces)):
                                self.current_frame_face_centroid_list.append(
                                    [int(faces[k].left() + faces[k].right()) / 2,
                                     int(faces[k].top() + faces[k].bottom()) / 2])
                                self.current_frame_face_X_e_distance_list = []

                                # 6.2.2.2  Positions of faces captured
                                self.current_frame_face_position_list.append(tuple(
                                    [faces[k].left(), int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4)]))

                                # 6.2.2.3
                                # For every faces detected, compare the faces in the database
                                for i in range(len(self.face_features_known_list)):
                                    if str(self.face_features_known_list[i][0]) != '0.0':
                                        e_distance_tmp = self.return_euclidean_distance(
                                            self.current_frame_face_feature_list[k],
                                            self.face_features_known_list[i])
                                        self.current_frame_face_X_e_distance_list.append(e_distance_tmp)
                                    else:
                                        #  person_X
                                        self.current_frame_face_X_e_distance_list.append(999999999)

                                # 6.2.2.4  Find the one with minimum e distance
                                similar_person_num = self.current_frame_face_X_e_distance_list.index(
                                    min(self.current_frame_face_X_e_distance_list))
                                if min(self.current_frame_face_X_e_distance_list) < 0.4:
                                    self.current_frame_face_name_list[k] = self.face_name_known_list[similar_person_num]

                            # 7.  Add note on cv2 window
                            self.draw_note(img_rd)

                    # Press 'q' to exit
                    if kk == ord(self.quit_key):
                        break
                    self.update_fps()
                    # cv2.namedWindow(self.name_camera, 1)
                    cv2.imshow(f'camera', imutils.resize(img_rd,
                                                         width=int(config['Stream']['window_size_w']),
                                                         height=int(config['Stream']['window_size_h'])))

    def run(self, source):
        cap = cv2.VideoCapture(source)
        self.process(cap)
        cap.release()
        cv2.destroyAllWindows()


def main(source):
    # logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(level=logging.INFO)
    face_recogn_con = FaceRecognizer()
    face_recogn_con.run(source=source)


if __name__ == '__main__':
    input = 0  # 0 for webcam, 'rtsp://XXXX' - for rstp-stream, 'https://XXX' for ip-cameras
    main(input)
