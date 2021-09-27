import numpy as np

import spikeextractors as se


class ksphySortingExtractor(se.SortingExtractor):
    extractor_name = "ksphy"
    is_writable = False

    def __init__(self):
        super().__init__()
        self._units = {}
        self.is_dumpable = False

    def set_sampling_frequency(self, sampling_frequency):
        self._sampling_frequency = sampling_frequency

    def add_unit(self, unit_id, times):
        self._units[unit_id] = dict(times=times)

    def get_unit_ids(self):
        return list(self._units.keys())

    @se.extraction_tools.check_get_unit_spike_train
    def get_unit_spike_train(self, unit_id, start_frame=None, end_frame=None):
        times = self._units[unit_id]["times"]
        inds = np.where((start_frame <= times) & (times < end_frame))[0]
        return np.array(times[inds])
