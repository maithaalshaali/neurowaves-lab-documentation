import mne
import matplotlib.pyplot as plt


# g hg gh h
data_path = "/Users/ma6895/Library/CloudStorage/Box-Box/heal-project/before_intervention/sub-001/meg/sub-001_heal_eyesopen_eyesclosed-1.con"
raw_data = mne.io.read_raw_kit(data_path)
print(raw_data.info.ch_names)
raw_data.plot()
plt.show()
a=1