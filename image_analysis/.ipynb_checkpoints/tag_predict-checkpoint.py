import sys
import numpy as np
import pandas as pd
import os
import math
import PIL
import glob
from os import path
import pickle
# from keras.applications.mobilenet_v2 import preprocess_input
# from keras.preprocessing.image import load_img, img_to_array

#os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import tensorflow as tf



import time
checkpoint_path = "/notebooks/Projektarbeit/image_analysis/oidv2/oidv2-resnet_v1_101.ckpt"
labelmap = "/notebooks/Projektarbeit/image_analysis/oidv2/classes-trainable.txt"
class_descriptions = "/notebooks/Projektarbeit/image_analysis/oidv2/class-descriptions.csv"

def load_label_map(labelmap_path, class_description_path):
    labelmap = [line.rstrip() for line in tf.gfile.GFile(labelmap_path)]

    label_dict = {}
    for line in tf.gfile.GFile(class_description_path):
        words = [word.strip(' "\n') for word in line.split(',', 1)]
        label_dict[words[0]] = words[1]

    return labelmap, label_dict

labelmap, label_dict = load_label_map(labelmap, class_descriptions)

def predict_tag(filename):
   
    with tf.Session() as sess:
        saver = tf.train.import_meta_graph(checkpoint_path + ".meta")
        saver.restore(sess, checkpoint_path)
        graph = tf.get_default_graph()

        input_operation = graph.get_operation_by_name('input_values')
        output_operation = graph.get_operation_by_name('multi_predictions')

        
        list_of_tags = []

        img = tf.gfile.FastGFile(filename, 'rb').read()
        #img_array = np.asarray(img)
        predictions_eval = sess.run(output_operation.outputs[0], {input_operation.outputs[0] : [img]})

        top_k = predictions_eval.argsort()[::-1]

        labels=''
        for idx in top_k:
            mid = labelmap[idx]
            display_name = label_dict[mid]
            score = predictions_eval[idx]
            if score >= 0.3:
                # Creating list of database objects
                list_of_tags.append((display_name,round(score,2)))

        return list_of_tags
    
def predict_multiple_images(filenames):
     with tf.Session() as sess:
        saver = tf.train.import_meta_graph(checkpoint_path + ".meta")
        saver.restore(sess, checkpoint_path)
        graph = tf.get_default_graph()

        input_operation = graph.get_operation_by_name('input_values')
        output_operation = graph.get_operation_by_name('multi_predictions')

        map_of_tags = dict()
    
        for filename, image_id in filenames: 
            print(image_id)
            list_of_tags = []

            img = tf.gfile.FastGFile(filename, 'rb').read()
            #img_array = np.asarray(img)
            predictions_eval = sess.run(output_operation.outputs[0], {input_operation.outputs[0] : [img]})

            top_k = predictions_eval.argsort()[::-1]

            labels=''
            for idx in top_k:
                mid = labelmap[idx]
                display_name = label_dict[mid]
                score = predictions_eval[idx]
                if score >= 0.3:
                    # Creating list of database objects
                    list_of_tags.append((display_name,round(score,2)))

            map_of_tags[image_id] = list_of_tags
            print(list_of_tags)

        return map_of_tags