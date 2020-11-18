from flask import redirect, render_template, url_for, request
from app import app, db
import os
import time
from DatabaseAccess import Image, Tag, NearDuplicateCluster

import werkzeug
import base64

from io import StringIO
from PIL import Image as PIL_Image

import numpy as np

def save_resize_uploaded_image(buf,save_path):
    image = PIL_Image.open(buf)
    maxSize = (240, 240)
    image.thumbnail(maxSize)
#     resizedImageFile = StringIO()
    try:
        image.save(save_path,'JPEG')
    except:
        image.save(save_path,'PNG')
#     resizedImageFile.seek(0)    # So that the next read starts at the beginning
    return 


@app.route('/')
def home_page():
    return render_template('home_page.html')


@app.route('/upload', methods=['GET','POST'])
def upload_page():
    if request.method == 'GET':
        return render_template('upload_page.html')
    else:
        try:
            image_file = request.files['file']
            image = Image()
            db.save_object(image)
            image_path = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
            image_file.save(image_path)
            try:
                date = PIL_Image.open(image_path)._getexif()[36867]        
            except:
                date = "None"
            db.updateImageDate(image.id,date)
            image_path_resized = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
            save_resize_uploaded_image(image_file,image_path_resized)
        except:
            pass
        return "True"
                
        
    
    
@app.route('/images', methods = ['POST','GET'])
def images_page():
    if request.method == 'GET':
        images = db.get_image_objects()
        image_srcs = []
        for image in images:
            try:
                image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
                image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
                # test with date == None
                print(image.date)
                if image.date == None:
                    image_date = "None"
                else:
                    image_date = image.date
                image_srcs.append((image_src,image.id,image_date,image.selected))
            except:
                print("image %s not found" % image.id)
        image_srcs.sort(key=lambda tup: tup[2])
        
        return render_template('images_page.html',image_srcs=image_srcs)
    else:
        task = request.values.get("task")
        if task == "delete_all":
            db.delete_all()
        elif task == "select_all":
            images = db.get_image_objects()
            for image in images:
                if image.selected == False:
                    db.updateImageSelected(image.id,True)
        elif task == "unselect_all":
            images = db.get_image_objects()
            for image in images:
                if image.selected == True:
                    db.updateImageSelected(image.id,False)
        elif task == "delete_unselected":
            images = db.get_image_objects()
            for image in images:
                if image.selected == False:
                    db.delete_image(image.id)
        return ""
    
@app.route("/aesthetics", methods=['GET', 'POST'])
def aesthetics_page():
    if request.method == 'GET':
        images = [image for image in db.get_image_objects() if image.aesthetic_score != None]
        image_srcs = []
        for image in images:
            image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
            image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
            image_srcs.append((image_src,image.id,round(image.aesthetic_score,2),image.selected))
        image_srcs.sort(key=lambda tup: tup[2], reverse=True)
        
        return render_template('aesthetics_page.html',image_srcs=image_srcs)
    else:
        images = [image for image in db.get_image_objects() if image.aesthetic_score == None]
        from utils import reset_keras
        import tensorflow as tf
        reset_keras()
        from image_analysis.aadb_predict import predict_aesthetic
        
        for image in images:
            image_path = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
            try:
                aesthetic_score = predict_aesthetic(image_path)
                print(aesthetic_score)
                db.updateImageAesthetic(image.id,aesthetic_score)
            except:
                pass
        return ""
    
@app.route("/convenience", methods=['GET', 'POST'])
def convenience_page():
    if request.method == 'GET':
        images = [image for image in db.get_image_objects() if image.convenience_score != None and image.convenience_score > 0.95]
        image_srcs = []
        for image in images:
            if image.convenience_score != None:
                image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
                image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
                image_srcs.append((image_src,image.id,image.selected))
        image_srcs.sort(key=lambda tup: tup[2], reverse=True)
        return render_template('convenience_page.html',image_srcs=image_srcs)
    else:
        task = request.values.get("task")
        if task == "delete_unselected_convenient_images":
            db.delete_unselected_convenient_images()
            return ""
        elif task == "convenience_start":
            images = [image for image in db.get_image_objects() if image.convenience_score == None]
            from keras import models
            from keras import layers
            from keras.preprocessing.image import load_img
            from utils import reset_keras
            reset_keras()
            model = models.Sequential()
            model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(150, 150, 3)))
            model.add(layers.MaxPooling2D((2, 2)))
            model.add(layers.Conv2D(64, (3, 3), activation='relu'))
            model.add(layers.MaxPooling2D((2, 2)))
            model.add(layers.Conv2D(128, (3, 3), activation='relu'))
            model.add(layers.MaxPooling2D((2, 2)))
            model.add(layers.Conv2D(128, (3, 3), activation='relu'))
            model.add(layers.MaxPooling2D((2, 2)))
            model.add(layers.Flatten())
            model.add(layers.Dense(64, activation='relu'))
            model.add(layers.Dense(1, activation='sigmoid'))
            model.load_weights('convenience_model.h5')

            for image in images:
                image_path = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
                img = load_img(image_path, target_size=(150, 150))
                img = np.array(img) / 255
                img_array = np.expand_dims(img, axis=0)
                convenience_score = model.predict(img_array)
                db.updateImageConvenience(image.id,convenience_score)
            reset_keras()

            return ""

@app.route("/faces", methods=['GET', 'POST'])
def faces_page():
    if request.method == 'GET':
        images = [image for image in db.get_image_objects() if image.faces_count != None]
        image_srcs = []
        for image in [image for image in images if image.faces_count > 0]:
            image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
            image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
            image_srcs.append((image_src,image.id,image.faces_count,image.selected))
        image_srcs.sort(key=lambda tup: tup[2], reverse=True)
        
        return render_template('faces_page.html',image_srcs=image_srcs)
    else:
        from mtcnn import MTCNN
        from matplotlib import pyplot
        from utils import reset_keras
        reset_keras()
        
        model = MTCNN()
        images = [image for image in db.get_image_objects() if image.faces_count == None]
#         images = [image for image in db.get_image_objects()]
        for image in images:
            filename = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
            pixels = pyplot.imread(filename)
            faces = model.detect_faces(pixels)
            confident_faces = [face for face in faces if face['confidence'] > 0.9]
            db.updateFacesCount(image.id,len(confident_faces))
        return ""
        reset_keras()



@app.route("/tags", methods=['GET','POST'])
def tags_page():
    if request.method == 'GET':
        tag_occurences = db.getTagOccurences()
        return render_template('tags_page.html', tag_occurences=tag_occurences)
    elif request.values.get("task") == "analyze_for_tags":
        images_to_analyze = [image for image in db.get_image_objects() if db.getTags(image.id) == []]
        print(len(images_to_analyze))
        from image_analysis.tag_predict import predict_multiple_images
        image_paths = []
        for image in images_to_analyze:
            image_path = os.path.join("/notebooks/datasets/projektarbeit/",str(image.id))
            image_paths.append((image_path,image.id))
        
        map_of_tags = predict_multiple_images(image_paths)
        for image_id in map_of_tags.keys():
            tags = map_of_tags[image_id]
            if tags == []:
                db.save_object(Tag(image_id,"None",1))
            else:
                for tag,score in tags:
                    if score > 0.3:
                        db.save_object(Tag(image_id,tag,score))
        return ""
    else:
        tag_name = request.values.get('tag')
        images = db.getImagesWithTag(tag_name)
        image_srcs = []
        for image in images:
            image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
            image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
            image_tags = db.getTags(image.id)
            image_tags_map_string = ""
            image_tags_map = {}
            for tag,confidence in image_tags:
                image_tags_map[tag] = confidence
                image_tags_map_string += "%s: %s \n" % (tag, confidence)
            
            image_srcs.append((image_src, image.id, image_tags_map, image_tags_map_string, image.selected))
            image_srcs.sort(key=lambda tup: tup[2][tag_name],reverse=True)
        return render_template('tag_response.html',image_srcs=image_srcs)
    
@app.route("/ndd",methods=['GET','POST'])
def ndd_page():
    if request.method == 'GET':
        cluster_list = db.getAllCluster()
        cluster_list_srcs = []
        for cluster in cluster_list:
            cluster_list_srcs_object = []
            for image_id in cluster.image_ids.split("/"):
                selected = db.getSelected(image_id)
                image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",image_id)
                image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
                cluster_list_srcs_object.append((image_src,os.path.basename(image_path),selected))
            cluster_list_srcs.append(cluster_list_srcs_object)
        return render_template('ndd_page.html',cluster_list=cluster_list_srcs)
    elif request.values.get("task") == "delete_duplicates":
        cluster_list = db.getAllCluster()
        for cluster in cluster_list:
            for image_id in cluster.image_ids.split("/"):
                selected = db.getSelected(image_id)
                if selected != True:
                    db.delete_image(image_id)

        return ""
    elif request.values.get("task") == "ndd_start":
        from utils import reset_keras
        import tensorflow as tf
        from ndd import ndd
        reset_keras()

        image_paths = ["/notebooks/datasets/projektarbeit/" + str(image.id) for image in db.get_image_objects()]
        
        similarity_rate = 0.55
        cluster = ndd.get_cluster_list(image_paths,similarity_rate)
        
        cluster_list = []
        for c in cluster:
            cluster_list_object = []
            cluster_list_object.append(c.index_image_path)
            for image_path in c.similar_images:
                cluster_list_object.append(image_path)
            cluster_list.append(cluster_list_object)
        
        db.dropNearDuplicateClusterTable()
        for cluster in cluster_list:
            cluster_image_ids = [os.path.basename(image_path) for image_path in cluster]
            print('/'.join(cluster_image_ids))
            db.save_object(NearDuplicateCluster('/'.join(cluster_image_ids)))
        reset_keras()

        return ""
    
    

@app.route("/select",methods=['POST'])
def select_image():
    image_id = int(request.values.get('image_id'))
    selected = request.values.get('selected') != "true"
    print(request.values.get('selected'),selected)
    db.updateImageSelected(image_id,selected)
    return ""
