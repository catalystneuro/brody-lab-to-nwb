"""Authors: Cody Baker."""
import numpy as np

from h5py import File
from pynwb import NWBFile
from nwb_conversion_tools.basedatainterface import BaseDataInterface


class MSortedProcessedInterface(BaseDataInterface):
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

    def get_metadata(self):
        mat_file = File(self.source_data["file_path"], mode="r")

        metadata = dict(
            NWBFile=dict(session_id=str(round(mat_file["Msorted"]["sessid"][0][0]))),
            Subject=dict(subject_id="".join([chr(x[0]) for x in mat_file["Msorted"]["rat"][()]]))
        )
        return metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        mat_file = File(self.source_data["file_path"], mode="r")
        side_mapping = dict(l="left", r="right", f="front")

        mat_data = dict(
            start_times=mat_file["Msorted"]["Trials"]["stateTimes"]["sending_trialnum"][0],
            stop_times=mat_file["Msorted"]["Trials"]["stateTimes"]["cleaned_up"][0],
            trial_type=[chr(x) for x in mat_file["Msorted"]["Trials"]["trial_type"][0]],
            violated=mat_file["Msorted"]["Trials"]["violated"][0].astype(bool),
            is_hit=mat_file["Msorted"]["Trials"]["is_hit"][0].astype(bool),
            side=[side_mapping[chr(x)] for x in mat_file["Msorted"]["Trials"]["sides"][0]],
            gamma=mat_file["Msorted"]["Trials"]["gamma"][0],
            reward_location=mat_file["Msorted"]["Trials"]["reward_loc"][0],
            poked_r=mat_file["Msorted"]["Trials"]["pokedR"][0],
            stim_dur_s=mat_file["Msorted"]["Trials"]["stim_dur_s"][0],
            click_diff_hz=mat_file["Msorted"]["Trials"]["stim_dur_s"][0]
        )

        times_column_descriptions = dict(
            wait_for_cpoke="",  # TODO
            cpoke_in="",  # TODO
            cpoke_out="",  # TODO
            clicks_on="",  # TODO
            clicks_off="",  # TODO
            spoke="",  # TODO
            right_reward="The time when right reward occured in seconds.",
            left_reward="The time when left reward occured in seconds.",
            error="The time when error occured in seconds."
        )
        times_column_descriptions.update({"break": ""})  # TODO
        for col, description in times_column_descriptions.items():
            name = f"{col}_time"
            mat_data.update({name: mat_file["Msorted"]["Trials"]["stateTimes"][col][0]})
            nwbfile.add_trial_column(name=name, description=description)

        column_descriptions = dict(
            trial_type="The identifier value for the trial type.",
            violated="Binary identifier value for trial violation.",
            is_hit="Binary identifier value for trial hits.",
            side="Left or right.",
            gamma="",  # TODO
            reward_location="Location of the reward.",
            poked_r="",  # TODO
            stim_dur_s="Duration of stimuli in seconds.",
            click_diff_hz=""  # TODO
        )
        for col, description in column_descriptions.items():
            nwbfile.add_trial_column(name=col, description=description)

        side_mapping = dict(l="left", r="right")
        n_trials = len(mat_data["trial_type"])
        add_pharma = mat_file["Msorted"]["Trials"]["pharma"]["manip"].shape == (1, n_trials)
        add_laser = any(mat_file["Msorted"]["Trials"]["laser"]["isOn"][0])

        if add_pharma:
            mat_data.update(
                pharma_manipulation=mat_file["Msorted"]["Trials"]["pharma"]["manip"],
                pharma_injector_mm=mat_file["Msorted"]["Trials"]["pharma"]["injector_mm"][0],
                pharma_dose_ng=mat_file["Msorted"]["Trials"]["pharma"]["doseNG"][0]
            )

            pharma_column_descriptions = dict(
                manip="Pharmacological manipulation.",
                injector_mm="",  # TODO
                dose_ng=""  # TODO
            )
            for col, description in pharma_column_descriptions.items():
                name = f"pharma_{col}"
                nwbfile.add_trial_column(name=name, description=description)
        if add_laser:
            mat_data.update(
                laser_is_on=mat_file["Msorted"]["Trials"]["laser"]["isOn"][0].astype(bool),
                laser_pulse_ms=mat_file["Msorted"]["Trials"]["laser"]["pulseMS"][0],
                laser_freq_hz=mat_file["Msorted"]["Trials"]["laser"]["freqHz"][0],
                laser_latency_ms=mat_file["Msorted"]["Trials"]["laser"]["latencyMS"][0],
                laser_duration_ms=mat_file["Msorted"]["Trials"]["laser"]["durMS"][0],
            )

            laser_column_descriptions = dict(
                is_on="Whether the laser was enabled or disabled.",
                pulse_ms="",  # TODO
                freq_hz="",  # TODO
                latency_ms="",  # TODO
                duration_ms="",  # TODO
            )
            for col, description in laser_column_descriptions.items():
                name = f"laser_{col}"
                nwbfile.add_trial_column(name=name, description=description)
            for x in laser_column_descriptions.keys() - "is_on":  # replace 0.0 with nan when laser is off
                mat_data[f"laser_{x}"][mat_data["laser_is_on"] == 0] = np.nan

        for k in range(n_trials):
            trial_kwargs = dict(start_time=mat_data["start_times"][k], stop_time=mat_data["stop_times"][k])
            for x in times_column_descriptions:
                name = f"{x}_times"
                trial_kwargs.update({name: mat_data[name][k]})
            for x in column_descriptions:
                trial_kwargs.update({x: mat_data[x][k]})
            if add_pharma:
                for x in pharma_column_descriptions:
                    name = f"pharma_{x}"
                    trial_kwargs.update({name: mat_data[name][k]})
            if add_laser:
                for x in laser_column_descriptions:
                    name = f"laser_{x}"
                    trial_kwargs.update({name: mat_data[name][k]})
            nwbfile.add_trial(**trial_kwargs)
