"""
Made by Pelle De Deckere, September 2023

Contact details:
https://pure.au.dk/portal/en/persons/pelle-de-deckere(ba57d59a-a1d5-438b-a8e4-33f9c5ad7e17).html
https://www.linkedin.com/in/pelle-de-deckere/
https://twitter.com/DeckerePelle
https://github.com/PelleDD

####
HOW TO RUN
####

Run/open this file inside the psychopy runnner/coder version 2023.2.2 minimum, this version is also forced

####
TESTING MACHINE
####

Apple MacBook Pro
Apple M2
MacOs Ventura Version 13.5.2 (22G91)

####
DIRECTORIES
####

-Your project folder
    -This file
    -'stimuli' folder (for now make one for future stimuli)
    -'subject_data_tap' folder (gets made otherwise)
        -Each subject gets a folder with their data pushed into it as a csv file

####
Task        
####

Tap spontaneous for X seconds on a midi device
    taping time onset and velocity is recorded in csv

"""
####IMPORTS#####

import os
from os import path
import sys
import psychopy as pp
#pp.useVersion('2022.2.4') #force version of psychopy everything after is based on this version
pp.useVersion('2023.2.2') #force version of psychopy everything after is based on this version
from psychopy import prefs
prefs.general['audioLib'] = ['pyo'] #this has to be imported before the sound module
from psychopy import gui, core, logging, event, visual, data, sound
sound.init(44100, buffer=128) #set buffers apparently this works best without cracks etc
from psychopy.hardware import keyboard
#from psychopy import plugins
#import pandas as pd
import time
#import random
import subprocess
import pkg_resources
import csv

'''
some explenation on external imports for me to remember

custom imports get installed in your standalone version of psychopy go to app show contents 
Recources/lib/pyhtonX/... (mac); folder called site packages has the added libraries

from psychopy site
Adding a .pth file
An alternative is to add a file into the site-packages folder of your application. This file should be pure text and have the extension .pth to indicate to Python that it adds to the path.
On win32 the site-packages folder will be something like C:/Program Files/PsychoPy2/lib/site-packages
On macOS you need to right-click the application icon, select Show Package Contents and then navigate down to Contents/Resources/lib/pythonX.X. Put your .pth file here, next to the various libraries.
The advantage of this method is that you dont need to do the import psychopy step. The downside is that when you update PsychoPy to a new major release youll need to repeat this step (patch updates wont affect it though).


mido pushes also something into the bin folder of your psychopy (in case of deleting)
'''

#BECAUSE OF THIS THE SCRIPT HAS TO RUN ONCE, ON SECOND RUN EXTERNAL IMPORTS WORK#
#importing external stuff needed for midi controls, mido needs rtmidi
#define the required library versions
required_versions = {
    "mido": "1.3",
    "python-rtmidi": "1.5.6",
}

# Function to check and install libraries with specific versions
def check_and_install_library(library_name, required_version):
    try:
        import_module = __import__(library_name)
        installed_version = pkg_resources.get_distribution(library_name).version

        if installed_version == required_version:
            print(f"Found {library_name} version {installed_version}")
        else:
            print(f"Found {library_name} version {installed_version}, but version {required_version} is required.")
            subprocess.check_call([sys.executable, "-m", "pip", "install", f"{library_name}=={required_version}"])

    except ImportError:
        print(f"{library_name} not found. Installing {library_name} version {required_version}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", f"{library_name}=={required_version}"])

# Check and install mido
check_and_install_library("mido", required_versions["mido"])

# Check and install python-rtmidi
check_and_install_library("python-rtmidi", required_versions["python-rtmidi"])

#import these external libraries
import mido
import rtmidi

####IMPORTS DONE#####

#look what you have, MIDI gear
def find_midi_ports():
  print(f"Input ports: {mido.get_input_names()}")
  print(f"Output ports: {mido.get_output_names()}") 

find_midi_ports()

#version psychopy
psy_version = pp.__version__

#tell me everything you encounter
logging.console.setLevel(logging.DEBUG) #tell me everything you encounter

#get directory name of file, give path to this directory
my_path = os.path.abspath(os.path.dirname(__file__))

#change working directory to given path
os.chdir(my_path)

#Create folder in the map this file is, for all subject output data if there is not one already
data_dir = os.path.join(my_path, 'subject_data_tap')
os.makedirs(data_dir, exist_ok=True)

#Get the path to the current working directory
cwd = os.getcwd()

#Construct the path to the stimuli folder inside the project folder
stimuli_path = os.path.join(cwd, "stimuli")

#Set default settings, dictionary
settings = {
            'subject': '0',  # Subject code use for loading/saving data
            'gender': ['male', 'female'],
            'age': '',
            'session': '1', #session 
            'run_type': ['training','exp'],        
            'debug': True,  # If true, small window, print extra info
            'home_dir': my_path, #not really being used but maybe handy to see where all this stuff is running from
            'between_stim': 2, # number of seconds between two presenations of stim
            'after_mask': 2, #time between mask and next chord 
            'after_stim': 0, #time between end of stim and appearance of rating scale
            'rating_time': 7, # number of seconds to make rating       
        }

#Push date, exp name and psychopy version into settings
settings['date'] = data.getDateStr() # get date and time via data module
settings['exp_name'] = 'tap_protocol' #set experiment name
settings['version'] = psy_version #push version of psychopy used in the gui

#create dialog box, we put this here because we need the settingssss for stuff to control from here
info_dlg = gui.DlgFromDict(settings, title='settings',
                            order=['subject', 'gender', 'age', 'session', 'run_type', 'debug', 'between_stim', 'after_mask', 'after_stim', 'rating_time'])
if info_dlg.OK: #if user presses OK then
    next_settings = settings.copy()
else: #user didn't press OK, i.e. cancelled
    core.quit()

#Construct the path to the CSV file inside the stimuli folder both for the exp and training session
#if settings['run_type'] == 'exp':
#    csv_list = os.path.join(stimuli_path, "stim_mask_list_chord.csv")
#else:
#    csv_list = os.path.join(stimuli_path, "stim_mask_list_chord_train.csv")

#folder name for the subject
sub_folder_name = settings['subject'] + '_' + settings['date'] + '_' + settings['exp_name']

#Create subject folder in the subject_data map this map is for individual output data if there is not one already
sub_dir = os.path.join(data_dir, sub_folder_name)
os.makedirs(sub_dir, exist_ok=True)

#path where data is pushed to, it joins the cwd with the map subject_data
data_path = sub_dir

# Initialize the MIDI input
#midi_input = mido.open_input('Arturia BeatStep')  # Replace with your MIDI pad's name
midi_input = mido.open_input('APC Key 25')

#function and key to quit the experiment and save log file
#Set relevant keys
kb = keyboard.Keyboard()
keyESC = 'escape' #key to quit experiment
keyNext = 'space' #key to advance

#ESC quits the experiment
if event.getKeys(keyList = [keyESC]): #press 'escape'
    logging.flush()
    core.quit()                       

#set window size
if settings['debug']: #if in debug mode, not full screen
        win = visual.Window(fullscr=False)
        
else: #otherwise full screen
        win = visual.Window(monitor='testMonitor', fullscr=True)

#make sure mouse is visible
win.allowGUI = True                        
win.mouseVisible = True 

# create a filename with path seperated by the unique name it should get when exp
filename = data_path + os.sep + settings['subject'] + '_' + settings['date'] + '_' + settings['exp_name']

#save a log file for detailed info handy for debugging - now only given when exp is running
if settings['run_type'] == 'exp':
    logFile = logging.LogFile(filename+'.log', level=logging.EXP)


# Create a "Thank you" message
welcome = visual.TextStim(win, text="Thank you for participating!\n\n" \
                                   "Press space to continue" 
                                   , pos=(0, 0))

#Instructions message
instr = visual.TextStim(win, text= "Tap on the MIDI pad at your preferred tempo.\n\n" \
                                   "Press space to start" 
                                    , pos=(0, 0))

#make fixation cross                          
fixation = visual.ShapeStim(win,
                                vertices=((0, -0.15), (0, 0.15), (0, 0),
                                        (-0.1, 0), (0.1, 0)),
                                lineWidth=13,
                                closeShape=False,
                                lineColor='white')

# Initialize lists to store tap data
tap_data = []

####---EXPERIMENT/TRAINING STARTS---####
#set clocks
globalClock = core.Clock()  # to track the time since experiment started

#draw instructions and flip it on the screen
welcome.draw()
win.flip()
event.waitKeys(keyList = [keyNext])     #list restricts options for key presses, waiting for space

#draw instructions depending what has been chosen
instr.draw()
win.flip()
event.waitKeys(keyList = [keyNext])     #list restricts options for key presses, waiting for space

#change cwd to the stimuli map otherwise it cannot trigger the files from the map
#os.chdir(stimuli_path)

#start
start_time = time.time()
while time.time() - start_time < 10:
    fixation.draw()
    win.flip()
    for msg in midi_input.iter_pending():
        if msg.type == 'note_on':
            tap_time = (time.time() - start_time)
            tap_velocity = msg.velocity
            # Create a dictionary to store tap data first and settings later
            tap_entry = {
                    'Tap Timing (ms)': tap_time,
                    'Tap Velocity': tap_velocity
                }
            # Add settings data to the tap entry
            tap_entry.update(settings)
            # Append the tap entry to the list of tap data, looopy
            tap_data.append(tap_entry)

# Close the MIDI input when the experiment is done
midi_input.close()

# Save the data using your preferred method (e.g., CSV, JSON)
def save_to_csv(filename, tap_data):
    if not filename.endswith(".csv"):
        filename += ".csv" #if the filename doesnt have the extension .csv add it
    with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=tap_data[0].keys())

            # Write headers
            csvwriter.writeheader()

            # Write tap data
            csvwriter.writerows(tap_data)

print(f"Data and settings saved to {filename}")

# Call the save_to_csv function to save the collected data
save_to_csv(filename, tap_data)

# Display the "Thank you" message for a few seconds
welcome.draw()
win.flip()
event.waitKeys(keyList = [keyNext])   # Display for 3 seconds (you can adjust the duration)

# Close the window and end the experiment
win.close()
core.quit()

