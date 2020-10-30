from statistics import mean
import collections
import numpy as np
import dlib
from scipy.spatial import distance

import cv2
import os
import sys
sys.path.insert(1,"image_analysis")
from face_scoring.yoloface.utils import *

import time

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('image_analysis/face_scoring/shape_predictor_68_face_landmarks.dat')
facerec = dlib.face_recognition_model_v1('image_analysis/face_scoring/dlib_face_recognition_resnet_model_v1.dat')

yoloface_net = cv2.dnn.readNetFromDarknet(
    "image_analysis/face_scoring/yoloface/cfg/yolov3-face.cfg", 
    "image_analysis/face_scoring/yoloface/model-weights/yolov3-wider_16000.weights"
)
yoloface_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
yoloface_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
# yoloface_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
# yoloface_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

# def predict(image_path):
#     image = np.array(Image.open(image_path))
#     descriptors = []
    
#     bounding_boxes = detector(image)
#     face_sizes = [mean([bb.height(), bb.width()]) for bb in bounding_boxes]
#     if(len(face_sizes) == 0):
#         return ([], descriptors)
#     avg_bb_size = mean(face_sizes)
#     bb_threshold = avg_bb_size - 80
    
#     relevant_faces = (bb for bb in bounding_boxes if mean([bb.height(), bb.width()]) > bb_threshold)
    
#     bounding_boxes = []
#     for bounding_box in relevant_faces:
#         raw_landmarks = predictor(image, bounding_box)
#         landmarks = np.float32(list(map(lambda p: (p.x, p.y), raw_landmarks.parts())))

#         face_descriptor = facerec.compute_face_descriptor(image, raw_landmarks)
#         descriptors.append(face_descriptor)
#         bounding_boxes.append(bounding_box)
        
#     return (relevant_faces, descriptors, bounding_boxes)


def predict(image_path):
    image = cv2.imread(image_path)

    descriptors = []
    blob = cv2.dnn.blobFromImage(image, 1 / 255, (IMG_WIDTH, IMG_HEIGHT), [0, 0, 0], 1, crop=False)
    yoloface_net.setInput(blob)
    outs = yoloface_net.forward(get_outputs_names(yoloface_net))
    
    bounding_boxes = post_process(image, outs, CONF_THRESHOLD, NMS_THRESHOLD)
    bounding_boxes = [dlib.rectangle(left=x, top=y, right=x+w, bottom=y+h) for (x, y, w, h) in bounding_boxes]
    
    
#     bounding_boxes = detector(image)
    
    face_sizes = [mean([bb.height(), bb.width()]) for bb in bounding_boxes]
    if(len(face_sizes) == 0):
        return ([], descriptors)
    avg_bb_size = mean(face_sizes)
    bb_threshold = avg_bb_size - 80
    
    relevant_faces = (bb for bb in bounding_boxes) # if mean([bb.height(), bb.width()]) > bb_threshold)
    
    bounding_boxes = []
    for bounding_box in relevant_faces:
        raw_landmarks = predictor(image, bounding_box)
        landmarks = np.float32(list(map(lambda p: (p.x, p.y), raw_landmarks.parts())))

        face_descriptor = facerec.compute_face_descriptor(image, raw_landmarks)
        descriptors.append(face_descriptor)
        bounding_boxes.append(bounding_box)
        
    return (bounding_boxes, descriptors, bounding_boxes)

def process_output(bounding_boxes,image):
    descriptors = []
    bounding_boxes = [dlib.rectangle(left=x, top=y, right=x+w, bottom=y+h) for (x, y, w, h) in bounding_boxes]   
#     bounding_boxes = detector(image)
    face_sizes = [mean([bb.height(), bb.width()]) for bb in bounding_boxes]
    if(len(face_sizes) == 0):
        return ([], descriptors)
    avg_bb_size = mean(face_sizes)
    bb_threshold = avg_bb_size - 80
    
    relevant_faces = (bb for bb in bounding_boxes) # if mean([bb.height(), bb.width()]) > bb_threshold)
    
    bounding_boxes = []
    for bounding_box in relevant_faces:
        raw_landmarks = predictor(image, bounding_box)
        landmarks = np.float32(list(map(lambda p: (p.x, p.y), raw_landmarks.parts())))

        face_descriptor = facerec.compute_face_descriptor(image, raw_landmarks)
        descriptors.append(face_descriptor)
        bounding_boxes.append(bounding_box)
    return (bounding_boxes,descriptors,bounding_boxes)    
    
    

def predict_on_batch(images, batch_size):
    # create batch of images
    results = []
    counter = 0
    image_list = []
    for image in images:
        image_list.append(image)
        blob = cv2.dnn.blobFromImage(image, 1 / 255, (IMG_WIDTH, IMG_HEIGHT), [0, 0, 0], 1, crop=False)
        if counter == 0:
            sess_input = blob
        else:
            sess_input = np.concatenate((sess_input, blob), axis = 0)
        
        if counter == batch_size - 1:
            #predict on batch
            yoloface_net.setInput(sess_input)
            sess_result = yoloface_net.forward(get_outputs_names(yoloface_net))
            if sess_result[0].shape[0] == batch_size:
                for index in range(batch_size):
                    result = (sess_result[0][index],sess_result[1][index],sess_result[2][index])
                    bounding_boxes = post_process(image_list[index], result, CONF_THRESHOLD, NMS_THRESHOLD)
                    results.append(process_output(bounding_boxes,image_list[index]))
            else:
                bounding_boxes = post_process(image, sess_result, CONF_THRESHOLD, NMS_THRESHOLD)
                results.append(process_output(bounding_boxes,image))
            counter = 0
            image_list = []
        else:
            counter += 1
    if counter != 0:
        yoloface_net.setInput(sess_input)
        sess_result = yoloface_net.forward(get_outputs_names(yoloface_net))
        if sess_result[0].shape[0] < batch_size:
            for index in range(len(sess_result[0])):
                result = (sess_result[0][index],sess_result[1][index],sess_result[2][index])
                bounding_boxes = post_process(image_list[index], result, CONF_THRESHOLD, NMS_THRESHOLD)
                results.append(process_output(bounding_boxes,image_list[index]))
        else:
            bounding_boxes = post_process(image_list[0], result, CONF_THRESHOLD, NMS_THRESHOLD)
            results.append(process_output(bounding_boxes,image_list[0]))
    return results


def predict_images(images):
    
    results = predict_on_batch(images,32)
#     results = [predict(image) for image in images]
    descriptors = [result[1] for result in results]

    bounding_boxes = []
    for result in results:
        if len(result) > 2:
            bounding_boxes.append(result[2])
        else:
            bounding_boxes.append(0)
            
    return (descriptors,bounding_boxes)

def cluster(descriptors, parameter):
    
    descriptors_flat = []
    for descriptors_in_image in descriptors:
        for descriptor in descriptors_in_image:
            descriptors_flat.append(descriptor)
            
    labels = dlib.chinese_whispers_clustering(descriptors_flat, parameter)
    
    ordered_labels = []
    i = 0
    for descriptors_in_image in descriptors:
        labels_for_image = []
        for descriptor in descriptors_in_image:
            labels_for_image.append(labels[i])
            i += 1
        ordered_labels.append(labels_for_image)
    
    return ordered_labels

def calc_scores(labels):
    
    #counts more then once if face recognized multiple times in one image
    face_frequencies = collections.Counter([x for sublist in labels for x in sublist])

    scores = []
    for face_ids_in_image in labels:
        if len(face_ids_in_image) == 0:
            scores.append(0)
        else:
            score = 0
            for face_id in face_ids_in_image:
                freq = face_frequencies[face_id]
                if(freq >= 3):
                    face_score = 1 / freq
                    score = max(score, face_score)
            scores.append(score)
            
    if len(scores) > 0:
        max_score = max(scores)
    else:
        max_score = 0
    if max_score > 0:
        scores = np.array(scores) / max_score
    return scores

def calc_scores_with_parameters(labels,parameters=None):
    
    scores = []
    for face_ids_in_image in labels:
        if parameters == None:
            parameter = 1
        else:
            parameter = parameters[face_id]
        if len(face_ids_in_image) == 0:
            scores.append(0)
        else:
            score = 0
            for face_id in face_ids_in_image:
                score = score + parameter / 4
            score = min(1,score)
            scores.append(score)
            
    if len(scores) > 0:
        max_score = max(scores)
    else:
        max_score = 0
    #if max_score > 0:
        #scores = np.array(scores) / max_score
    return scores


def smile_score(image):
    bounding_boxes = detector(image)
    face_sizes = [mean([bb.height(), bb.width()]) for bb in bounding_boxes]
    if(len(face_sizes) == 0):
        return 0
    avg_bb_size = mean(face_sizes)
    bb_threshold = avg_bb_size - 80
    
    relevant_faces = (bb for bb in bounding_boxes if mean([bb.height(), bb.width()]) > bb_threshold)
    
    smiles = []
    
    # From https://medium.freecodecamp.org/smilfie-auto-capture-selfies-by-detecting-a-smile-using-opencv-and-python-8c5cfb6ec197
    for bounding_box in relevant_faces:
        landmarks = predictor(image, bounding_box)
        landmarks = np.float32(list(map(lambda p: (p.x, p.y), landmarks.parts())))
        
        left_vertical_distance = distance.euclidean(landmarks[51], landmarks[59])
        middle_vertical_distance = distance.euclidean(landmarks[52], landmarks[58])
        right_vertical_distance = distance.euclidean(landmarks[53], landmarks[57])
        horizontal_distance = distance.euclidean(landmarks[48], landmarks[55])
        
        mouth_aspect_ratio = (left_vertical_distance + middle_vertical_distance + right_vertical_distance) / (3 * horizontal_distance)
        smiles.append(distance.euclidean(mouth_aspect_ratio, 0.34))
        
    if len(smiles) == 0:
        return 0
    
    return mean(smiles)



