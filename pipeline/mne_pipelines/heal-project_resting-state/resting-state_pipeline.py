import mne
import matplotlib.pyplot as plt
import numpy as np

# g hg gh h
data_path = "/Users/ma6895/Library/CloudStorage/Box-Box/heal-project/before_intervention/sub-001/meg/sub-001_heal_eyesopen_eyesclosed-1.con"
raw_data = mne.io.read_raw_kit(data_path)
#print(raw_data.info.ch_names)
print(raw_data.ch_names)
#raw_data.plot()
raw_data_copy = raw_data.copy().pick_channels(['MISC 001'])
raw_data_copy.plot()
plt.show()
data_MISC001, time = raw_data_copy[:]
print(data_MISC001, time)

max_MISC001 = np.max(data_MISC001)
min_MISC001= np.min(data_MISC001)
print('max of data', max_MISC001)
print('min of data', min_MISC001)
threshold = (max_MISC001 + min_MISC001)/2

print('Cutting threshold', threshold)



#need to find max and min values of channel MISC 001 to use as thresholds to detect when the triggers start and end

import mne
import matplotlib.pyplot as plt
import numpy as np

# ----------------------
# Load raw KIT data
# ----------------------
data_path = "/Users/ma6895/Library/CloudStorage/Box-Box/heal-project/before_intervention/sub-001/meg/sub-001_heal_eyesopen_eyesclosed-1.con"
raw = mne.io.read_raw_kit(data_path, preload=True)

print("Channels:", raw.ch_names)

# ----------------------
# Pick trigger channel
# ----------------------
trigger_ch = "MISC 001"  # Eyes closed = 224, Eyes open = 225
raw_trigger = raw.copy().pick_channels([trigger_ch])

raw_trigger.plot()
plt.show()

# Get numpy data from trigger channel
trigger_data, times = raw_trigger[:]

# ----------------------
# Detect trigger onsets
# ----------------------
# Find events automatically
events = mne.find_events(raw, stim_channel=trigger_ch, shortest_event=1)
print("First 10 events:\n", events[:10])

# ----------------------
# Map your events
# ----------------------
event_id = {"eyes_closed": 224, "eyes_open": 225}

# ----------------------
# Epoch into chunks
# ----------------------
epochs = mne.Epochs(raw, events, event_id=event_id,
                    tmin=0, tmax=10,  # 10s chunks
                    baseline=None, preload=True)

# Separate conditions
epochs_closed = epochs["eyes_closed"]
epochs_open = epochs["eyes_open"]

# ----------------------
# Quick plots
# ----------------------
epochs_closed.average().plot(title="Eyes Closed")
epochs_open.average().plot(title="Eyes Open")

events = mne.find_events(raw, stim_channel="MISC 001", shortest_event=1)
print("First 10 events:\n", events[:10])

# ----------------------
# Timeline plot of eyes-open vs eyes-closed conditions
# This block reads the trigger channel (MISC 001), converts it into a simple binary timeline
# (0 = eyes closed, 1 = eyes open), and plots when the subject’s eyes were open or closed
# over the duration of the recording.
# ----------------------

import matplotlib.pyplot as plt
import numpy as np

# Get trigger data from MISC 001
trigger_data, times = raw.copy().pick_channels(['MISC 001'])[:]

# Create a simple binary timeline: 0 = eyes closed, 1 = eyes open
# Adjust threshold based on your trigger data
threshold = (np.max(trigger_data) + np.min(trigger_data)) / 2
timeline = np.where(trigger_data > threshold, 1, 0)  # 1 = eyes open, 0 = eyes closed

# Plot the timeline
plt.figure(figsize=(15, 3))
plt.plot(times, timeline, drawstyle='steps-post')
plt.xlabel('Time (s)')
plt.ylabel('Condition')
plt.yticks([0, 1], ['Eyes Closed', 'Eyes Open'])
plt.title('Timeline of Eyes-Closed vs Eyes-Open Conditions')
plt.ylim(-0.5, 1.5)
plt.show()

