import time
from datetime import datetime
from os import walk, path
import math
import exifread
from PIL import Image, ImageOps, ExifTags
import matplotlib.pyplot as plt
import numpy as np
import ntpath
from fix_orientation import fix_orientation
import piexif
from aesthetics_calculation import Aesthetic_score

def rotate_jpeg(filename):
    img = Image.open(filename)
    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])

        if piexif.ImageIFD.Orientation in exif_dict["0th"]:
            orientation = exif_dict["0th"].pop(piexif.ImageIFD.Orientation)
            exif_bytes = piexif.dump(exif_dict)

            if orientation == 2:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                img = img.rotate(180)
            elif orientation == 4:
                img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 5:
                img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 6:
                img = img.rotate(-90, expand=True)
            elif orientation == 7:
                img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 8:
                img = img.rotate(90, expand=True)

            img.save(filename, exif=exif_bytes)
        else:
            print("No Exif data for image")

def add_border_to_image(input_image, border, color=0):
    img = Image.open(input_image)
 
    if isinstance(border, int) or isinstance(border, tuple):
        bimg = ImageOps.expand(img, border=border, fill=color)
    else:
        raise RuntimeError('Border is not an integer or tuple!')
 
    return bimg


def show_images(images, cols = 1, titles = None, target_size = None):
    """Display a list of images in a single figure with matplotlib.
    
    Parameters
    ---------
    images: List of np.arrays compatible with plt.imshow.
    
    cols (Default = 1): Number of columns in figure (number of rows is set to np.ceil(n_images/float(cols))).
    
    titles: List of titles corresponding to each image. Must have the same length as titles.
    """
    
    generic_title = False
    assert((titles is None)or (len(images) == len(titles)))
    n_images = len(images)
    if titles is None: 
        titles = ['Image (%d)' % i for i in range(1,n_images + 1)]
        generic_title = True
        
    best_image = ""
    top_score = 0
    
    if type(titles[0]) is Aesthetic_score:
        for n, (image, title) in enumerate(zip(images, titles)):
            if title.score >= top_score:
                top_score = title.score
                best_image = image
                
    fig = plt.figure()
    for n, (image, title) in enumerate(zip(images, titles)):
           
        a = fig.add_subplot(cols, np.ceil(n_images/float(cols)), n + 1)
        
        '''If scores are provides as titles for the images, we mark the best with a blue border'''
        if image == best_image:
            
            img = add_border_to_image(image, 100, color=(33, 243, 255))
        
        else:
            img = Image.open(image)
        
        if target_size != None:
            img = img.resize(target_size)
        
        img = np.asarray(img)
        
        if img.ndim == 2:
            plt.gray()
        plt.axis("off")
        plt.imshow(img)
        if generic_title == False and type(title) is str:
            title = ntpath.basename(title)
        elif type(title) is Aesthetic_score:
            title = title.score
        a.set_title(title)
        
    fig.set_size_inches(np.array(fig.get_size_inches()) * n_images)
    plt.show()
    plt.close()


def transform_date_taken_to_timestamp(date_taken_string):
    dt_obj = datetime.strptime(date_taken_string, '%Y:%m:%d %H:%M:%S')
    return dt_obj.timestamp() * 1000

def get_date_taken(path):
    return Image.open(path)._getexif()[36867]

def get_timestamp_difference(image_a, image_b):
    tags_image_1 = {}
    tags_image_2 = {}
    with open(image_a, 'rb') as f:
        tags_image_1 = exifread.process_file(f, details=False)
    with open(image_b, 'rb') as f:
        tags_image_2 = exifread.process_file(f, details=False)
    
    if "Image DateTime" in tags_image_1.keys() and "Image DateTime" in tags_image_2.keys():
        datetime_1 = str(tags_image_1["Image DateTime"]).split(".")[0]
        datetime_2 = str(tags_image_2["Image DateTime"]).split(".")[0]
        
        millisec_1 = transform_date_taken_to_timestamp(datetime_1)
        millisec_2 = transform_date_taken_to_timestamp(datetime_2)

        return abs(millisec_2 - millisec_1)
    
    elif get_date_taken(image_a) is not None and get_date_taken(image_b) is not None:
        return abs(transform_date_taken_to_timestamp(get_date_taken(image_a)) - transform_date_taken_to_timestamp(get_date_taken(image_b)))
        
    else:
        print("No timestamp in image(s)")
        return math.inf

def clear_rotation(filepath):
    try:
        image=Image.open(filepath)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif=dict(image._getexif().items())

        if exif[orientation] == 3:
            image=image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image=image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image=image.rotate(90, expand=True)
        
        image.info["exif"] = 0
        image.save(filepath, exif=image.info["exif"])

    except (AttributeError, KeyError, IndexError):
        print("No Exif data found")
        pass