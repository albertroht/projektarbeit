#imports
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '../')
sys.path.insert(1, '/notebooks/Projektarbeit/ndd')

import os
import importlib
os.environ['CUDA_VISIBLE_DEVICES'] = "0"
import numpy as np
import pandas as pd
pd.set_option('display.max_colwidth', -1)

from keras.applications.mobilenet import MobileNet, preprocess_input
from keras.models import Model
from keras.preprocessing.image import load_img
from os import walk, path

import image_clustering

import itertools

import importlib
from image_clustering import get_similarities_for_filenames

import os
import pickle
import time

import glob


# Returns a list of image tuples that are temporally close to each other
def get_temporally_close_image_tuples(timestamp_file_dict, seconds_distance = 5):
    temporally_close_image_tuples = []
    
    for combo in combinations:
        timestamp_image_A = timestamp_file_dict[combo[0]]
        timestamp_image_B = timestamp_file_dict[combo[1]]
        
        # Get time-distance between images
        ms_time_difference = abs(timestamp_image_A - timestamp_image_B)
        print(ms_time_difference)

        if ms_time_difference <= (seconds_distance * 1000):
            potential_duplicate = {"filename_1" : combo[0], "filename_2" : combo[1]}
            temporally_close_image_tuples.append(potential_duplicate)
    
    return temporally_close_image_tuples

def get_cluster_list(image_paths, similarity_rate, cluster_list_path=None,
                     save_path=None, batch_size=16):
        
    from ndd_utils import get_date_taken, transform_date_taken_to_timestamp
    # Creating a list of dicts with each image filename and its timestamp for later reference
    timestamp_file_dict = {}
    image_paths_with_timestamp = []    

    for image_path in image_paths:
        try:
            timestamp_file_dict[image_path] = transform_date_taken_to_timestamp(get_date_taken(image_path))
            image_paths_with_timestamp.append(image_path)    
        except:
            pass

    global combinations
    combinations = itertools.combinations(image_paths_with_timestamp, 2)

    print("Found %s images" % len(timestamp_file_dict))
    temporally_close_image_tuples = get_temporally_close_image_tuples(timestamp_file_dict)
    print(temporally_close_image_tuples)


    pd.DataFrame(temporally_close_image_tuples)

    # Creating a list where every image filename is only present once (so that the vector-transformation only have to be made once per image)
    filenames_to_evaluate = []

    for potential_duplicate in temporally_close_image_tuples:
        if potential_duplicate["filename_1"] not in filenames_to_evaluate:
            filenames_to_evaluate.append(potential_duplicate["filename_1"])
        if potential_duplicate["filename_2"] not in filenames_to_evaluate:
            filenames_to_evaluate.append(potential_duplicate["filename_2"])

    
    # load the pretrained model
    model = MobileNet(input_shape=(224, 224, 3), weights='imagenet', include_top=True)
    # Remove the last 5 layers to get to the pooling layer
    for i in range(0, 5):
        model.layers.pop()

    # Create a new model instance with newly defined output(s)
    new_model = Model(inputs=model.input, outputs=[model.layers[-1].output])


    results = []
    counter = 0
    image_list = []
    for filename in filenames_to_evaluate:
        image_list.append(filename)

        image = load_img(filename, target_size=(224, 224))
        image = preprocess_input(np.array(image))
        img_array = np.expand_dims(image, axis=0)

        if counter == 0:
            sess_input = img_array
        else:
            sess_input = np.concatenate((sess_input,img_array), axis = 0)

        if counter == batch_size - 1:
            sess_result = new_model.predict(sess_input,batch_size=16)
            for index,result in enumerate(sess_result):
                filename_imagevector_dict = {"image_filename": image_list[index],
                                     "vector" : result}
                results.append(filename_imagevector_dict.copy())
            counter = 0
            image_list = []
        else:
            counter += 1
    if counter != 0:
        sess_result = new_model.predict(sess_input)
        for index,result in enumerate(sess_result):
            filename_imagevector_dict = {"image_filename": image_list[index],
                                 "vector" : result}
            results.append(filename_imagevector_dict.copy())


    from utils import reset_keras

    reset_keras(new_model)

    results = pd.DataFrame(results)

    similarities_df = pd.DataFrame(get_similarities_for_filenames(results, filenames_to_evaluate,similarity_rate))
    print(similarities_df)
    try:
        sorted_values = similarities_df.sort_values(by=["similarity"], ascending=False).reset_index(drop=True)
    except:
        return []
#         sorted_values.to_csv("sim_test.csv", decimal=".", sep=";", index=False)
    cluster_list = image_clustering.create_image_clusters(sorted_values, results)


    if cluster_list_path:
        with open(cluster_list_path,"wb") as fp:
            pickle.dump(cluster_list ,fp)


    return cluster_list