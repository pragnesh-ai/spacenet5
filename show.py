#!/usr/bin/env python3
import re
from skimage import io
import matplotlib.pyplot as plt
import sys
import glob
import os
import plac
import random
import imageio
import numpy as np
from inspect import getsourcefile
import snflow as flow

DATADIR = "%s/data/train/AOI_7_Moscow/" % os.path.abspath(os.path.dirname(getsourcefile(lambda : 0)))

def cli(dataset: ("One of MS, PAN, PS-RGB, or PS-MS", "option", "d")="PS-RGB",
        *filename: "The name of the file, or a substring within the name"):
    """Leave filename blank to choose a random image"""
    for f in filename:
        allids = flow.get_imageids()
        path = None
        for id in allids:
            if re.search(re.compile(f), os.path.basename(id)):
                path = id
                break
        im = flow.get_image(filename=path)
        fig = plt.figure()
        fig.add_subplot(1,2,1)
        plt.imshow(im)
        plt.title("Original")
        fig.add_subplot(1,2,2)
        tb = flow.TargetBundle()
        binim = tb[os.path.basename(path)].image().squeeze()
        plt.imshow(binim)
        plt.imshow
        plt.title("Target: %s" % path)
    if not filename:
        fpath = flow.get_file(dataset=dataset)
        print("Displaying %s" % fpath)
        im = flow.get_image(filename=fpath, dataset=dataset)
        fig = plt.figure()
        fig.add_subplot(1,2,1)
        plt.imshow(im)
        plt.title("Original")
        fig.add_subplot(1,2,2)
        tb = flow.TargetBundle()
        plt.imshow(tb[os.path.basename(fpath)].image().squeeze())
        plt.title("Target")
    plt.show()

if __name__ == '__main__':
    plac.call(cli)
