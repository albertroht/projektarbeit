from statistics import mean
import collections
import numpy as np
import dlib
from scipy.spatial import distance

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('/notebooks/graph_creation_and_ACO/scripts/face_scoring/shape_predictor_68_face_landmarks.dat')
facerec = dlib.face_recognition_model_v1('/notebooks/graph_creation_and_ACO/scripts/face_scoring/dlib_face_recognition_resnet_model_v1.dat')

def predict(image):
    descriptors = []
    
    bounding_boxes = detector(image)
    face_sizes = [mean([bb.height(), bb.width()]) for bb in bounding_boxes]
    if(len(face_sizes) == 0):
        return ([], descriptors)
    avg_bb_size = mean(face_sizes)
    bb_threshold = avg_bb_size - 80
    
    relevant_faces = (bb for bb in bounding_boxes if mean([bb.height(), bb.width()]) > bb_threshold)
    
    bounding_boxes = []
    for bounding_box in relevant_faces:
        raw_landmarks = predictor(image, bounding_box)
        landmarks = np.float32(list(map(lambda p: (p.x, p.y), raw_landmarks.parts())))

        face_descriptor = facerec.compute_face_descriptor(image, raw_landmarks)
        descriptors.append(face_descriptor)
        bounding_boxes.append(bounding_box)
        
    return (relevant_faces, descriptors, bounding_boxes)

def predict_images(images):
    results = [predict(image) for image in images]
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

def calc_scores_with_parameters(labels,parameters):

    scores = []
    for face_ids_in_image in labels:
        if len(face_ids_in_image) == 0:
            scores.append(0)
        else:
            score = 0
            for face_id in face_ids_in_image:
                score = score + parameters[face_id] / 4
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