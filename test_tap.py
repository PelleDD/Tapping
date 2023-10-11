"""
Made by Pelle De Deckere, September 2023

Contact details:
https://pure.au.dk/portal/en/persons/pelle-de-deckere(ba57d59a-a1d5-438b-a8e4-33f9c5ad7e17).html
https://www.linkedin.com/in/pelle-de-deckere/
https://twitter.com/DeckerePelle
https://github.com/PelleDD

##########
HOW TO RUN
##########

Run/open this file inside the psychopy runnner/coder version 2023.2.2 minimum, this version is also forced if ran in newer versions

###############
TESTING MACHINE
###############

Apple MacBook Pro
Apple M2
MacOs Ventura Version 13.5.2 (22G91)

###########
DIRECTORIES
###########

-Your project folder
    -This file
    -'stimuli' folder (contains csv with naming and also csv with lists for stimuli triggers)
    -'subject_data_tap' folder (gets made otherwise)
        -Each subject gets a folder with their data pushed into it as a csv file and a log file

#####
Tasks        
#####

all tapping is done through midi


Tap spontaneous for x seconds 
    taping time onset and velocity is recorded in csv
    amount of time can be adjusted in the start gui under spon_tap_duration


Tap synchronization
    Tap on the beat of the audio file triggered
    low, medium and high complexityes
    80, 120 and 160 bpm
    total of 18 stimuli fully randomized



"""
####IMPORTS#####

import os
from os import path
import sys
import psychopy as pp
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
import pandas as pd
import random
import threading

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

#BECAUSE OF THIS THE SCRIPT HAS TO RUN ONCE FIRST, ON THE SECOND RUN EXTERNAL IMPORTS WORK#
#importing external stuff needed for midi controls, mido needs rtmidi
#define the required library versions
required_versions = {
    "mido": "1.3.0",
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
            'session': '1', #session if participants doe this more than once
            'run_type': ['training','exp'],      
            'debug': True,  # If true, small window, print extra info
            'home_dir': my_path, #not really being used but maybe handy to see where all this stuff is running from
            'spon_tap_duration': 5, # amount of time in seconds for the duration of the spontaneous tapping task
            'sync_break_duration': 3, #time between the audio stim from the sync tap task
            'after_stim': 0, #not in use
            'rating_time': 7, #not in use   
        }

#Push date, exp name and psychopy version into settings
settings['date'] = data.getDateStr() # get date and time via data module
settings['exp_name'] = 'tap_protocol' #set experiment name
settings['version'] = psy_version #push version of psychopy used in the gui

#create dialog box, we put this here because we need the settingssss for stuff to control from here
info_dlg = gui.DlgFromDict(settings, title='settings',
                            order=['subject', 'gender', 'age', 'session', 'run_type', 'debug', 'spon_tap_duration', 'sync_break_duration', 'after_stim', 'rating_time'])
if info_dlg.OK: #if user presses OK then
    next_settings = settings.copy()
else: #user didn't press OK, i.e. cancelled
    core.quit()

#folder name for the subject
sub_folder_name = settings['subject'] + '_' + settings['date'] + '_' + settings['exp_name']

#Create subject folder in the subject_data map this map is for individual output data if there is not one already
sub_dir = os.path.join(data_dir, sub_folder_name)
os.makedirs(sub_dir, exist_ok=True)

#path where data is pushed to, it joins the cwd with the map subject_data
data_path = sub_dir

# Initialize the MIDI input
# Try to open the 'Arturia BeatStep' MIDI input else Pelle's APC
try:
    midi_input = mido.open_input('Arturia BeatStep')
    print("Using Arturia BeatStep MIDI input.")
except IOError:
    # If 'Arturia BeatStep' is not available, try to open 'APC Key 25'
    try:
        midi_input = mido.open_input('APC Key 25')
        print("Using APC Key 25 MIDI input.")
    except IOError:
        # If both devices are unavailable, handle the error or set a default input
        print("No suitable MIDI input found. Handle the error or set a default input.")


#function and key to quit the experiment and save log file
#Set relevant keys
kb = keyboard.Keyboard()
keyESC = 'escape' #key to quit experiment
keyNext = 'space' #key to advance

#ESC quits the experiment
if event.getKeys(keyList = [keyESC]): #press 'escape'
    logging.flush()
    core.quit()                       

#set window size if debud
if settings['debug']: #if in debug mode, not full screen
        win = visual.Window(fullscr=False)
        
else: #otherwise full screen
        win = visual.Window(monitor='testMonitor', fullscr=True)

#make sure mouse is visible
win.allowGUI = True                        
win.mouseVisible = True 

#Construct the path to the CSV file inside the stimuli folder both for the exp and training session
if settings['run_type'] == 'exp':
     csv_list = os.path.join(stimuli_path, "stim_list_tap.csv")
else:
     csv_list = os.path.join(stimuli_path, "stim_list_tap.csv")

# Load the stim/masks/grooves CSV file into a DataFrame, csv_list deterimned by the training or exp, THE SEP thing costed me 3 hours to figure out, check column names!!!
df = pd.read_csv(csv_list, engine='python', encoding = 'utf-8', sep=';')

# Extract the mask and stim column into a list
spon_stim_list = df['sync_stim_name'].tolist()

# create a filename with path seperated by the unique name it should get when exp
log_filename = data_path + os.sep + settings['subject'] + '_' + 'log_' + settings['date'] + '_' + settings['exp_name']
spon_filename = data_path + os.sep + settings['subject'] + '_' + 'spon_' + settings['date'] + '_' + settings['exp_name']
sync_filename = data_path + os.sep + settings['subject'] + '_' + 'sync_' + settings['date'] + '_' + settings['exp_name']

#save a log file for detailed info handy for debugging - now only given when exp is running
if settings['run_type'] == 'exp' or 'training':
    logFile = logging.LogFile(log_filename+'.log', level=logging.EXP)

# Create a "Thank you" message
welcome = visual.TextStim(win, text="Thank you for participating!\n\n" \
                                   "Press space to continue" 
                                   , pos=(0, 0))

# Create a "Thank you" message end
end = visual.TextStim(win, text="Thank you for participating!\n\n" \
                                   "Press space to end" 
                                   , pos=(0, 0))

#Instructions spon tap message
instr_spon_tap = visual.TextStim(win, text= "Tap on the MIDI pad at your preferred steady tempo.\n\n" \
                                   "Press space to start" 
                                    , pos=(0, 0))

#Instructions sync tap message
instr_sync_tap = visual.TextStim(win, text= "Tap on the MIDI pad with the beat of the track after the count in.\n\n" \
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
spon_tap_data = []
sync_tap_data = []

####---EXPERIMENT/TRAINING STARTS---####
#set clocks
globalClock = core.Clock()  # to track the time since experiment started

#draw instructions and flip it on the screen
welcome.draw()
win.flip()
event.waitKeys(keyList = [keyNext])     #list restricts options for key presses, waiting for space

#draw instructions depending what has been chosen
instr_spon_tap.draw()
win.flip()
event.waitKeys(keyList = [keyNext])     #list restricts options for key presses, waiting for space

###SPONTANEOUS TAPPING###
#Participants tap x time on their own preferred pace
#start
start_time = time.time()
while time.time() - start_time < settings['spon_tap_duration']:
    fixation.draw()
    win.flip()
    for msg in midi_input.iter_pending():
        if msg.type == 'note_on':
            tap_time = (time.time() - start_time)
            tap_velocity = msg.velocity
            # Create a dictionary to store tap data first and settings later
            tap_entry = {
                    'tap_timing(s)': tap_time,
                    'tap_velocity(s)': tap_velocity,
                    'audio_file': '',
                    'audio_onset_timing(s)': '',
                    'audio_close_timing(s)': '', 
                    'task': 'spontaneous_tap'
                }
            # Add settings data to the tap entry
            tap_entry.update(settings)
            # Append the tap entry to the list of tap data, looopy
            spon_tap_data.append(tap_entry)

# Close the MIDI input when the experiment is done
midi_input.close()

# Save the data this function is made for this task to save
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

#Call the save_to_csv function to save the collected data
save_to_csv(spon_filename, spon_tap_data)

####SYNCHRONIZATION TAPPING####

# Try to open the 'Arturia BeatStep' MIDI input else Pelle's APC
try:
    midi_input = mido.open_input('Arturia BeatStep')
    print("Using Arturia BeatStep MIDI input.")
except IOError:
    # If 'Arturia BeatStep' is not available, try to open 'APC Key 25'
    try:
        midi_input = mido.open_input('APC Key 25')
        print("Using APC Key 25 MIDI input.")
    except IOError:
        # If both devices are unavailable, handle the error or set a default input
        print("No suitable MIDI input found. Handle the error or set a default input.")


#change cwd to the stimuli map otherwise it cannot trigger the files from the map
os.chdir(stimuli_path)

#Read audio file names/tap along stimuli from the CSV file
audio_files = []
if settings['run_type'] == 'exp':
    audio_files_df = pd.read_csv('stim_list_tap.csv', sep=';')
    audio_files = audio_files_df['sync_stim_name'].tolist()
else:
    audio_files_df = pd.read_csv('stim_list_tap_train.csv', sep=';')
    audio_files = audio_files_df['sync_stim_name'].tolist()


#Shuffle the audio files for random order of stimuli presentation
random.shuffle(audio_files)

# Create a list to preload audio files
preloaded_audio = []
audio_file_names = []

# Preload all audio files as objects and their names and get full duration
#create empty variable to fill
total_duration_sync_audio = 0

for audio_file in audio_files:
    preloaded_audio.append(sound.Sound(audio_file)) #store sound object
    audio_file_names.append(audio_file)  # Store the file name
    audio = sound.Sound(audio_file) #get the full duration of all audio files
    total_duration_sync_audio += audio.getDuration()

# Add sync_break_duration seconds between each audio file
total_duration_sync_audio += (len(audio_files) - 1) * settings['sync_break_duration'] #fill the empty variable

#Function to trigger an audio file for sync trial
def trigger_audio(audio):
    # Play the audio file
    audio.play()
    print(f"Playing audio file: {audio}")
    core.wait(audio.getDuration())
    audio.stop()

    #Set the flag to signal the audio playback thread to stop
    #global audio_thread_running
    #audio_thread_running = False

#Create a thread to play audiofor sync trial
def audio_thread(audio_file, audio_onset_time):
    global audio_close_time #make it global so the tap thread can access it
    audio_duration = audio_file.getDuration()
    audio_close_time = audio_onset_time + audio_duration
    trigger_audio(audio_file)

    while time.time() < audio_close_time:
        pass #keep this active until fully played the file

    #Set the flag to signal the tap thread to stop
    global tap_thread_running
    tap_thread_running = False

#Create a thread for tap event recording
def tap_sync_thread():
    start_tap_time = time.time() #timestamp of when this thread was activated
    tap_time_offset = 0  #tap time starts at 0 for every audio file
    while tap_thread_running:
        for msg in midi_input.iter_pending():
            if msg.type == 'note_on':
                current_tap_time = time.time() #time stamp of when the tap happend
                tap_time = tap_time_offset + current_tap_time - start_tap_time
                tap_velocity = msg.velocity
                
                # Create a dictionary to store tap data
                sync_tap_entry = {
                    'tap_timing(s)': tap_time,
                    'tap_velocity(s)': tap_velocity,
                    'audio_file': audio_file_name,
                    'audio_onset_timing(s)': audio_onset_time,
                    'audio_close_timing(s)': audio_close_time,
                    'task': 'sync_tap'
                }
                
                # Add settings data to the single tap entry
                sync_tap_entry.update(settings)
                
                # Append the tap entry to the list of full tap data
                sync_tap_data.append(sync_tap_entry)


#draw instructions depending what has been chosen
instr_sync_tap.draw()
win.flip()
event.waitKeys(keyList = [keyNext])     #list restricts options for key presses, waiting for space

###start of the trial###
#clock for the sync trial
start_sync_time = time.time()

#clock main
while time.time() - start_sync_time < total_duration_sync_audio:
       
#Check if there are more audio files to process it goes through the whole list
    if preloaded_audio:
        fixation.draw()
        win.flip()
        # Trigger audio file and record onset time
        audio_file = preloaded_audio.pop(0)  # Take the first audio file in the list and erase it from the list
        audio_file_name = audio_file_names.pop(0) #we need the name as well
        audio_onset_time = time.time() - start_sync_time  # Calculate onset time once for the trial

        #Start audio playback thread
        audio_playback_thread = threading.Thread(target=audio_thread, args=(audio_file, audio_onset_time))
        audio_playback_thread.start()

        #Reset the flag to ensure tap thread runs
        tap_thread_running = True

        #Start tap event recording thread
        tap_recording_thread = threading.Thread(target=tap_sync_thread)
        tap_recording_thread.start()

        #Wait for audio playback thread to complete
        audio_playback_thread.join()

    #a break before the next audio file
    time.sleep(settings['sync_break_duration'])

#change working directory back to the path of the python file to save correctly
os.chdir(my_path)

#i made this for individual task maybe not nice but just to be sure data from seperate tasks is handled seperatly
def append_to_csv_sync(filename, tap_data):
    if not tap_data:
        print("No data to append.")
        return
    if not filename.endswith(".csv"):
        filename += ".csv" #if the filename doesnt have the extension .csv add it
    with open(filename, 'a', newline='') as csvfile: #a means append
        csvwriter = csv.DictWriter(csvfile,  fieldnames=tap_data[0].keys())

        # Write tap data without writing headers again
        csvwriter.writerows(tap_data)

# Call the append_to_csv function to append the collected data to the existing CSV file

append_to_csv_sync(spon_filename, sync_tap_data)

print(f"Data appended to {spon_filename}")

#Close the MIDI input when the experiment is done
midi_input.close()

# Display the "Thank you" message until space
end.draw()
win.flip()
event.waitKeys(keyList = [keyNext])   # key stroke ends it all

print("Hooray another data set")

# Close the window and end the experiment
win.close()
core.quit()

