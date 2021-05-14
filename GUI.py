#GUI.py
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QPushButton, QApplication, QTableWidget, QTableWidgetItem
import json
import io
import os
import time
#import main_development as comp
import test1 as comp
import traceback, sys

class Rack(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super(Rack, self).__init__(*args, **kwargs)

        self.setGeometry(QtCore.QRect(10, 10, 304, 371)) #Placement
        self.setText("Live feed") 
        self.setPixmap(QtGui.QPixmap("Pics/input0.png")) #Can be changed to variable from JSON   
        self.setScaledContents(True) #Scales the picture
        self.setObjectName("Rack")

class Window(QtWidgets.QWidget):

    def __init__(self):
        super(Window, self).__init__()

        self.compvis = comp.CompVis()
        self.pic = QtGui.QPixmap("Pics/input0.png")
        self.rack = Rack(self) #Init
        self.threadpool = QtCore.QThreadPool()

        self.dict_iteration = 0
        
        self.add = QtWidgets.QPushButton(self)
        self.add.setGeometry(QtCore.QRect(435, 358, 273, 40))
        self.add.setText("Add obj.")

        self.remove = QtWidgets.QPushButton(self)
        self.remove.setGeometry(QtCore.QRect(698, 358, 273, 40))
        self.remove.setText("Delete row")
        self.remove.clicked.connect(self.remove_slot_by_row)

        self.startButton = QtWidgets.QPushButton(self) 
        self.startButton.setGeometry(QtCore.QRect(310, 10, 136, 21))
        self.startButton.clicked.connect(self.run_compvis)
        self.startButton.setText("Run")

        self.stopButton = QtWidgets.QPushButton(self) 
        self.stopButton.setGeometry(QtCore.QRect(310, 30, 136, 21))

        self.stopButton.clicked.connect(self.stop_compvis)
        self.stopButton.setText("Stop")

        self.brightButton = QtWidgets.QPushButton(self) 
        self.brightButton.setGeometry(QtCore.QRect(310, 50, 136, 21))
        self.brightButton.clicked.connect(self.adjust_brightness)
        self.brightButton.setText("Adj. bright.")

        self.contrastButton = QtWidgets.QPushButton(self) 
        self.contrastButton.setGeometry(QtCore.QRect(310, 70, 136, 21))
        self.contrastButton.clicked.connect(self.adjust_contrast)
        self.contrastButton.setText("Adj. contrast.")

        self.threshButton = QtWidgets.QPushButton(self) 
        self.threshButton.setGeometry(QtCore.QRect(310, 90, 136, 21))
        self.threshButton.clicked.connect(self.adjust_thresh)
        self.threshButton.setText("Adj. thresh.")

        self.row_count = 15
        #Table
        self.TableofSlots = QtWidgets.QTableWidget(self)
        self.TableofSlots.setGeometry(QtCore.QRect(440, 10, 527, 350))
        self.TableofSlots.setColumnCount(5)
        self.TableofSlots.setRowCount(self.row_count)
        item = QtWidgets.QTableWidgetItem()
        self.TableofSlots.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.TableofSlots.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.TableofSlots.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.TableofSlots.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.TableofSlots.setHorizontalHeaderItem(4, item)
        item = self.TableofSlots.horizontalHeaderItem(0)
        item.setText("Location")
        item = self.TableofSlots.horizontalHeaderItem(1)
        item.setText("Top")
        item = self.TableofSlots.horizontalHeaderItem(2)
        item.setText("Left")
        item = self.TableofSlots.horizontalHeaderItem(3)
        item.setText("Width")
        item = self.TableofSlots.horizontalHeaderItem(4)
        item.setText("Height")
        self.fill_table_settings()
        self.add.clicked.connect(lambda:self.update_json())

#######Help functions
    def draw_rectangle(self, pb, bb, color, fill = False):
        img_width = self.pic.width()
        img_height = self.pic.height()
        x, y, h, w = bb['left'], bb['top'], bb['height'], bb['width']
        x = int(x*img_width)
        y = int(y*img_height)
        w = int(w*img_width)
        h = int(h*img_height)
        color = QtGui.QColor(color)

        if fill:
            pb.setOpacity(0.5)
            pb.fillRect(x,y,w,h, color)
        else:
            pb.setOpacity(1)
            pen = QtGui.QPen(color, 5)
            pb.setPen(pen)
            
            pb.drawRect(x, y, w, h)

    def update_pic(self, iteration):
        path = "Output/output" + str(iteration) + ".png"
        self.pic = QtGui.QPixmap(path)
        self.Rack.setPixmap(self.pic)

    def update_pic2(self, iteration):
        path = "Pics/input" + str(iteration) + ".png"

        self.pic = QtGui.QPixmap(path)
        if not os.path.exists(path):
            print("PIC not found")
            return
        pb = QtGui.QPainter(self.pic)
        ''' with io.open("Answers/answer" + str(iteration) + ".json", 'rt') as ans:
            predictions = json.load(ans)['predictions'] '''
    
        for pred in self.compvis.get_predictions():
            bb = pred['boundingBox']
            self.draw_rectangle(pb, bb, "blue")

        for location in self.compvis.get_locations():
            color = "red"
            if location['hasBox']:
                color = "green"
                if self.compvis.settings['Compare method'] == "percent_overlap":
                    if "overlap" in location:
                        bb = location['overlap']
                        self.draw_rectangle(pb, bb, "green", fill=True)

            bb = location['boundingBox']
            self.draw_rectangle(pb, bb, color)
        pb.end()
        self.rack.setPixmap(self.pic)
        file = QtCore.QFile("Output/output" + str(iteration) + ".png")
        if not file.open(QtCore.QIODevice.WriteOnly):
            print("cant open")
        self.pic.save(file)

    def update_settings():
        pass

    def run_threaded_process(self, process, on_complete):
        """Execute a function in the background with a worker"""
        worker = Worker(fn=process)
        self.threadpool.start(worker)
        worker.signals.finished.connect(on_complete)
        worker.signals.progress.connect(self.progress_fn)

    def progress_fn(self, msg):
        self.update_pic2(msg)

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            print(event.globalPos().x(), event.globalPos().y())

    def update_json(self):

        filepath = 'defaultsettings.json'
        if os.path.exists('settings.json'):
            filepath = 'settings.json'
        with open(filepath, 'r') as file:
            print("opening settings")
            data = json.load(file)

        self.temp = 0
        for i in range(len(data['Locations'])):
            new_dict = self.create_dict(i)
            if all(new_dict.values()):
                data["Locations"][i] = new_dict
            else:
                pass
            temp=i+1
        print("HEJ")
        for row in range(self.row_count-temp):
            new_dict = self.create_dict(row+temp)
            if all(new_dict['boundingBox'].values()): 
                    data["Locations"].append(new_dict)
            else:
                #Säg ifrån att det sket sig
                pass
                
        print(data)
        with open('settings.json', "w") as file:
            json.dump(data, file, indent=4)
        
        self.compvis.update_settings()
        self.update_pic2(self.compvis.iteration)
        #Se över buid_row

    #def add_slot(self): #Funkar, men skickar inget popup
        #this_dict = self.create_dict()

        #filepath = 'defaultsettings.json'
        #if os.path.exists('settings.json'):
        #    filepath = 'settings.json'
        #with open(filepath, 'r') as file:
        #    print("opening settings")
        #    data = json.load(file)
#
       # data["Locations"].append(this_dict)
       # with open('settings.json', "w") as file:
       #     json.dump(data, file, indent=4)

       # self.dict_iteration += 1

    def create_dict(self, row):

        this_dict = {"name" : None, "hasBox" : False, "boundingBox" : 
            {"height": None,"left": None,"top": None,"width": None}}
        #print(str(self.dict_iteration))
        this_dict = self.get_slotname(this_dict, row)
        this_dict = self.get_top(this_dict, row)
        this_dict = self.get_left(this_dict, row)
        this_dict = self.get_height(this_dict, row)
        this_dict = self.get_width(this_dict, row)
        #print(this_dict)
        return this_dict

    def remove_slot_by_name(self):#Funkar inte, behövs det ens?
        name, ok = QInputDialog.getText(self, 'Text Input Dialog', 'location name to remove:')
        if ok == True:
            slot = name

        for row in range (self.dict_iteration):
            #print(self.TableofSlots.item(row,0).text())
            #print(row)
            if self.TableofSlots.item(row,0).text() == slot:
                #print(row)
                self.TableofSlots.removeRow(row)
                row = row - 1
                #print(row)
                #Fixa for each

        with open('settings.json', 'r') as file:
            data = json.load(file)
            for i in range(len(data['Locations'])):
                if data['Locations'][i]['name'] == slot:
                    data['Locations'].pop(i)

        with open('settings.json', 'w') as file:
            json.dump(data, file, indent=4)

    def remove_slot_by_row(self): #Funkar
        row_index, okPressed = QInputDialog.getInt(self, "Remove row","Value:", 1, 1, 40, 1)
        if okPressed == True:
            slot = self.TableofSlots.item(row_index-1,0).text()
        
        self.TableofSlots.removeRow(row_index-1)

        with open('settings.json', 'r') as file:
            data = json.load(file)
            
            for i in range(len(data['Locations'])-1):
                if data['Locations'][i]['name'] == slot:
                    data['Locations'].pop(i)
        
        with open('settings.json', 'w') as file:
            json.dump(data, file, indent=4)

    def fill_table_settings(self): #Funkar   
        filepath = 'defaultsettings.json'
        if os.path.exists('settings.json'):
            filepath = 'settings.json'
        with open(filepath, 'r') as file:
            #print("opening settings")
            data = json.load(file)

        for entry in data["Locations"]:
            self.TableofSlots.setItem(self.dict_iteration,0, QTableWidgetItem(entry["name"]))
            self.TableofSlots.setItem(self.dict_iteration,1, QTableWidgetItem(str(entry["boundingBox"]["top"])))
            self.TableofSlots.setItem(self.dict_iteration,2, QTableWidgetItem(str(entry["boundingBox"]["left"])))
            self.TableofSlots.setItem(self.dict_iteration,3, QTableWidgetItem(str(entry["boundingBox"]["height"])))
            self.TableofSlots.setItem(self.dict_iteration,4, QTableWidgetItem(str(entry["boundingBox"]["width"])))

            self.dict_iteration += 1
    
    def run_compvis(self):
        self.compvis.update_settings()
        self.run_threaded_process(self.compvis.loop, self.completed)
        
    def stop_compvis(self):
        self.compvis.running = False

    def completed(self):
        self.compvis.deinit()
        print("TOOT")
#######Functions for buttons

    def adjust_brightness(self):
        bright, okPressed = QInputDialog.getInt(self, "Set brightness","Value:", 1, 1, 100, 1)

        filepath = 'defaultsettings.json'
        if os.path.exists('settings.json'):
            filepath = 'settings.json'
        with open(filepath, 'r') as file:
            data = json.load(file)

        data["Camera brightness"] = bright #
        with open('settings.json', "w") as file:
            json.dump(data, file, indent=4)

    def adjust_contrast(self):
        contrast, okPressed = QInputDialog.getInt(self, "Set contrast","Value:", 1, 1, 100, 1)

        filepath = 'defaultsettings.json'
        if os.path.exists('settings.json'):
            filepath = 'settings.json'
        with open(filepath, 'r') as file:
            data = json.load(file)

        data["Camera contrast"] = contrast
        with open('settings.json', "w") as file:
            json.dump(data, file, indent=4)

    def adjust_thresh(self):
        thresh, okPressed = QInputDialog.getDouble(self, "Set threshold","Value:", 0.0, 0, 1, 3)

        filepath = 'defaultsettings.json'
        if os.path.exists('settings.json'):
            filepath = 'settings.json'
        with open(filepath, 'r') as file:
            data = json.load(file)

        data["Threshold"] = thresh
        with open('settings.json', "w") as file:
            json.dump(data, file, indent=4)

    def set_resolution(self):
        items = ("Red","Blue","Green")
        item, okPressed = QInputDialog.getItem(self, "Get item","Color:", items, 0, False)
        if ok and item:
            print(item)

    def get_top(self, this_dict, row):
        try:
            if self.TableofSlots.item(row,1) is not None:
                top = self.TableofSlots.item(row,1).text()
                this_dict["boundingBox"]["top"]=float(top)
            else:
                raise ValueError
        except ValueError:
            top = None
            #self.TableofSlots.setItem(row,1, QTableWidgetItem(str(top)))
            #self.showSetBox(" top coordinate")
        
        
        #print(top)
        #self.TableofSlots.setItem(self.dict_iteration,1, QTableWidgetItem(str(top)))
        return this_dict

    def get_left(self, this_dict, row):
        try:
            if self.TableofSlots.item(row,2) is not None:
                left = self.TableofSlots.item(row,2).text()
                this_dict["boundingBox"]["left"]=float(left)
            else:
                raise ValueError
        except ValueError:
            left = None
            #self.TableofSlots.setItem(row,2, QTableWidgetItem(str(left)))
            #self.showSetBox(" left coordinate")
        #print(left)
        #self.TableofSlots.setItem(self.dict_iteration,2, QTableWidgetItem(str(left)))
        return this_dict

    def get_height(self, this_dict, row):
        try:
            if self.TableofSlots.item(row,3) is not None:
                height = self.TableofSlots.item(row,3).text()
                this_dict["boundingBox"]["height"]=float(height)
            else:
                raise ValueError
        except ValueError:
            height = None
            #self.TableofSlots.setItem(row,3, QTableWidgetItem(str(height)))
            #self.showSetBox(" height")
        
        #print(height)
        #self.TableofSlots.setItem(self.dict_iteration,3, QTableWidgetItem(str(height)))
        return this_dict

    def get_width(self, this_dict, row):
        try:
            if self.TableofSlots.item(row,4) is not None:
                width = self.TableofSlots.item(row,4).text()
                this_dict["boundingBox"]["width"]= float(width)
            else:
                raise ValueError
        except ValueError:
            width = None
            #self.TableofSlots.setItem(row,4, QTableWidgetItem(str(width)))
            #self.showSetBox(" width")
        
        #print(width)
        #self.TableofSlots.setItem(self.dict_iteration,4, QTableWidgetItem(str(width)))
        return this_dict

    def get_slotname(self, this_dict, row):
        try:
            if self.TableofSlots.item(row,0) is not None:
                name = self.TableofSlots.item(row,0).text()
                this_dict["name"]=name
            else:
                raise ValueError
        except ValueError:
            name = None
            #self.TableofSlots.setItem(row,0, QTableWidgetItem(name))
            #self.showSetBox(" name")

        
        #print(name)
        #self.TableofSlots.setItem(self.dict_iteration,0, QTableWidgetItem(name))
        return this_dict

    def showSetBox(self, missing):
        msg = QMessageBox()
        msg.setWindowTitle("ERROR")
        msg.setText("No"+ missing + " given")

        x = msg.exec_() #Shows message box

    #https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
class Worker(QtCore.QRunnable):
    """Worker thread for running background tasks."""

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @QtCore.pyqtSlot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs,
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class WorkerSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        `tuple` (exctype, value, traceback.format_exc() )
    result
        `object` data returned from processing, anything
    """
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(int)



def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    comp.init()
    window = Window()
    window.setGeometry(500, 150, 1000, 1000)
    window.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()