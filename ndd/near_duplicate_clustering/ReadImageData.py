from GalleryImage import GalleryImage
import glob
from PIL import Image
import pandas as pd
import datetime

def get_date_taken(img):
    try:
        exif_data = img._getexif()
        if 36867 in exif_data:
            image_timestamp = exif_data[36867]
            return image_timestamp
        else:
            return 0
    except AttributeError:
        return 0
    except TypeError:
        return 0

def transform_datetime_to_timestamp(date_time):
    timestamp = datetime.datetime.strptime(date_time, "%Y:%m:%d %H:%M:%S").timestamp()

    return int(timestamp)

def get_list_of_timestamps(list_of_images):
    # Transforming the datetime format into a Unix timestamp format
    timestamp_list = []

    for image in list_of_images:
        timestamp = image.getData()["timestamp"]
        timestamp_list.append(timestamp)

    return timestamp_list

def readImagesFromDirectory(directory_name):
    list_of_images = []

    for filename in sorted(glob.glob(directory_name + '*.jpg')):  # assuming jpg
        img = Image.open(filename)
        date_time = get_date_taken(img)
        timestamp = transform_datetime_to_timestamp(str(date_time))
        gallery_image = GalleryImage(filename, timestamp)
        list_of_images.append(gallery_image)

    return list_of_images


def readImagesFromCSV(filename):
    read_df = pd.read_csv(filename, decimal=".", sep=";", index_col=False)

    list_of_images = []

    for i in range(read_df.shape[0]):
        date_time = read_df.iloc[i][1]
        timestamp = transform_datetime_to_timestamp(str(date_time))
        single_image = GalleryImage(read_df.iloc[i][2], timestamp)
        list_of_images.append(single_image)

    return list_of_images