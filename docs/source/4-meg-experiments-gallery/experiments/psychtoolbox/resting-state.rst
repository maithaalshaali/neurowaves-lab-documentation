.. _resting_state_exp:

Experiments example 1 (Psychtoolbox): Resting state
---------------------------------------------------

Description
^^^^^^^^^^^

- Resting state experiment: Using PsychToolBox the following script executes a resting state experiment.

The participant is asked to close their eyes for some time, then to open their eyes while fixing a centered shape for a same duration.
Two triggers are sent from the 'Datapixx3' to the KIT-MEG on channels 224 (closing eyes) and 225 (opening eyes).
In MNE, Channel 224 = MISC 001 and Channel 225 = MISC 002
The code for the experiment can be found here: Source file link


:github-file:`Resting State Eyes Closed <experiments/psychtoolbox/restingstate/resting_state_meg_EYES_CLOSED.m>`
:github-file:`Resting State Eyes Open <experiments/psychtoolbox/restingstate/resting_state_meg_EYES_OPEN.m>`




Analysis results
^^^^^^^^^^^^^^^^

The notebook provides analysis results after running the experiment on a participant (Sub-01).

`Link to notebook <../../../6-meg-pipeline-gallery/notebooks/mne/resting_state_pipeline.ipynb>`_