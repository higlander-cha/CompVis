#main.py

#import ActionDetection as adet
import io
import json
import os
import time
from math import sqrt

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import requests
from gpiozero import Button, LEDBoard
from picamera import Color, PiCamera
from PIL import Image
import traceback
import logging


class Camera(PiCamera):
    def __init__(self, settings):
        super(Camera, self).__init__()
        self.rotation = settings['Camera rotation']
        self.resolution = tuple(settings['Camera resolution'])
        self.framerate = settings['Camera framerate']
        self.brightness = settings['Camera brightness']
        self.contrast = settings['Camera contrast']
   
    def take_picture(self):
        self.capture(os.getcwd() + '/Pics/image.jpg') #take a picture and save at cwd  

class CompVis:
    def __init__(self):
        self.settings = self.load_settings()
        self.camera = Camera(self.settings)
        #self.waiter = ActionDetection.Waiter(self.camera, settings['Waiter period'])
        self.url = self.settings['url']
        self.threshold = self.settings['Threshold']
        self.compare = self.load_comparator()
        self.locations = self.settings['Locations']
        self.iteration = self._get_iteration()

        ##some tests
        self.test()
        
        self.url = self.url + "/image"
        
    def deinit(self):
        self.camera.close()

    def load_settings(self): #Get settings from jsonFile
        print("getting settings")
        try: 
            with io.open(os.getcwd() + '/settings.json', 'rt', encoding='utf-8-sig') as json_file:
                if json_file.readable():
                    settings = json.load(json_file)
                else:
                    raise FileNotFoundError
        except FileNotFoundError:
            with io.open(os.getcwd() + '/defaultsettings.json', 'rt') as json_file:    
                if json_file.readable():
                    settings = json.load(json_file)
                else:
                    raise FileNotFoundError 
            ##initiate with default values 
        return settings

    def load_comparator(self):
        if self.settings['Compare method'] == "center_to_center":
            return compare_center_to_center
        elif self.settings['Compare method'] == "percent_overlap": 
            return compare_percent_overlap 
        else: #default
            return compare_center_to_center

    def test(self):
        self.camera.take_picture() #make sure camera works
        with open(os.getcwd() + '/Pics/image.jpg') as image_file: 
            assert image_file.readable()

        r = requests.get(self.url)
        assert r.ok
        logging.debug(r.text) # should say: CustomVision.ai model host harness
        print(r.text)

    def get_predictions(self, frame):
        files = {'imageData': frame}
        test_response = requests.post(self.url, files=files)
        assert test_response.ok
        return test_response.json()

    def process_data(self, data): #excludes predictions under threshold and updates data in location
        predictions = [x for x in data['predictions'] if x['probability'] > self.threshold]
        for location in self.locations:
            if self.compare(location, predictions, self.settings):
                location['hasBox'] = True
            else:
                location['hasBox'] = False
        return predictions

    def draw_rectangle(self, ax, bb, edgecolour, facecolour=None):
        img_width,img_height = self.camera.resolution
        x, y, h, w = bb['left'], bb['top'], bb['height'], bb['width']
        fill = facecolour != None
        alpha = 1
        if fill:
            alpha = 0.5
        rect = patches.Rectangle(
                    (img_width*x,img_height*y), w*img_width, h*img_height, 
                    linewidth=1, edgecolor=edgecolour, fill=fill, facecolor=facecolour, alpha=alpha)
        ax.add_patch(rect)

    def show(self, predictions): #TODO: Implement with GUI
        im = Image.open(os.getcwd() + '/Pics/image.jpg')
        fig, ax = plt.subplots()
        ax.imshow(im)
        img_width,img_height = self.camera.resolution

        for x in predictions:
            bb = x['boundingBox']
            self.draw_rectangle(ax, bb, 'b')

        for location in self.locations:
            bb = location['boundingBox']
            color = 'r'
            if location['hasBox']:
                color = 'g'
            self.draw_rectangle(ax, bb, color)

            if self.compare == "center_to_center":
                if "center" in location:
                    #make a transparent circle with the comparing radius around center
                    pass
            elif self.settings['Compare method'] == "percent_overlap":
                if "overlap" in location:
                    bb = location['overlap']
                    self.draw_rectangle(ax, bb, 'g', 'g')
        #save a copy of that image 
        image_name = "output" + str(self.iteration) + ".png"
        plt.savefig(os.getcwd() + "/Output/" + image_name)
        plt.show()
    
        
    def run(self):
        print("run")
        directory = os.getcwd()
        image_name = "input" + str(self.iteration) + ".png"
        ##
        self.camera.capture(directory + '/Pics/' + image_name)
        with io.open(directory + '/Pics/input' + str(self.iteration) + '.png', 'rb') as image_file:
            data = self.get_predictions(image_file)
            #TODO: save data
            with io.open(os.getcwd() + "/Answers/answer" + str(self.iteration) + ".json", "w") as json_file:
                print(data)
                json.dump(data, json_file)
            predictions = self.process_data(data)
            self.show(predictions)

    def run_once(self, progress_callback):
        print("run_once")
        directory = os.getcwd()
        image_name = "input" + str(self.iteration) + ".png"
        
        self.camera.capture(directory + '/Pics/' + image_name)
        with io.open(directory + '/Pics/input' + str(self.iteration) + '.png', 'rb') as image_file:
            data = self.get_predictions(image_file)
            
        with io.open(directory + "/Answers/answer" + str(self.iteration) + ".json", "w") as json_file:
            print(data)
            json.dump(data, json_file)
        predictions = self.process_data(data)
        progress_callback.emit(self.iteration)
        print("ITERATION: {iteration}".format(iteration=str(self.iteration)))
        self.iteration += 1;

    def loop(self, progress_callback):
        self.running = True
        directory = os.getcwd()
        
        while self.runnning:
            image_name = "input" + str(self.iteration) + ".png"
            self.camera.capture(directory + '/Pics/' + image_name)
            with io.open(directory + '/Pics/' + image_name, 'rb') as image_file:
                data = self.get_predictions(image_file)
            
            #save data
            with io.open(directory + "/Answers/answer" + str(self.iteration) + ".json", "w") as json_file:
                print(data)
                json.dump(data, json_file)
            predictions = self.process_data(data)
            progress_callback.emit(self.iteration) #tell gui that we just did an iteration
            print("ITERATION: {iteration}".format(iteration=str(self.iteration)))
            self.iteration += 1;
            time.sleep(self.settings['Period'])

    def change_settings(self): #TODO: Either gui changes here
        pass

    def get_settings(self):  #TODO: or receives the object and changes it
        pass

    def _get_iteration(self):
        directory = os.getcwd() + "/Pics"
        return len(os.listdir(directory))
  
def compare_percent_overlap(location, predictions, settings):
    bb = location['boundingBox']
    l_bb = bb['left'], bb['top'], bb['width'], bb['height']
    for pred in predictions:
        bb = pred['boundingBox']
        p_bb = bb['left'], bb['top'], bb['width'], bb['height']
        x1 = max(l_bb[0], p_bb[0])
        y1 = max(l_bb[1], p_bb[1])
        px2 = p_bb[0] + p_bb[2]
        py2 = p_bb[1] + p_bb[3]
        lx2 = l_bb[0] + l_bb[2]
        ly2 = l_bb[1] + l_bb[3]
        x2 = min(px2, lx2)
        y2 = min(py2, ly2)
        h = x2 - x1
        w = y2 - y1
        if h < 0 or w < 0:
            continue
        overlap = (x1,y1,h,w)
        overlap_size = overlap[2] * overlap[3]
        pred_size = p_bb[2] * p_bb[3]
        overlap_percentage = 100 * overlap_size/pred_size
        
        if overlap_percentage > settings['Percent overlap required']:
            location['overlap'] = {
                'left' : overlap[0],
                'top' : overlap[1],
                'width' : overlap[2],
                'height' : overlap[3]
                }

            return True  
    return False

    
           


def compare_center_to_center(loc, predictions, settings): #a,b are dicts with height, width, top, left 
    #expressed as fractions of the frame radius is expressed as a fraction of the width and height 
    for pred in predictions:
        if center not in loc:
            loc['center'] = center(loc['boundingBox'])
        if center not in pred:
            pred['center'] = center(pred['boundingBox'])
        dx = loc['center'][0] - pred['center'][0]
        dy = loc['center'][1] - pred['center'][1]
        distance = sqrt(dx**2 + dy**2)
        radius = settings['Radius'] * (loc['boundingBox']['height'] + loc['boundingBox']['width']) / 2
        if distance < radius:
            return True
    return False
    

def center(bounding_box): #computes the center of a bounding box
    x = bounding_box['left'] + bounding_box['width']/2
    y = bounding_box['top'] + bounding_box['height']/2
    return (x,y)

def init():
    directory = os.getcwd() + "/Pics"
    if not os.path.exists(directory):
        os.mkdir(directory)
    directory = os.getcwd() + "/Answers"
    if not os.path.exists(directory):
        os.mkdir(directory)
    directory = os.getcwd() + "/Output"
    if not os.path.exists(directory):
        os.mkdir(directory)

def main():
    #make directories if they dont exist
    directory = os.getcwd() + "/Pics"
    if not os.path.exists(directory):
        os.mkdir(directory)
    directory = os.getcwd() + "/Answers"
    if not os.path.exists(directory):
        os.mkdir(directory)
    directory = os.getcwd() + "/Output"
    if not os.path.exists(directory):
        os.mkdir(directory)

    #init and run
    compvis = CompVis()
    compvis.run()
    compvis.deinit()
    

if __name__ == "__main__":
    print("Running main.py")
    main()