"""Authors: Jess Breda and Cody Baker."""
import numpy as np
import pandas as pd
import scipy.io as spio


def load_nested_mat(filename):
    """
    Replace scipy.io.loadmat.

    It cures the problem of not properly recovering python dictionaries from mat files.
    It calls the function check keys to cure all entries which are still mat-objects.
    From https://stackoverflow.com/questions/48970785/complex-matlab-struct-mat-file-read-by-python.
    """

    def _check_vars(d):
        """
        Check if entries in dictionary are mat-objects.

        If yes todict is called to change them to nested dictionaries
        """
        for key in d:
            if isinstance(d[key], spio.matlab.mio5_params.mat_struct):
                d[key] = _todict(d[key])
            elif isinstance(d[key], np.ndarray):
                d[key] = _toarray(d[key])
        return d

    def _todict(matobj):
        """Recursive function which constructs from matobjects nested dictionaries."""
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
        Recursive function which constructs ndarray from cellarrays (which are loaded as numpy ndarrays).

        Recurses into the elements if they contain matobjects.
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


def make_beh_df(beh_info):
    """
    Wangle the ndarry from load_behaviorand and put it into a tidy dataframe.

    Parameters
    ----------
    beh_info : ndarray
        Extracted .mat structure.

    Returns
    -------
    beh_df : df (ntrials x items)
        Tidy data frame with behavior information & some relabeling.
    """
    beh_df = pd.DataFrame()
    pd.options.mode.chained_assignment = None

    # assign trail n values
    beh_df['trial_num'] = np.arange(1, beh_info['n_completed_trials'] + 1)

    # rename previous side to be L/R
    prev_side_adj = np.roll(beh_info['prev_side'], 1)  # n-1 trial info
    prev_side_adj = np.where(prev_side_adj == 114, 'RIGHT', 'LEFT')
    prev_side_adj[0] = 'N/A'  # trial 0 doesn't have a previous

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
            aud1_on[trial] = float("NaN")
            aud1_off[trial] = float("NaN")
            aud2_on[trial] = float("NaN")
            aud2_off[trial] = float("NaN")

        elif beh_df['hit_hist'][trial] == 'hit':
            hit_state[trial] = parsed_events_dict[trial]['states']['hit_state'][0]
            aud1_on[trial] = parsed_events_dict[trial]['waves']['stimAUD1'][0]
            aud1_off[trial] = parsed_events_dict[trial]['waves']['stimAUD1'][1]
            aud2_on[trial] = parsed_events_dict[trial]['waves']['stimAUD2'][0]
            aud2_off[trial] = parsed_events_dict[trial]['waves']['stimAUD2'][1]

        elif beh_df['hit_hist'][trial] == 'miss':
            hit_state[trial] = parsed_events_dict[trial]['states']['second_hit_state'][0]
            aud1_on[trial] = parsed_events_dict[trial]['waves']['stimAUD1'][0]
            aud1_off[trial] = parsed_events_dict[trial]['waves']['stimAUD1'][1]
            aud2_on[trial] = parsed_events_dict[trial]['waves']['stimAUD2'][0]
            aud2_off[trial] = parsed_events_dict[trial]['waves']['stimAUD2'][1]

        else:
            raise Exception('hit_hist doesn''t appear to have correct structure (hit, miss, viol)')

    beh_df['c_poke'] = c_poke
    beh_df['end_state'] = end_state
    beh_df['hit_state'] = hit_state
    beh_df['aud1_on'] = aud1_on
    beh_df['aud1_off'] = aud1_off
    beh_df['aud2_on'] = aud2_on
    beh_df['aud2_off'] = aud2_off
    beh_df['end_state'] = end_state

    find_loudness(beh_df)
    find_first_sound(beh_df)

    pd.options.mode.chained_assignment = 'warn'
    return beh_df


def find_loudness(beh_df):
    """
    Quick function for converting from pair history info to determine which sound was louder in a trial.

    Ignores pyschometric trials.
    Pass in beh_df, or any dataframe with 'pair_hist' column to create a new column called loduness.
    """
    conditions = [
        (beh_df['pair_hist'] < 5),
        (beh_df['pair_hist'] >= 5) & (beh_df['pair_hist'] < 9),
        (beh_df['pair_hist'] >= 9)
    ]

    values = ['aud_1', 'aud_2', 'psycho']
    beh_df['louder'] = np.select(conditions, values)


def find_first_sound(beh_df):
    """Quick function for converting from pair history info to determine the loudness of the first sound in a trial."""
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
