"""Authors: Cody Baker."""
from datetime import timedelta
from pathlib import Path

import numpy as np
from hdmf.backends.hdf5.h5_utils import H5DataIO
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils import get_base_schema, get_schema_from_hdmf_class
from pynwb import NWBFile, TimeSeries
from pynwb.behavior import SpatialSeries, Position, CompassDirection
from ndx_tank_metadata import LabMetaDataExtension, RigExtension, MazeExtension


class BrodyBehaviorDataInterface(BaseDataInterface):
    """Conversion class for the Brody lab behavioral data."""

    @classmethod
    def get_source_schema(cls):
        """Compile input schemas from each of the data interface classes."""
        # TODO
        raise NotImplementedError("Not built yet!")

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        """Primary conversion function for the custom Brody lab behavioral interface."""
        # TODO
        raise NotImplementedError("Not built yet!")
