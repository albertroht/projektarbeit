import numpy as np
import pandas as pd
import os
import cv2
from torch.utils.data import DataLoader, Dataset
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F
from torchvision import models, transforms
from collections import OrderedDict
from tqdm import tqdm
import pprint
import random
import torch
import sys
sys.path.append("../datasets/deep-photo-aesthetics")
sys.path.append("../datasets/deep-photo-aesthetics/utils")

use_cuda = torch.cuda.is_available()

from model.resnet_FT import ResNetGAPFeatures as Net
from data import read_data, create_dataloader, AestheticsDataset

# create model
save_path = "../datasets/deep-photo-aesthetics/checkpoint/001" 
checkpoint = "epoch_7.loss_0.36878775069165487.pth"
resnet = models.resnet50(pretrained=True)
net = Net(resnet, n_features=12)
if use_cuda:
    resnet = resnet.cuda()
    net = net.cuda()
    net.load_state_dict(torch.load("%s/%s"%(save_path,checkpoint), map_location=lambda storage, loc: storage))
else:
    net.load_state_dict(torch.load("%s/%s"%(save_path,checkpoint), map_location=lambda storage, loc: storage))
    
attr_keys = ['BalacingElements', 'ColorHarmony', 'Content', 'DoF',
             'Light', 'MotionBlur', 'Object', 'RuleOfThirds', 'VividColor']
non_neg_attr_keys = ['Repetition', 'Symmetry', 'score']
all_keys = attr_keys + non_neg_attr_keys
used_keys = ["ColorHarmony", "Content", "DoF", "Object", "VividColor", "score"]

def extract_prediction(inp, net):
    d = dict()
    net.eval()
    output = net(inp)
    for i, key in enumerate(all_keys):
        d[key] = output[:, i].squeeze().data[0]
    return d

normalize_transform = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )

transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize([299, 299]),
                transforms.ToTensor(),
                normalize_transform
            ])

def predict_aesthetic(image_path):
    image_default = mpimg.imread(image_path)
    image = transform(image_default)
    inp = Variable(image).unsqueeze(0)
    if use_cuda:
        inp = inp.cuda()
    predicted_values = extract_prediction(inp, net)
    return predicted_values['score']
    