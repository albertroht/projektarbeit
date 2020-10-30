from keras import backend as K
from keras.models import load_model
from keras.preprocessing.image import load_img, img_to_array
from keras.applications.mobilenet import preprocess_input
from keras.activations import relu
import numpy as np

'''To check which image to "keep" from the duplicate cluster we predict the aesthetics score with the deep learning model'''

def earth_mover_loss(y_true, y_pred):
    cdf_ytrue = K.cumsum(y_true, axis=-1)
    cdf_ypred = K.cumsum(y_pred, axis=-1)
    samplewise_emd = K.sqrt(K.mean(K.square(K.abs(cdf_ytrue - cdf_ypred)), axis=-1))
    return K.mean(samplewise_emd)

def mean_score(scores):
    si = np.arange(1, 11, 1)
    mean = np.sum(scores * si)
    return Aesthetic_score(mean)


class Aesthetic_score(object):
    
    def __init__(self, score):
        self.score = score

class Aesthetic_model(object):
    
    model = load_model("ndd/image_vectors/mobilenetV2_aesthetics_trained.h5", 
                             custom_objects={"relu6" : relu, 
                                             "earth_mover_loss" : earth_mover_loss})
    
    
    def get_model_score(self, image_filename):
        img = load_img(image_filename, target_size=(224, 224))

        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        x = preprocess_input(img_array)
    
        return mean_score(self.model.predict(x))
    
    


    
