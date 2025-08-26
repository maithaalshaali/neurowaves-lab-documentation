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