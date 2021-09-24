"""Authors: Cody Baker and Jess Breda."""
import numpy as np

from pynwb import NWBFile
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils.json_schema import FilePathType

from .protocol_info_utils import load_behavior, make_beh_df


class ProtocolInfoInterface(BaseDataInterface):
    """Conversion class for behavioral and spiking info contained in a protocol_info.mat file."""

    @classmethod
    def get_source_schema(cls):
        source_schema = dict(
            required=["file_path"],
            properties=dict(
                file_path=dict(
                    type="string",
                    format="file",
                    description="Path to .mat file containing processed data."
                )
            ),
            type="object",
            additionalProperties=False
        )
        return source_schema

    def __init__(self, file_path: FilePathType):
        self.source_data = dict(file_path=file_path)
        behavior_info = load_behavior(self.source_data["file_path"])
        self.behavior_df = make_beh_df(behavior_info)

    def run_conversion(self, nwbfile: NWBFile, metadata: dict, column_map: dict, column_descriptions: dict):
        """
        Convert the values in the behavioral dataframe object to the NWBFile Trials table.

        Parameters
        ----------
        nwbfile : NWBFile
            DESCRIPTION.
        metadata : dict
            DESCRIPTION.
        column_map : dict
            A dictionary mapping the column names in the dataframe to intended column names in the NWBFile Trials table.
            We encourage the user to remap any columns that represent timed events by adding _time or _times
            (for multiple) to the end of the NWBFile name.

            E.g.,
                column_map = dict(hit_hist=hit_history, c_poke=c_poke_time, ...)

            Likewise, if there are any binary conditions, we encourage manipulating the underlying data to be boolean,
            and to change the name of the column to is_* where * is the intended name.

            E.g., if
                self.behavior_df["laser_on"][:] = [1 0 0 1 ...]
            then set
                self.behavior_df["laser_on"][:] = [True False False True ...]
            and
                column_map = dict(laser_on=is_laser_on, ...)
        column_descriptions : dict
            A dictionary pairing the NWBFile column names with string text describing their context in the experiment.
        """
        assert len(column_map) == len(column_descriptions), (
            f"The length of the column_map ({len(column_map)}) does not match the length of "
            f"column_descriptions ({len(column_descriptions)})!"
        )

        for nwb_name, description in column_descriptions.items():
            nwbfile.add_trial_column(name=nwb_name, description=description)

        n_trials = self.behavior_df.shape[0]
        for k in range(n_trials):
            trial_kwargs = dict()
            for mat_name, nwb_name in column_map.items():
                trial_kwargs.update({nwb_name: self.behavior_df[mat_name][k]})
            all_times = trial_kwargs.values()
            trial_kwargs.update(start_time=np.min(all_times), stop_time=np.max(all_times))
