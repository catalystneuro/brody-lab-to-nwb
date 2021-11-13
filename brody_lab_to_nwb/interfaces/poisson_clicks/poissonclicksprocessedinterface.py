"""Authors: Cody Baker."""
import numpy as np
from scipy.io import loadmat

from pynwb import NWBFile
from nwb_conversion_tools.basedatainterface import BaseDataInterface


class PoissonClicksProcessedInterface(BaseDataInterface):
    """Conversion class for processed behavioral data parsed from raw 'saved history'."""

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

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        mat_file = loadmat(self.source_data["file_path"])
        mat_data = dict(
            start_times=[x[0] for x in mat_file["Trials"]["stateTimes"][0][0]["sending_trialnum"][0][0]],
            stop_times=[x[0] for x in mat_file["Trials"]["stateTimes"][0][0]["cleaned_up"][0][0]],
            trial_type=mat_file["Trials"]["trial_type"][0][0],
            violated=[x[0].astype(bool) for x in mat_file["Trials"]["violated"][0][0]],
            is_hit=[x[0].astype(bool) for x in mat_file["Trials"]["is_hit"][0][0]],
            side=mat_file["Trials"]["sides"][0][0],
            gamma=[x[0] for x in mat_file["Trials"]["gamma"][0][0]],
            reward_location=[x[0] for x in mat_file["Trials"]["reward_loc"][0][0]],
            poked_r=[x[0].astype(bool) for x in mat_file["Trials"]["pokedR"][0][0]],
            click_diff_hz=[x[0] for x in mat_file["Trials"]["click_diff_hz"][0][0]]
        )
        column_descriptions = dict(
            trial_type="The identifier value for the trial type.",
            violated="Binary identifier value for trial violation.",
            is_hit="Binary identifier value for trial hits.",
            side="Left or right.",
            gamma="",  # TODO
            reward_location="Location of the reward.",
            poked_r="",  # TODO
            click_diff_hz=""  # TODO
        )
        for col, description in column_descriptions.items():
            nwbfile.add_trial_column(name=col, description=description)

        n_trials = len(mat_data["trial_type"])

        for k in range(n_trials):
            trial_kwargs = dict(start_time=mat_data["start_times"][k], stop_time=mat_data["stop_times"][k])
            for x in column_descriptions:
                trial_kwargs.update({x: mat_data[x][k]})
            nwbfile.add_trial(**trial_kwargs)
