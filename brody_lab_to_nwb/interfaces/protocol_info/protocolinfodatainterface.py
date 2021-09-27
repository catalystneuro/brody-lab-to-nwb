"""Authors: Cody Baker and Jess Breda."""
import numpy as np
import pandas as pd

from pynwb import NWBFile
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils.json_schema import FilePathType

from .protocol_info_utils import load_nested_mat, make_beh_df


class ProtocolInfoInterface(BaseDataInterface):
    """Conversion class for behavioral info contained in a protocol_info.mat file."""

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
        behavior_info = load_nested_mat(self.source_data["file_path"])["behS"]
        self.behavior_df = make_beh_df(behavior_info)

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        """
        Convert the values in the behavioral dataframe object to the NWBFile Trials table.

        Maps the column names and descriptions via the column_mapping.csv located in the same folder as this interface.
        To add new columns to extract from protocol_info.mat, be sure to add the naming details to the .csv file.
        """
        column_mapping = pd.read_csv("column_mapping.csv", keep_default_na=False)

        # The .csv may contain more fields than were contained in this particular .mat file
        valid_column_mapping = column_mapping[[x in self.behavior_df for x in column_mapping["mat_name"]]]

        for _, row in valid_column_mapping.iterrows():
            nwbfile.add_trial_column(name=row["nwb_name"], description=row["nwb_description"])

        n_trials = self.behavior_df.shape[0]
        for k in range(n_trials):
            trial_kwargs = dict()
            for _, row in valid_column_mapping.iterrows():
                trial_kwargs.update({row["nwb_name"]: self.behavior_df[row["mat_name"]][k]})
            # From conversations with Jess, hard-coding start and stop times relative to shifts of particular columns
            trial_kwargs.update(
                start_time=trial_kwargs["c_poke_time"] - 0.5,
                stop_time=trial_kwargs["end_state_time"] + 1
            )
            nwbfile.add_trial(**trial_kwargs)
