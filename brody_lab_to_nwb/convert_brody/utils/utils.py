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
from spiketoolkit.preprocessing import bandpass_filter, resample

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


def get_lfp(file_or_folder_path: PathType, probe_file_path: OptionalPathType = None, filter_opts: dict = None):
    """
    Make a RecordingExtractor, either by loading the data (SpikeGLX) or running preprocessing.

    Parameters
    ----------
    file_or_folder_path : PathType
        DESCRIPTION.
    probe_file_path : OptionalPathType, optional
        DESCRIPTION. The default is None.
    """
    suffix = Path(file_or_folder_path).suffix
    if suffix == ".bin":  # SpikeGLX automatically stores LFP data
        recording_lfp = SpikeGLXRecordingExtractor(
            file_path=file_or_folder_path.parent / file_or_folder_path.name.replace("ap", "lf")
        )
        return recording_lfp

    if "freq_resample_lfp" in filter_opts:
        freq_resample_lfp = filter_opts["freq_resample_lfp"]
        filter_opts.pop("freq_resample_lfp")
    recording = make_extractor(file_or_folder_path=file_or_folder_path, probe_file_path=probe_file_path)
    recording_lfp = bandpass_filter(recording, **filter_opts)
    recording_lfp = resample(recording=recording_lfp, resample_rate=freq_resample_lfp)
    return recording_lfp
