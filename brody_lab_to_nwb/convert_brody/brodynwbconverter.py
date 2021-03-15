"""Authors: Cody Baker."""
from pathlib import Path
from typing import Optional, Union
import numpy as np

from nwb_conversion_tools import NWBConverter, SpikeGadgetsRecordingInterface

from .brodybehaviordatainterface import BrodyBehaviorDataInterface

OptionalArrayType = Optional[Union[list, np.ndarray]]
PathType = Union[Path, str]


class BrodysNWBConverter(NWBConverter):
    """Primary conversion class for the Brody lab processing pipeline."""

    data_interface_classes = dict(
        SpikeGadgetsRecording=SpikeGadgetsRecordingInterface,
        Behavior=BrodyBehaviorDataInterface
    )

    def get_metadata(self):
        # TODO
        raise NotImplementedError("Not built yet!")
