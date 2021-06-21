from typing import Union
from pathlib import Path
from re import search
import numpy as np

from spikeextractors import SpikeGLXRecordingExtractor, NeuralynxRecordingExtractor, MultiRecordingChannelExtractor

from .spikegadgestrecordingextractor import SpikeGadgetsRecordingExtractor


PathType = Union[str, Path]


def make_nlx_extractor(folder_path: PathType):
    neuralynx_files = [x for x in Path(folder_path).iterdir() if ".ncs" in x.suffixes]
    file_nums = [int(search(r"\d+$", filename.stem)[0]) for filename in neuralynx_files]
    sort_idx = np.argsort(file_nums)
    sorted_neuralynx_files = (np.array(neuralynx_files)[sort_idx]).tolist()
    return MultiRecordingChannelExtractor(
        [NeuralynxRecordingExtractor(filename=filename) for filename in sorted_neuralynx_files]
    )


def make_extractor(file_or_folder_path: PathType):
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
        return SpikeGLXRecordingExtractor(file_path=file_or_folder_path)
    elif suffix == ".rec":
        return SpikeGadgetsRecordingExtractor(filename=file_or_folder_path)
    elif suffix == "":  # neuralynx uses folder format
        return make_nlx_extractor(folder_path=file_or_folder_path)
