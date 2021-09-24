"""Authors: Cody Baker and Jess Breda."""
import numpy as np
import pandas as pd

from pynwb import NWBFile
from nwb_conversion_tools.basedatainterface import BaseDataInterface
from nwb_conversion_tools.utils.json_schema import FilePathType

from .protocol_info_utils import load_nested_mat, load_behavior, make_beh_df

DEFAULT_COLUMN_MAP = dict(a=2)


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

        for nwb_name, nwb_description in zip(column_mapping["nwb_name"], column_mapping["nwb_description"]):
            nwbfile.add_trial_column(name=nwb_name, description=nwb_description)

        n_trials = self.behavior_df.shape[0]
        for k in range(n_trials):
            trial_kwargs = dict()
            for mat_name, nwb_name in zip(column_mapping["mat_name"], column_mapping["nwb_name"]):
                trial_kwargs.update({nwb_name: self.behavior_df[mat_name][k]})
            all_times = [v for k, v in trial_kwargs.items() if "time" in k]
            trial_kwargs.update(start_time=np.min(all_times), stop_time=np.max(all_times))
            nwbfile.add_trial(**trial_kwargs)
