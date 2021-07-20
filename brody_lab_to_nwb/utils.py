"""Authors: Cody Baker."""
from typing import Union, Optional
from pathlib import Path
from re import search
import numpy as np

from spikeextractors import (
    SpikeGLXRecordingExtractor,
    NeuralynxRecordingExtractor,
    MultiRecordingChannelExtractor,
    load_probe_file
)

from .spikegadgestrecordingextractor import SpikeGadgetsRecordingExtractor


PathType = Union[str, Path]
OptionalPathType = Optional[PathType]


def make_nlx_extractor(folder_path: PathType):
    """
    Auxiliary function for robust loading of Neuralynx .ncs files from common folder_path.

    Parameters
    ----------
    folder_path : PathType
        Path to the folder containing the .ncs files to be loaded.
    """
    neuralynx_files = [x for x in Path(folder_path).iterdir() if ".ncs" in x.suffixes]
    file_nums = [int(search(r"\d+$", filename.stem)[0]) for filename in neuralynx_files]
    sort_idx = np.argsort(file_nums)
    sorted_neuralynx_files = (np.array(neuralynx_files)[sort_idx]).tolist()
    return MultiRecordingChannelExtractor(
        [NeuralynxRecordingExtractor(filename=filename) for filename in sorted_neuralynx_files[:4]]
    )


def make_extractor(file_or_folder_path: PathType, probe_file_path: OptionalPathType = None):
    """
    Route the file or folder path to construct the appropriate RecordingExtractor type.

    Intended to simplify the SpikeInterface pipeline notebook across formats.

    Parameters
    ----------
    file_or_folder_path : PathType
        File path to SpikeGLX (ab.bin) or SpikeGadgets (.rec) recording,
        or folder path to collection of Neuralynx (.ncs) files.
    """
    suffix = Path(file_or_folder_path).suffix
    if suffix == ".bin":
        recording = SpikeGLXRecordingExtractor(file_path=file_or_folder_path)
    elif suffix == ".rec":
        recording = SpikeGadgetsRecordingExtractor(filename=file_or_folder_path)
    elif suffix == "":  # neuralynx uses folder format
        recording = make_nlx_extractor(folder_path=file_or_folder_path)
    if probe_file_path is not None:
        recording = load_probe_file(recording=recording, probe_file=probe_file_path)
    return recording
