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