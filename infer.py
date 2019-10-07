import sys
import snflow as flow
import numpy as np
import snmodel
import cv2
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
import sknw
import keras
import time
import getch

def infer_mask(model, image):
    output = model.predict(image)
    return np.array(output)

def infer_roads(masks):
    skels = []
    graphs = []
    for mask in masks:
        img = prep_for_skeletonize(mask)
        skel = skeletonize(img)
        graph = sknw.build_sknw(skel)
        return graph, skel
        skels.append(skel)
        graphs.append(graph)
    return graphs, skels

def prep_for_skeletonize(img):
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, img = cv2.threshold(img, 0.25, 1, cv2.THRESH_BINARY)
    img = dilate_and_erode(img)
    img = np.array(np.round(img), dtype=np.float32)
    return img

def dilate_and_erode(img):
    kernel = np.ones((1,35))
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    return img

def infer(model, image):
    mask = infer_mask(model, image.reshape([1,] + flow.IMSHAPE))
    graph, skel = infer_roads(mask)
    return mask, graph, skel

def infer_and_show(model, image):
    mask, graph, skel = infer(model, image)
    dilated_mask = dilate_and_erode(mask[0][:,:,0])
#    mask = infer_mask(model, image.reshape([1,] + flow.IMSHAPE))
#    graph, skel = infer_roads(mask)
#    masks, graphs, skels = [mask], [graph], [skel]
    for idx in range(1):
        fig = plt.figure()
        fig.add_subplot(1,5,1)
        plt.imshow(image)
        plt.title("1. Input (satellite image)")

        fig.add_subplot(1,5,2)
        plt.imshow(mask[0][:,:,0])
        plt.title("2. Mask (network output)")

        fig.add_subplot(1,5,3)
        plt.imshow(dilated_mask)
        plt.title("3. Postprocessed mask")

        fig.add_subplot(1,5,4)
        plt.imshow(skel)
        plt.title("4. Skeletonized mask")

        fig.add_subplot(1,5,5)
        plt.imshow(skel)
        plt.title("5. Resulting graph")
        for (s,e) in graph.edges():
            ps = graph[s][e]['pts']
            plt.plot(ps[:,1], ps[:,0], 'blue')
    
        node, nodes = graph.node, graph.nodes()
        ps = np.array([node[i]['o'] for i in nodes])
        try:
            plt.plot(ps[:,1], ps[:,0], 'r.')
        except IndexError as exc:
            print("WARNING: IndexError: %s" % exc)
        
        plt.show()

def do_all(loop=True):
    model = keras.models.load_model("model.tf")
    while True:
        path = flow.get_file()
        image = flow.resize(flow.get_image(path), flow.IMSHAPE).reshape(flow.IMSHAPE)
        if not loop:
            ret = infer(model, image) + (path,)
            return ret
        infer_and_show(model, image)
        sys.stdout.write("(Q)uit, or press any other key to continue.")
        sys.stdout.flush()
        char = getch.getch()
        print()
        if char.lower() == 'q':
            sys.exit()

if __name__ == "__main__":
    do_all()
