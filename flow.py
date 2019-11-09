import random
import os
import cv2
import tensorflow as tf
import pandas as pd
import shapely
import json
import numpy as np
from settings import *
import matplotlib.pyplot as plt
import skimage
from keras.preprocessing.image import ImageDataGenerator
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Dataflow(tf.keras.utils.Sequence):
    def __init__(self, batch_size=1, samples=None, transform=False, shuffle=False, validation_set=False):
        self.transform = transform
        self.shuffle = shuffle
        self.batch_size = batch_size
        if transform:
            data_gen_args = dict(rotation_range=25,
                                     width_shift_range=0.1,
                                     height_shift_range=0.1,
                                     zoom_range=0.2,
                                     shear_range=0.2)
        else:
            data_gen_args = {}
        self.image_datagen = ImageDataGenerator(**data_gen_args)
        self.mask_datagen = ImageDataGenerator(**data_gen_args)

        if samples:
            self.samples = samples
        else:
            files = []
            for directory in LABELDIRS:
                files += [os.path.join(directory, f) for f in os.listdir(directory)]
            length = len(files)
            if validation_set:
                files = files[int(length*0.9):]
            else:
                files = files[:int(length*0.9)]
            self.samples = [Target.from_file(f) for f in files]

    def __len__(self):
        """Length of this dataflow in units of batch_size"""
        length = int(np.ceil(len(self.samples) / float(self.batch_size)))
        return length

    def __getitem__(self, idx):
        """Return images,masks := numpy arrays of size batch_size"""
        x = np.array([ex.image() for ex in self.samples[idx * self.batch_size:(idx + 1) * self.batch_size]])
        y = np.array([tgt.mask() for tgt in self.samples[idx * self.batch_size:(idx + 1) * self.batch_size]])
        """"
        trans_dict = { 'theta': 90, 'shear': 0.1 }
        for i in range(len(x)):
            if random.random() < float(self.transform):
                x[i] = self.image_datagen.apply_transform(x[i], trans_dict)
                y[i] = self.image_datagen.apply_transform(y[i], trans_dict)
        """
        return x,y


class Building:
    def __init__(self):
        self.wkt = None

    def coords(self):
        wkt = self.wkt
        pairs = []
        for pair in re.findall(r"\-?\d+\.?\d+ \-?\d+\.?\d+", wkt):
            xy = pair.split(" ")
            x,y = round(float(xy[0])), round(float(xy[1]))
            pairs.append(np.array([x,y]))
        return np.array(pairs)

    def color(self, scale=False):
        ret = CLASSES.index(self.klass)
        if scale:
            ret = ret / N_CLASSES
        return ret


class Target:
    def __init__(self, text):
        self.buildings = []
        self.parse_json(text)

    def parse_json(self, text):
        data = json.loads(text)
        self.img_name = data['metadata']['img_name']
        self.metadata = data['metadata']

        for feature in data['features']['xy']:
            prop = feature['properties']
            if prop['feature_type'] != 'building':
                continue
            b = Building()
            b.klass = prop.get('subtype', "no-damage")
           
            if b.klass not in CLASSES:
                logger.error(f"Unrecognized building subtype: {b.klass}")

            b.wkt = feature.get('wkt', None)
            b.uid = prop['uid']
            self.buildings.append(b)

    def mask(self, img=None):
        if img is None:
            img = np.zeros(TARGETSHAPE)
        for b in self.buildings:
            coords = b.coords()
            if len(coords > 1):
                cv2.fillConvexPoly(img, coords, b.color(scale=True))
        return img.clip(0.0, 1.0)

    def image(self):
        for path in IMAGEDIRS:
            fullpath = os.path.join(path, self.img_name)
            try:
                return skimage.io.imread(fullpath)
            except OSError as exc:
                continue
        raise exc

    @staticmethod
    def from_file(filename):
        with open(filename) as f:
            return Target(f.read())


def get_test_files():
    files = []
    for d in TESTDIRS:
        files += [os.path.join(d, ex) for ex in os.listdir(d)]
    return files


if __name__ == '__main__':
    import time
    df = Dataflow(batch_size=1)
    while True:
        idx = random.randint(0,len(df) - 1)
        fig = plt.figure()

        fig.add_subplot(1,3,1)
        plt.imshow(df.samples[idx].image())
        plt.title(df.samples[idx].img_name)

        fig.add_subplot(1,3,2)
        plt.imshow(df.samples[idx].image())
        colormap = {0: 'red', 1: 'blue', 2: 'green', 3: 'purple', 4: 'orange', 5: 'yellow', 6: 'brown' }
        for b in df.samples[idx].buildings:
            plt.plot(b.coords()[:,0], b.coords()[:,1], color=colormap[b.color()])
        plt.title("image overlaid with mask")

        fig.add_subplot(1,3,3)
        plt.imshow(df.samples[idx].mask().squeeze(), cmap='gray')
        plt.title("mask")


        plt.show()
        time.sleep(1)
