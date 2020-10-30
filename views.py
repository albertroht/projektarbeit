from flask import redirect, render_template, url_for, request
from app import app, db
import os

from DatabaseAccess import Image, Tag, NearDuplicateCluster

import werkzeug
import base64


def save_resize_uploaded_image(buf,save_path):
    from io import StringIO
    from PIL import Image

    image = Image.open(buf)

    maxSize = (240, 240)
    image.thumbnail(maxSize)

    # Turn back into file-like object
#     resizedImageFile = StringIO()
    image.save(save_path , 'JPEG')
#     resizedImageFile.seek(0)    # So that the next read starts at the beginning

    return 


## Home
@app.route('/')
def home_page():
    return render_template('home_page.html')


## TODO: put classify_upload into #
## Upload
@app.route('/upload', methods=['GET','POST'])
def upload_page():
    if request.method == 'GET':
        return render_template('upload_page.html')
    else:

#         from image_analysis.face_scoring import face_cluster
        image_file = request.files['file']
        image = Image()
        db.save_object(image)
        print(image.id)
        image_path = os.path.join("/notebooks/datasets/projektarbeit",str(image.id))
        image_file.save(image_path)
        image_path_resized = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))

        save_resize_uploaded_image(image_file,image_path_resized)



        ## face_analysis
    #     face_count = len(face_cluster.predict(image_path)[0])
    #     print("found %s faces"%face_count)
    #     db.updateFacesCount(image.id,face_count)

        return "True"
        
@app.route("/aesthetics", methods=['GET', 'POST'])
def aesthetics_page():
    if request.method == 'GET':
        images = db.get_image_objects()
        image_srcs = []
        for image in images:
            if image.aesthetic_score != None:
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
            aesthetic_score = predict_aesthetic(image_path)
            db.updateImageAesthetic(image.id,aesthetic_score)
            
        images = db.get_image_objects()
        image_srcs = []
        for image in images:
            if image.aesthetic_score != None:
                image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
                image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
                image_srcs.append((image_src,image.id,round(image.aesthetic_score,2),image.selected))
        image_srcs.sort(key=lambda tup: tup[2], reverse=True)
        
        return render_template('aesthetics_response.html',image_srcs=image_srcs)
    
@app.route("/select",methods=['POST'])
def select_image():
    image_id = int(request.values.get('image_id'))
    selected = request.values.get('selected') != "true"
    print(request.values.get('selected'),selected)
    db.updateImageSelected(image_id,selected)
    return ""

@app.route("/faces", methods=['GET', 'POST'])
def faces_page():
    if request.method == 'GET':
        images = db.get_image_objects()
        image_srcs = []
        for image in images:
            image_path = os.path.join("/notebooks/datasets/projektarbeit/rezised",str(image.id))
            image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
            image_tags = db.getTags(image.id)
            image_srcs.append((image_src,image.id,image.faces_count,image_tags,image.selected))
        image_srcs.sort(key=lambda tup: tup[2], reverse=True)
        
        return render_template('faces_page.html',image_srcs=image_srcs)
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
        return render_template('tags_page.html', tag_occurences=tag_occurences)
    else:
        tag_name = request.values.get('tag')
        images = db.getImagesWithTag(tag_name)
        image_srcs = []
        for image in images:
            image_path = os.path.join("/notebooks/datasets/projektarbeit/resized",str(image.id))
            image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
            image_tags = db.getTags(image.id)
            image_tags_map = {}
            for tag,confidence in image_tags:
                image_tags_map[tag] = confidence
            image_srcs.append((image_src,image.id,image.aesthetic_score,image_tags_map,image.selected))
            ## sort by confidence or aesthetic score?
            image_srcs.sort(key=lambda tup: tup[3][tag_name],reverse=True)
        return render_template('tag_response.html',image_srcs=image_srcs)

@app.route("/analyze_for_tags",methods=['POST'])
def analyze_for_tags():
    images_to_analyze = [image for image in db.get_image_objects() if db.getTags(image.id) == []]
    from image_analysis.tag_predict import predict_tag
    for image in images_to_analyze:
        image_path = os.path.join("/notebooks/datasets/projektarbeit/",str(image.id))
        tags = predict_tag(image_path)
        for tag,score in tags:
            if score > 0.3:
                db.save_object(Tag(image.id,tag,score))
    return ""
    
@app.route("/ndd",methods=['GET','POST'])
def ndd_page():
    if request.method == 'GET':
#         try:
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
#         except:
#             return render_template('ndd_page.html')
    else:
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
        
        cluster_list_srcs = []
        for cluster in cluster_list:
            cluster_list_srcs_object = []
            cluster = [os.path.join("/notebooks/datasets/projektarbeit/resized/",os.path.basename(image_path)) for image_path in cluster]
            for image_path in cluster:
                selected = db.getSelected(os.path.basename(image_path))
                image_src = 'data:image/png;base64,' + base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')
                cluster_list_srcs_object.append((image_src,os.path.basename(image_path),selected))
            cluster_list_srcs.append(cluster_list_srcs_object)
        
        reset_keras()
        return render_template('ndd_response.html',cluster_list=cluster_list_srcs)
    
@app.route("/delete_duplicates",methods=['POST'])
def delete_duplicates():
    cluster_list = db.getAllCluster()
    for cluster in cluster_list:
        for image_id in cluster.image_ids.split("/"):
            selected = db.getSelected(image_id)
            if selected != True:
                db.delete_image(image_id)
    
    return ""
    