"""Authors: Cody Baker."""
import numpy as np

from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
from h5py import File


class WirelessTetrodeProcessedInterface(BaseDataInterface):
    """Conversion class for the processed data corresponding to the Neuralynx format for the Brody lab."""

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
        mat_file = File(self.source_data["file_path"], mode="r")
        trial_info = mat_file["Msorted"]["Trials"]
        trial_type = [chr(x) for x in trial_info["trial_type"][0]]
        n_trials = len(trial_type)

        nwbfile.add_trial_column(name="trial_type", description="The identifier value for the trial type.")
        for k in range(n_trials):
            nwbfile.add_trial(
                start_time=np.nan,
                stop_time=np.nan,
                trial_type=trial_type[k]
            )
