from flask import redirect, render_template, url_for, request
from app import app, db
import os
from utils import reset_keras
import tensorflow as tf

from DatabaseAccess import Image,Tag
from image_analysis.aadb_predict import predict_aesthetic
from image_analysis.tag_predict import predict_tag


## Home
@app.route('/')
def home_page():
    return render_template('home_page.html')

## Upload
@app.route('/upload')
def upload_page():
    return render_template('upload_page.html')


import werkzeug
@app.route('/classify_upload', methods=['GET', 'POST'])
def classify_upload():
    image_file = request.files['file']
    image = Image()
    db.save_object(image)
    image_path = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
    image_file.save(image_path)
    aesthetic_score = predict_aesthetic(image_path)
    tags = predict_tag(image_path)
    for tag,score in tags:
        if score > 0.3:
            db.save_object(Tag(image.id,tag,score))
    db.updateImageAesthetic(image.id,round(aesthetic_score,2))
    return "True"

import base64
@app.route("/show_images", methods=['GET', 'POST'])
def show_images_page():
    if request.method == 'GET':
        images = db.get_image_objects()
        image_srcs = []
        for image in images:
            image_path = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
            image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
            image_tags = db.getTags(image.id)
            image_srcs.append((image_src,image.id,image.aesthetic_score,image_tags,image.selected))
        image_srcs.sort(key=lambda tup: tup[2], reverse=True)
        
        return render_template('show_images_page.html',image_srcs=image_srcs)
    else:
        image_id = int(request.values.get('image_id'))
        selected = request.values.get('selected') != "true"
        print(request.values.get('selected'),selected)
        db.updateImageSelected(image_id,selected)
        return ""


@app.route("/tags", methods=['GET','POST'])
def tags_page():
    if request.method == 'GET':
        tag_occurences = db.getTagOccurences()
        print(tag_occurences)
        return render_template('cluster_page.html', tag_occurences=tag_occurences)
    else:
        tag_name = request.values.get('tag')
        images = db.getImagesWithTag(tag_name)
        image_srcs = []
        for image in images:
            image_path = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
            image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
            image_tags = db.getTags(image.id)
            image_srcs.append((image_src,image.id,image.aesthetic_score,image_tags,image.selected))
        return render_template('response_images.html',image_srcs=image_srcs)
