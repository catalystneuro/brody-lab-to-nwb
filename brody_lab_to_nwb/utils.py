"""Authors: Cody Baker."""
from typing import Union
from pathlib import Path
from natsort import natsorted

from spikeextractors import NeuralynxRecordingExtractor, MultiRecordingChannelExtractor


PathType = Union[str, Path]


def make_nlx_extractor(folder_path: PathType):
    """
    Auxiliary function for robust loading of Neuralynx .ncs files from common folder_path.

    Parameters
    ----------
    folder_path : PathType
        Path to the folder containing the .ncs files to be loaded.
    """
    neuralynx_files = natsorted([str(x) for x in Path(folder_path).iterdir() if ".ncs" in x.suffixes])
    extractors = [NeuralynxRecordingExtractor(filename=filename, seg_index=0) for filename in neuralynx_files]
    gains = [extractor.get_channel_gains()[0] for extractor in extractors]
    for extractor in extractors:
        extractor.clear_channel_gains()
    recording_extractor = MultiRecordingChannelExtractor(extractors)
    recording_extractor.set_channel_gains(gains=gains)
    return recording_extractor
