"""Authors: Jess Breda and Cody Baker."""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import seaborn as sns
import scipy.io as spio


def load_nested_mat(filename):
    """
    This function should be called instead of direct scipy.io.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects. From https://stackoverflow.com/questions
    /48970785/complex-matlab-struct-mat-file-read-by-python
    """

    def _check_vars(d):
        """
        Checks if entries in dictionary are mat-objects. If yes
        todict is called to change them to nested dictionaries
        """
        for key in d:
            if isinstance(d[key], spio.matlab.mio5_params.mat_struct):
                d[key] = _todict(d[key])
            elif isinstance(d[key], np.ndarray):
                d[key] = _toarray(d[key])
        return d

    def _todict(matobj):
        """
        A recursive function which constructs from matobjects nested dictionaries
        """
        d = {}
        for strg in matobj._fieldnames:
            elem = matobj.__dict__[strg]
            if isinstance(elem, spio.matlab.mio5_params.mat_struct):
                d[strg] = _todict(elem)
            elif isinstance(elem, np.ndarray):
                d[strg] = _toarray(elem)
            else:
                d[strg] = elem
        return d

    def _toarray(ndarray):
        """
        A recursive function which constructs ndarray from cellarrays
        (which are loaded as numpy ndarrays), recursing into the elements
        if they contain matobjects.
        """
        if ndarray.dtype != 'float64':
            elem_list = []
            for sub_elem in ndarray:
                if isinstance(sub_elem, spio.matlab.mio5_params.mat_struct):
                    elem_list.append(_todict(sub_elem))
                elif isinstance(sub_elem, np.ndarray):
                    elem_list.append(_toarray(sub_elem))
                else:
                    elem_list.append(sub_elem)
            return np.array(elem_list)
        else:
            return ndarray

    data = spio.loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_vars(data)


def load_and_wrangle_behavior(beh_path):
    """
    This function loads behavior and spike data from a single session given path information.

    Parameters
    ----------
    beh_path : string
        Path to .mat file with behavior info.

    Returns
    -------
    beh_df : df (ntrials x items)
        Tidy data frame with behavior information & some relabeling.
    """
    beh_info = load_behavior(beh_path)
    beh_df = make_beh_df(beh_info)
    return beh_df

def load_and_wrangle(beh_path, spks_path, overwrite):
    """
    This function loads behavior and spike data from a single session given path
    information. If behavior data has already been loaded & wrangled, will load
    the dataframe instead of creating a new one.
    inputs
    ------
    beh_path  : string, path to .mat file with behavior info
    spks_path : string, path to .mat file with spks info
    overwrite (optional, False) : wether or not to overwrite previous dataframe
    or load up if already made
    returns
    ------
    beh_df    :  df (ntrials x items), tidy data frame with behavior information
                & some relabeling
    spks_info : ndarray, with spk info from .mat file
    """

    # --Spikes--- (eventually can load/in out with pickle if needed)
    sess_path = os.path.dirname(spks_path)

    if os.path.exists(os.path.join(sess_path, 'spks_dict.pkl')) and overwrite==False:

        with open(os.path.join(sess_path, 'spks_dict.pkl'), 'rb') as fh:
            spks_dict = pickle.load(fh)

    else:
        # load, wrangle & save out
        spks_info = load_spks(spks_path)
        spks_dict = make_spks_dict(spks_info)

        output = open(os.path.join(sess_path, 'spks_dict.pkl'), 'wb')
        pickle.dump(spks_dict, output)
        output.close()

    # --Behavior--
    # check if the df has already been created, then either load or wrangle & savout
    if os.path.exists(os.path.join(sess_path, 'beh_df.csv')) and overwrite==False:

        beh_df = pd.read_csv(os.path.join(sess_path, 'beh_df.csv'))

    else:
        # load, wrangle & save out
        beh_info = load_behavior(beh_path)
        full_beh_df = make_beh_df(beh_info)
        beh_df = filter_phys_time(full_beh_df, spks_dict)

        # beh_df.head()
        beh_df.to_csv(os.path.join(sess_path, 'beh_df.csv'), index=False)

    return beh_df, spks_dict

## called by load and wrangle:

def load_spks(spks_path):
    """
    This function loads the behavior data from the ksphy_cluster_info_foranalys.mat
    file in the directory that is passed into it
    inputs
    ------
    spks_path : string, path to .mat file with spiking info extracted from kilosort/raw data
    returns
    ------
    spks_info : ndarray, with spk info from .mat file
    """
    spks_info = spio.loadmat(spks_path)
    spks_info = spks_info['PWMspkS'][0]

    return spks_info

def make_spks_dict(spks_info):
    """
    Data wrangling function to take ndarry from load_spks() and put into python dict
    for analysis
    inputs
    ------
    spks_info : ndarray, with spk info from .mat file
    returns
    -------
    spks_dict : dict with ephys information for session & each cell
    """

    # initilaize
    spks_dict= {}
    ncells = len(spks_info['trodenum'])
    trode_nums = []
    m_waves = []
    s_waves = []
    spk_qual = []
    spk_times = []

    # grab date, spike to behavior time & fs
    spks_dict['date'] = spks_info['date'][0][0]
    spks_dict['spk2fsm'] = spks_info['behav_session'][0]['spk2fsm_rt'][0][0][0]#[m, b
    spks_dict['fs'] = spks_info['fs'][0][0][0]

    # for each cell, tetrode number, spike type, mean waveform, std waveform
    for cell in range(ncells):
        trode_nums.append(spks_info['trodenum'][cell][0][0])
        spk_times.append(spks_info['event_ts_fsm'][cell]) # in beh time
        m_waves.append(spks_info['waves_mn'][cell].reshape(4,32))
        s_waves.append(spks_info['waves_std'][cell].reshape(4,32))

        if spks_info['mua'][cell][0][0] == 1:
            spk_qual.append('multi')
        elif spks_info['single'][cell][0][0] == 1:
            spk_qual.append('single')
        else:
            raise TypeError("cell not marked as multi or single")

    # appened
    spks_dict['trode_nums'] = trode_nums
    spks_dict['spk_qual'] = spk_qual
    spks_dict['spk_times'] = spk_times
    spks_dict['mean_wav'] = m_waves #[ncell][tetrode]
    spks_dict['std_wav'] = s_waves

    return spks_dict

def load_behavior(beh_path):
    """
    This function loads the behavior data from the protocol_info.mat file in the
    directory that is passed into it
    inputs
    ------
    beh_path  : string, path to .mat file with behavior info
    returns
    ------
    beh_info  : ndarray, with behavior .mat structure extracted
    """
    beh_info = load_nested_mat(beh_path) # this function is custom to deal with nested structures
    beh_info = beh_info["behS"]

    return beh_info

def make_beh_df(beh_info):

    """
    Data wrangling function to take ndarry from load_behaviorand putting it into a
    tidy dataframe for analysis
    inputs
    ------
    beh_info : ndarray, extracted .mat structure from load_session_info()
    returns
    -------
    beh_df   : df (ntrials x items), tidy data frame with behavior information & some relabeling
    """

    # initialize data frame
    beh_df = pd.DataFrame()

    # ignore setting with copy warning
    pd.options.mode.chained_assignment = None

    # assign trail n values
    beh_df['trial_num'] = np.arange(1, beh_info['n_completed_trials'] + 1)

    # rename previous side to be L/R
    prev_side_adj = np.roll(beh_info['prev_side'],1) # n-1 trial info
    prev_side_adj = np.where(prev_side_adj == 114, 'RIGHT', 'LEFT' )
    prev_side_adj[0] = 'NaN' # trial 0 doesn't have a previous

    # turn hit info to strings
    beh_df['hit_hist'] = beh_info['hit_history']
    beh_df['hit_hist'] = beh_df['hit_hist'].mask(beh_df['hit_hist'] == 1.0, "hit")
    beh_df['hit_hist'] = beh_df['hit_hist'].mask(beh_df['hit_hist'] == 0.0, "miss")
    beh_df['hit_hist'][beh_df['hit_hist'].isnull()] = "viol"

    # get n_trial length items into df
    beh_df['delay'] = beh_info['delay']
    beh_df['pair_hist'] = beh_info['pair_history']
    beh_df['correct_side'] = beh_info['correct_side']
    beh_df['prev_side'] = prev_side_adj
    beh_df['aud1_sigma'] = beh_info['aud1_sigma']
    beh_df['aud2_sigma'] = beh_info['aud2_sigma']

    # extract parsed events/state machine info for each trial
    parsed_events_dict = beh_info["parsed_events"]

    # initilize space
    c_poke = np.zeros((len(parsed_events_dict)))
    hit_state = np.zeros((len(parsed_events_dict)))
    aud1_on = np.zeros((len(parsed_events_dict)))
    aud1_off = np.zeros((len(parsed_events_dict)))
    aud2_on = np.zeros((len(parsed_events_dict)))
    aud2_off = np.zeros((len(parsed_events_dict)))
    end_state = np.zeros((len(parsed_events_dict)))

    # iterate over items from state matrix
    for trial in range(len(parsed_events_dict)):

        # every trial has a center poke & end_state
        c_poke[trial] = parsed_events_dict[trial]['states']['cp'][0]
        end_state[trial] = parsed_events_dict[trial]['states']['check_next_trial_ready'][1]

        # not all trials will have sound/hit time/etc, pull out info for non-violated
        if beh_df['hit_hist'][trial] == 'viol':
            hit_state[trial] = float("NaN")
            aud1_on[trial]   = float("NaN")
            aud1_off[trial]  = float("NaN")
            aud2_on[trial]   = float("NaN")
            aud2_off[trial]  = float("NaN")

        elif beh_df['hit_hist'][trial] == 'hit':
            hit_state[trial] = parsed_events_dict[trial]['states']['hit_state'][0]
            aud1_on[trial]   = parsed_events_dict[trial]['waves']['stimAUD1'][0]
            aud1_off[trial]  = parsed_events_dict[trial]['waves']['stimAUD1'][1]
            aud2_on[trial]   = parsed_events_dict[trial]['waves']['stimAUD2'][0]
            aud2_off[trial]  = parsed_events_dict[trial]['waves']['stimAUD2'][1]

        elif beh_df['hit_hist'][trial] == 'miss':
            hit_state[trial] = parsed_events_dict[trial]['states']['second_hit_state'][0]
            aud1_on[trial]   = parsed_events_dict[trial]['waves']['stimAUD1'][0]
            aud1_off[trial]  = parsed_events_dict[trial]['waves']['stimAUD1'][1]
            aud2_on[trial]   = parsed_events_dict[trial]['waves']['stimAUD2'][0]
            aud2_off[trial]  = parsed_events_dict[trial]['waves']['stimAUD2'][1]

        else:
            raise Exception('hit_hist doesn''t appear to have correct structure (hit, miss, viol)')


    # add to df
    beh_df['c_poke']    = c_poke
    beh_df['end_state'] = end_state
    beh_df['hit_state'] = hit_state
    beh_df['aud1_on']   = aud1_on
    beh_df['aud1_off']  = aud1_off
    beh_df['aud2_on']   = aud2_on
    beh_df['aud2_off']  = aud2_off
    beh_df['end_state'] = end_state

    find_loudness(beh_df)
    find_first_sound(beh_df)


    # turn warning back on
    # ignore setting with copy warning
    pd.options.mode.chained_assignment = 'warn'

    return beh_df

def filter_phys_time(full_beh_df, spks_dict):


    """
    Sometimes session is started pre phys or ends post phys. This function removes the trials when
    phys recording did not occur
    inputs:
    -------
    full_beh_df  : df, contianing beh information for the whole session created by
                   make_beh_df()
    spks_dict    : dict with ephys information for session & each cell
    returns
    -------
    filt_df       : df, contianing beh information only for trials that occured
                  during ephys recording session
    """
    starts = []
    ends = []

    for neuron in range(len(spks_dict['spk_times'])):
        starts.append(spks_dict['spk_times'][neuron][0])
        ends.append(spks_dict['spk_times'][neuron][-1])

    start_time = np.max(starts)
    end_time = np.min(ends)

    filt_df = full_beh_df.query('c_poke > @start_time & hit_state < @end_time')

    return filt_df

def find_loudness(beh_df):
    """Quick function for converting from pair history info to determine
    which sound was louder in a trial, ignoring pyschometric trials. Pass in beh_df,
    or any dataframe with 'pair_hist' column to create a new column called loduness"""

    conditions = [
        (beh_df['pair_hist'] < 5),
        (beh_df['pair_hist'] >= 5) & (beh_df['pair_hist'] < 9),
        (beh_df['pair_hist'] >= 9)
    ]

    values = ['aud_1', 'aud_2', 'psycho']
    beh_df['louder'] = np.select(conditions, values)

def find_first_sound(beh_df):
    """
    Quick function for converting from pair history info to determine the loudness
    of the first sound in a trial
    """

    conditions = [
        (beh_df['pair_hist'] == 1) | (beh_df['pair_hist'] == 6),
        (beh_df['pair_hist'] == 2) | (beh_df['pair_hist'] == 7),
        (beh_df['pair_hist'] == 3) | (beh_df['pair_hist'] == 8),
        (beh_df['pair_hist'] == 4), (beh_df['pair_hist'] == 5),
        (beh_df['pair_hist'] >= 9)
    ]
    # taking behS.soundpairs, using dB from athena paper
    values = ['68', '76', '84', '92*', '60*', 'psycho']
    beh_df['first_sound'] = np.select(conditions, values)


"Selective Loading"
## == Selective loading functions to use once neurons of interest are determined
### ---this function calls all of the above except make_spks_dict
def selective_load_and_wrangle(beh_path, spks_path, sess_neurons, overwrite):
    """
    This function loads behavior and spike data from a single session given path
    information. If behavior data has already been loaded & wrangled, will load
    the dataframe instead of creating a new one.
    inputs
    ------
    beh_path  : string, path to .mat file with behavior info
    spks_path : string, path to .mat file with spks info
    sess_neurons : list, containing 0 indexed neuron numbers to load for a session
    overwrite (optional, False) : wether or not to overwrite previous dataframe
    or load up if already made
    returns
    ------
    beh_df    :  df (ntrials x items), tidy data frame with behavior information
                & some relabeling
    spks_info : ndarray, with spk info from .mat file
    """

    # --Spikes--- (eventually can load/in out with pickle if needed)
    sess_path = os.path.dirname(spks_path)

    if os.path.exists(os.path.join(sess_path, 'selective_spks_dict.pkl')) and overwrite==False:

        with open(os.path.join(sess_path, 'selective_spks_dict.pkl'), 'rb') as fh:
            spks_dict = pickle.load(fh)

    else:
        # load, wrangle & save out
        spks_info = load_spks(spks_path)
        spks_dict = selective_make_spks_dict(spks_info, sess_neurons)

        output = open(os.path.join(sess_path, 'selective_spks_dict.pkl'), 'wb')
        pickle.dump(spks_dict, output)
        output.close()

    # --Behavior--
    # check if the df has already been created, then either load or wrangle & savout
    if os.path.exists(os.path.join(sess_path, 'beh_df.csv')) and overwrite==False:

        beh_df = pd.read_csv(os.path.join(sess_path, 'beh_df.csv'))

    else:
        # load, wrangle & save out
        beh_info = load_behavior(beh_path)
        full_beh_df = make_beh_df(beh_info)
        beh_df = filter_phys_time(full_beh_df, spks_dict)

        beh_df.to_csv(os.path.join(sess_path, 'beh_df.csv'), index=False)

    return beh_df, spks_dict

### ---this function calls all of the above except make_spks_dict, here is the edit:
def selective_make_spks_dict(spks_info, sess_neurons):
    """
    Data wrangling function to take ndarry from load_spks() and put into python dict
    for analysis
    inputs
    ------
    spks_info : ndarray, with spk info from .mat file
    sess_neurons : list, containing 0 indexed neuron numbers to load for a session
    returns
    -------
    spks_dict : dict with ephys information for session & each cell
    """

    # initilaize
    spks_dict= {}
    neuron_nums = [] # to be able to confirm indexing in non-selective loading
    trode_nums = []
    m_waves = []
    s_waves = []
    spk_qual = []
    spk_times = []


    # grab date, spike to behavior time & fs
    spks_dict['date'] = spks_info['date'][0][0]
    spks_dict['spk2fsm'] = spks_info['behav_session'][0]['spk2fsm_rt'][0][0][0]#[m, b
    spks_dict['fs'] = spks_info['fs'][0][0][0]

    # for each pre-selected cell, tetrode number, spike type, mean waveform, std waveform
    for cell in sess_neurons:
        trode_nums.append(spks_info['trodenum'][cell][0][0])
        spk_times.append(spks_info['event_ts_fsm'][cell]) # in beh time
        m_waves.append(spks_info['waves_mn'][cell].reshape(4,32))
        s_waves.append(spks_info['waves_std'][cell].reshape(4,32))
        neuron_nums.append(cell)

        if spks_info['mua'][cell][0][0] == 1:
            spk_qual.append('multi')
        elif spks_info['single'][cell][0][0] == 1:
            spk_qual.append('single')
        else:
            raise TypeError("cell not marked as multi or single")

    # append
    spks_dict['neuron_nums'] = neuron_nums
    spks_dict['trode_nums'] = trode_nums
    spks_dict['spk_qual'] = spk_qual
    spks_dict['spk_times'] = spk_times
    spks_dict['mean_wav'] = m_waves #[ncell][tetrode]
    spks_dict['std_wav'] = s_waves

    return spks_dict


"Event centering of spike times for plotting"

def event_align_session(spks_dict, beh_df, sess_path, overwrite=False, delay_mode=True, file_name=None):
    """ Function for alining spike times from each neuron in a session to relevant events
    and saving out as a dictionary
    Params:
    ------
    spks_dict  :
    beh_df     : df (ntrials x items), tidy data frame with behavior information & some relabeling
    sess_path  : string, path to session folder in bucket
    overwrite  : bool, whether or not to overwrite previous dictionary, (optional, defualt = False)
    delay_mode : bool, whether or not to aligned to variable delay peroid (optional, default = True)
    file_name  : str,optional- defualt = 'event_aligned_spks.pkl' what to save out .pkl as
    Returns:
    --------
    session_algined : dict, nested with dicts of aligned spk times for each neuron
    session_windows : dict, nested with dicts of windows used to align spk times
                      for each neuron, event
    """

    # check to see if already there, load in if so
    if file_name:
        fname = file_name
    else:
        fname = 'event_aligned_spks.pkl'

    if os.path.exists(os.path.join(sess_path, fname)) and \
    os.path.exists(os.path.join(sess_path, 'session_windows.pkl')) and \
    overwrite==False:

        print('loading from file...')

        with open(os.path.join(sess_path, file_name), 'rb') as fh:
            session_aligned = pickle.load(fh)

        with open(os.path.join(sess_path, 'session_windows.pkl'), 'rb') as fh:
            session_windows = pickle.load(fh)
    else:

        print('no file found, running alignment for session')

        # initialize information
        session_spks = spks_dict['spk_times']
        n_neurons = len(session_spks)
        session_aligned = {}
        session_windows = {}

        for ineuron in range(n_neurons):

            # TODO saving out additional info from this might be nice at some point
            trial_spks = split_spks_by_trial(session_spks[ineuron], beh_df)
            neuron_aligned, windows = align_neuron_to_events(beh_df, trial_spks, delay_mode=delay_mode)
            session_aligned[ineuron] = neuron_aligned
            session_windows[ineuron] = windows

        # save out
        output = open(os.path.join(sess_path, file_name), 'wb')
        pickle.dump(session_aligned, output)
        output.close()

        output = open(os.path.join(sess_path, 'session_windows.pkl'), 'wb' )
        pickle.dump(session_windows, output)
        output.close()

    return session_aligned, session_windows

# called by event_align session:

def split_spks_by_trial(spk_times, beh_df):
    """
    Function that converts spikes for a whole trial (1d) into array where rows are trials
    and columns are spk times within a trial for a neuron, added to dict with other trial level info
    inputs
    ------
    spk_times : arr-like, 1d containing spk times in seconds for a single neuron for a session
    beh_df        : df, containing behavior information for a trial
    returns
    -------
    trial_spks_dict : dict, containing trial number (w/ respect to whole session), start and stop times
                      for a trial and the spks occuring in a a trial in s
    """

    # initialize
    neuron_spks_dict = {}
    trial_nums = []
    trial_starts = []
    trial_stops = []
    trial_spks = []

    # make counter because dataframe idx is not continous
    # instead, it represents overall trial number with respect to start of session
    itrial = 0

    for idx, trial in beh_df.iterrows():

        # grab start time 500 ms before c poke
        trial_start = trial['c_poke'] -0.5

        # create end time so delays have same length
        if trial['delay'] == 2:
            trial_end = trial_start + 5.5
        elif trial['delay'] == 4:
            trial_end = trial_start + 7.7
        elif trial['delay'] == 6:
            trial_end = trial_start + 9.9
        else:
            print('Trial delay is not 2, 4 or 6 seconds- this is not correct')

        # append trial info
        trial_nums.append(idx)
        trial_starts.append(trial_start)
        trial_stops.append(trial_end)

        # grab spike time within trial window & append them
        trial_spks.append(spk_times[np.logical_and(spk_times >= trial_start, spk_times <= trial_end)])


    neuron_spks_dict['nums'] = trial_nums
    neuron_spks_dict['times'] = trial_starts, trial_stops
    neuron_spks_dict['spks'] = trial_spks

    return neuron_spks_dict

def align_neuron_to_events(beh_df, neuron_spks, delay_mode=True):

    """Wrapper function for event alignment for a single neuron spk times
    Params:
    ------
    beh_df : df (ntrials x items), tidy data frame with behavior information
                & some relabeling
    neuron_spks : list, single neuron output from split_spks_by_trial() trial_spks_dict['trial_spks']
    delay_mode  : bool, whether or not to aligned to variable delay peroid (optional, default = True)
    Returns:
    -------
    algined : dict, keys = event being aligned to, values = spks by trial for event
    """

    stimuli_aligned, stimuli_windows = stimuli_align(beh_df, neuron_spks)

    if delay_mode == True:

        delay_aligned, delay_windows = delay_align(beh_df, neuron_spks)

        aligned = dict(stimuli_aligned, **delay_aligned)
        windows = dict(stimuli_windows, **delay_windows)

        return aligned, windows

    else:
        return stimuli_aligned, stimuli_windows

def stimuli_align(beh_df, neuron_spks):

    """Function for aligning spike times to certain stimuli in the trial
    Params
    ------
    beh_df : df (ntrials x items), tidy data frame with behavior information
                & some relabeling
    neuron_spks : list, single neuron output from split_spks_by_trial()
    Returns
    -------
    stimuli_dict : dict with events centered to stimuli happening on all trials"""

    # specific events and windows
    df_event = ['aud1_on', 'aud1_off', 'aud2_on', 'aud2_off', 'aud1_on', 'aud1_off']
    names = ['aud1on', 'aud1off', 'aud2on', 'aud2off', 'trial_all', 'delay_overlap']
    windows = [[-400, 600], [-500, 500], [-400, 600], [-500, 500], [-100, 5000], [-600, 2600]]


    stimuli_dict = {}
    # rest idx for iteration
    beh_df = beh_df.reset_index()

    for event,name,window in zip(df_event,names,windows):

        # intialize a list to push to in the dictionary
        stimuli_dict[name] = []

        for itrial, row in beh_df.iterrows():

            trial_spks = neuron_spks['spks'][itrial]

            # grab alignment time
            align_time = row[event]

            # create windows
            start = align_time + (window[0] * 0.001)
            stop  = align_time + (window[1] * 0.001)

             # grab spks in the window
            spks_in_window = trial_spks[np.logical_and(trial_spks > start, trial_spks < stop)]
            event_aligned = spks_in_window - align_time

            # append
            stimuli_dict[name].append(event_aligned)

    stimuli_windows = dict(zip(names, windows))

    return stimuli_dict, stimuli_windows

def delay_align(beh_df, neuron_spks):
    """Function for extracting info for specific delay lengths
    Params
    ------
    beh_df : df (ntrials x items), tidy data frame with behavior information
                & some relabeling
    neuron_spks : list, single neuron output from split_spks_by_trial()
    Returns
    -------
    delay_dict : dict with events centered and contianing spks specific to delay length
    delay_windows: dict with aligmnet windows for each delay event
    Notes
    -----
    this code is very bulky, but it does the job. future Jess don't judge me
    """

    # hard code windows and names of trial types
    delay_windows = [[-150, 2150],[-200, 2400], [-150, 4150], [-200, 4400]]
    delay_names = ['delay2s', 'trial2s', 'delay4s', 'trial4s']

    L =[[],[],[],[]]
    beh_df = beh_df.reset_index()

    # iterate over each trial
    for itrial, row in beh_df.iterrows():

        trial_spks = neuron_spks['spks'][itrial]
        d_align_time = row['aud1_off']
        t_align_time = row['aud1_on']

        if row['delay'] == 2:

            # this grabs just delay period
            d = 0
            d_start  = d_align_time + (delay_windows[d][0] * 0.001)
            d_stop   = d_align_time + (delay_windows[d][1] * 0.001)

            spks_in_delay = trial_spks[np.logical_and(trial_spks > d_start, trial_spks < d_stop)]
            delay_aligned = spks_in_delay - d_align_time
            L[d].append(delay_aligned)

            # this grab the whole trial
            t = 1
            t_start  = t_align_time + (delay_windows[t][0] * 0.001)
            t_stop   = t_align_time + (delay_windows[t][1] * 0.001)

            spks_in_trial = trial_spks[np.logical_and(trial_spks > t_start, trial_spks < t_stop)]
            trial_aligned = spks_in_trial - t_align_time
            L[t].append(trial_aligned)

        elif row['delay'] == 4:

            d = 2
            d_start  = d_align_time + (delay_windows[d][0] * 0.001)
            d_stop   = d_align_time + (delay_windows[d][1] * 0.001)

            spks_in_delay = trial_spks[np.logical_and(trial_spks > d_start, trial_spks < d_stop)]
            delay_aligned = spks_in_delay - d_align_time
            L[d].append(delay_aligned)

            t = 3
            t_start  = t_align_time + (delay_windows[t][0] * 0.001)
            t_stop   = t_align_time + (delay_windows[t][1] * 0.001)

            spks_in_trial = trial_spks[np.logical_and(trial_spks > t_start, trial_spks < t_stop)]
            trial_aligned = spks_in_trial - t_align_time
            L[t].append(trial_aligned)


    return dict(zip(delay_names, L)), dict(zip(delay_names, delay_windows))


"Importing masking info & creating dfs"

def deal_with_masking(spks_dict, beh_df, sess_path, csv_name, threshold=1000):
    """
    Function that loads masking info based on active bundles for the session, assess masking
    and returns dataframes for each bundle with trials that have not been masked
    inputs
    ------
    spks_dict : dict, with ephys infomration created by make_spks_dict()
    beh_df    : df, with behavior information created by make_beh_df ()
    sess_path : path to directory for a sorted session with mask NPY files for each bundle
    csv_name  :vstr, what you want to title the csv, without bndl number. (e.g. 'hit_trials_df')
    threshold (optional) : int, number of samples that can be masked during a trial
                           and still considered valid
    returns
    -------
    bndl_dfs  : dict, containing behavior df with unmasekd trails for each bndl that has a mask
    df_names  : list, Ncells long containing dict keys to access df for each cell
    saved out
    ---------
    mask_dict : dict, with masking information used to create a dataframs, saved as .pkl
    """

    mask_dict = load_masks(spks_dict, sess_path)

    all_samples_masked, mask_keys = det_samples_masked(mask_dict, beh_df)

    all_unmasked_idxs = find_unmasked_idx(all_samples_masked, threshold = threshold)

    bndl_dfs, df_names = make_unmasked_dfs(all_unmasked_idxs, mask_keys, beh_df, spks_dict, sess_path, csv_name)

    return bndl_dfs, df_names

# called by deal_with_masking:

def load_masks(spks_dict, sess_path):
    """
    Function for loading mask info stored in sorted in sorted session directory
    based on the active tetrodes in the session
    inputs
    ------
    spks_dict: dict, containing ephys information created by make_spks_dict()
    sess_path : path to directory for a sorted session with mask NPY files for each bundle
    returns
    -------
    mask_dict : dict, containing unique tetrodes for the session & mask info for bundles with
    cells, along with array for common time fram for spks & beh. True = Masked, False = Nonmasked
    """

    if os.path.exists(os.path.join(sess_path, 'selective_mask_dict.pkl')):
        print("Loading existing mask_dict...")
        with open(os.path.join(sess_path, 'selective_mask_dict.pkl'), 'rb') as fh:
            mask_dict = pickle.load(fh)
        print("Done loading.")

    else:
        print("Creating mask_dict...")
    # intialize space
        mask_dict = {}

        # deal with multiple cells on one tetrode
        unique_trodes = np.unique(spks_dict['trode_nums'])
        unique_trodes.sort()
        mask_dict['uniq_trodes'] = unique_trodes

        for trode in unique_trodes:

            # determine (unefficiently) which mask file is correct
            if trode <= 8:
                bndl = "bundle1_mask_info"
            elif trode > 8 <= 16:
                bndl = "bundle2_mask_info"
            elif trode > 16 <= 24:
                bndl = "bundle3_mask_info"
            elif trode > 24 <= 32:
                bndl = "bundle4_mask_info"
            else:
                print("trode not between 1-32, function will break")

            # load it, flatten & convert to bool (0.0 = noise, 1.0 = signal)
            print("loading mask info....")
            bndl_mask = np.load(os.path.join(sess_path, bndl))
            bndl_mask = bndl_mask.flatten()
            bndl_mask_bool = np.where(bndl_mask == 0.0, True, False)
            mask_dict[bndl]= bndl_mask_bool
            print('mask info loaded')

        # update dictionary with time alignment array
        mask_fsm = mask2fsm(spks_dict, mask_dict)
        mask_dict['mask_fsm'] = mask_fsm

        # save out
        output = open(os.path.join(sess_path, 'selective_mask_dict.pkl'), 'wb')
        pickle.dump(mask_dict, output)
        output.close()

    return mask_dict

def mask2fsm(spks_dict, mask_dict):
    """
    Quick function to use shape of boolean mask to create a second array in fsm time
    to allow for a 'common' timeframe between task events and ephys masking. Eventually
    this should be extracted from trodes. Returns an appended mask_dict
    """
    # organize & assign
    fs = spks_dict['fs']
    key = list(mask_dict)[1] # grab mask info for first bundle in list
    total_samples = len(mask_dict[key])

    # create a array the same length of the bool with values in seconds at fs
    mask_sec = np.linspace(0, total_samples/fs, total_samples)

    # convert the time array above from spk time to fsm time
    mask_fsm = (mask_sec * spks_dict['spk2fsm'][0]) + spks_dict['spk2fsm'][1]

    return mask_fsm

def det_samples_masked(mask_dict, beh_df):
    """
    Function that determines how many samples were masked for each bundle between c_poke
    and aud2_off
    inputs
    ------
    mask_dict : dict, created in load_masks() and mask2fsm()
    beh_df : dataframe created in make_beh_df()
    returns
    -------
    all_samples_masked : list, [n_bundle][n_trial] containing number of samples masked per
                         trial between c_poke and aud2_off
    """
    # --- data frame prep
    # get only trials without violatios
    no_viol_df = beh_df[beh_df['hit_hist'] != 'viol']

    # grab start and stop indicies for window
    start = no_viol_df['c_poke']
    end = no_viol_df['aud2_off']

    # --- determining masks
    # determine where masks are, store keys for them
    mask_keys = []
    for f in range(1,5):
        key = "bundle{}_mask_info".format(f)
        if key in mask_dict:
            mask_keys.append(key)

    # --- extract masks using df trial times
    all_samples_masked = []

    # iterate over masks
    for mask in mask_keys:

        bndl_samples_masked = []

        # iterate over each trial
        for trial, row in no_viol_df.iterrows():

            # find time closesd to start & stop for each trial, return the idx in mask_fsm
            idx_s = np.searchsorted(mask_dict['mask_fsm'], start[trial], side = "left")
            idx_e = np.searchsorted(mask_dict['mask_fsm'], end[trial], side = "left")

            # use these indices to go back into trodes_time for each mask
            bndl_samples_masked.append(np.sum(mask_dict[mask][idx_s:idx_e]))

        all_samples_masked.append(bndl_samples_masked)

    return all_samples_masked, mask_keys

def find_unmasked_idx(all_samples_masked, threshold=1000):
    """
    Function to find behavior trial indices where masking is < threshold
    inputs
    ------
    all_samples_masked  : list, created in det_samples_masked()[n_bndl][n_trial]
    threshold (optional): int, specifying maximum n samples masked for a 'good' trial
    returns
    -------
    all_unmasked_idxs : list, [n_bundle][n__good_trial] containing indices for trials that
                        have masking below the threshold & can be used for analysis
    """
    # initialize
    all_unmasked_idxs = []

    # iterate over each bundle
    for bndl in range(len(all_samples_masked)):
        bndl_unmasked_idxs = []

        # if a trial has less than threshold # samples masked, grab the index
        for trial in range(len(all_samples_masked[bndl])):

            if (all_samples_masked[bndl][trial]) < threshold:
                bndl_unmasked_idxs.append(trial)

        all_unmasked_idxs.append(bndl_unmasked_idxs)

    return all_unmasked_idxs

def make_unmasked_dfs(all_unmasked_idxs, mask_keys, beh_df, spks_dict, sess_path, csv_name):
    """
    Function to take the indices where trial masking is below threshold and filter a df
    for each bundle, along with a Nells long list for plotting
    inputs
    ------
    all_masked_idxs : list, indices for filtering df, created by find_unmasked_idx()
    mask_keys       : list, which bundles are being masked, created by det_samples_masked()
    beh_df          : df, created in make_beh_df()
    spks_dict       : dict, created in make_spks_dict()
    sess_path       : str, path to directory for a sorted session where masking info is located &
                      save out will occur
    csv_name        : str, what you want to title the csv, without bndl number. (e.g. 'hit_trials_df')
    returns
    -------
    bndl_dfs        : dict, containing df for each bndl that has a mask
    df_names        : list, Ncells long containing dict keys to access df for each cell
    """
    # initialize
    bndl_dfs = {}
    df_names = []

    # for each cell, filter df & append inf0
    for trode in spks_dict['trode_nums']:

        if trode <= 8:
            idx = mask_keys.index("bundle1_mask_info")
            print("ngood, first:", len(all_unmasked_idxs[idx]))
            bndl1_df = beh_df.iloc[all_unmasked_idxs[idx]]
            bndl_dfs.update({'bndl1_df' : bndl1_df})
            df_names.append('bndl1_df')
            bndl1_df.to_csv(os.path.join(sess_path, 'bndl1_' + csv_name + '.csv'), index=False)

        elif trode > 8 <= 16:
            idx = mask_keys.index("bundle2_mask_info")
            print("ngood, second:", len(all_unmasked_idxs[idx]))
            bndl2_df = beh_df.iloc[all_unmasked_idxs[idx]]
            bndl_dfs.update({'bndl2_df' : bndl2_df})
            df_names.append('bndl2_df')
            bndl2_df.to_csv(os.path.join(sess_path, 'bndl2_' + csv_name + '.csv'), index=False)

        elif trode > 16 <= 24:
            idx = mask_keys.index("bundle3_mask_info")
            bndl3_df = beh_df.iloc[all_unmasked_idxs[idx]]
            bndl_dfs.update({'bndl3_df' : bndl3_df})
            df_names.append('bndl3_df')
            beh_df.to_csv(os.path.join(sess_path, 'bndl3_' + csv_name + '.csv'), index=False)

        elif trode > 24 <= 32:
            idx = mask_keys.index("bundle4_mask_info")
            bndl4_df = beh_df.iloc[all_unmasked_idxs[idx]]
            bndl_dfs.update({'bndl4_df' : bndl4_df})
            df_names.append('bndl4_df')
            beh_df.to_csv(os.path.join(sess_path, 'bndl4_' + csv_name + '.csv'), index=False)

        else:
            print("trode not between 1-32, function will break")

    return bndl_dfs, df_names
