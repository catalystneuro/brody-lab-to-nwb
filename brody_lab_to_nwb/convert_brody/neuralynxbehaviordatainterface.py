"""Authors: Cody Baker."""
import numpy as np

from nwb_conversion_tools.basedatainterface import BaseDataInterface
from pynwb import NWBFile
from h5py import File


class NeuralynxBehaviorDataInterface(BaseDataInterface):
    """Conversion class for the behavioral data corresponding to the Neuralynx format for the Brody lab."""

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
            NWBFile=dict(session_id=str(round(mat_file["Msorted"]["sessid"][()][0][0]))),
            Subject=dict(subject_id="".join([chr(x[0]) for x in mat_file["Msorted"]["rat"][()]]))
        )
        return metadata

    def run_conversion(self, nwbfile: NWBFile, metadata: dict):
        mat_file = File(self.source_data["file_path"], mode="r")
        side_mapping = dict(l="left", r="right", f="front")  # TODO: check on "f"
        mat_data = dict(
            trial_type=[chr(x) for x in mat_file["Msorted"]["Trials"]["trial_type"][0]],
            violated=mat_file["Msorted"]["Trials"]["violated"][()][0],
            is_hit=mat_file["Msorted"]["Trials"]["is_hit"][()][0],
            side=[side_mapping[chr(x)] for x in mat_file["Msorted"]["Trials"]["sides"][0]],
            gamma=mat_file["Msorted"]["Trials"]["gamma"][()][0],
            reward_location=mat_file["Msorted"]["Trials"]["reward_loc"][()][0],
            poked_r=mat_file["Msorted"]["Trials"]["pokedR"][()][0],
            stim_dur_s=mat_file["Msorted"]["Trials"]["stim_dur_s"][()][0],
            click_diff_hz=mat_file["Msorted"]["Trials"]["stim_dur_s"][()][0]
        )
        side_mapping = dict(l="left", r="right")
        n_trials = len(mat_data["trial_type"])
        add_pharma = mat_file["Msorted"]["Trials"]["pharma"]["manip"].shape == (1, n_trials)
        add_laser = any(mat_file["Msorted"]["Trials"]["laser"]["isOn"][()][0])

        nwbfile.add_trial_column(name="trial_type", description="The identifier value for the trial type.")
        nwbfile.add_trial_column(name="violated", description="Binary identifier value for trial violation.")
        nwbfile.add_trial_column(name="is_hit", description="Binary identifier value for trial hits.")
        nwbfile.add_trial_column(name="side", description="Left or right.")
        nwbfile.add_trial_column(name="gamma", description="")  # TODO
        nwbfile.add_trial_column(name="reward_location", description="Location of the reward.")
        nwbfile.add_trial_column(name="poked_r", description="")  # TODO
        nwbfile.add_trial_column(name="stim_dur_s", description="Duration of stimuli in seconds.")
        nwbfile.add_trial_column(name="click_diff_hz", description="")  # TODO

        if add_pharma:
            mat_data.update(
                pharma_manipulation=mat_file["Msorted"]["Trials"]["pharma"]["manip"],  # TODO, need to test non-none
                pharma_injector_mm=mat_file["Msorted"]["Trials"]["pharma"]["injector_mm"][()][0],
                pharma_dose_ng=mat_file["Msorted"]["Trials"]["pharma"]["doseNG"][()][0]
            )
            nwbfile.add_trial_column(name="pharma_manip", description="Pharmacological manipulation.")
            nwbfile.add_trial_column(name="pharma_injector_mm", description="")  # TODO
            nwbfile.add_trial_column(name="pharma_dose_ng", description="")  # TODO
        if add_laser:
            on_off_mapping = {0: "Off", 1: "On"}
            mat_data.update(
                on_or_off=[on_off_mapping[x] for x in mat_file["Msorted"]["Trials"]["laser"]["isOn"][()][0]],
                laser_pulse_ms=mat_file["Msorted"]["Trials"]["laser"]["pulseMS"][()][0],
                laser_freq_hz=mat_file["Msorted"]["Trials"]["laser"]["freqHz"][()][0],
                laser_latency_ms=mat_file["Msorted"]["Trials"]["laser"]["latencyMS"][()][0],
                laser_duration_ms=mat_file["Msorted"]["Trials"]["laser"]["durMS"][()][0],
                #laser_freq_hz=mat_file["Msorted"]["Trials"]["laser"]["triggerEvent"][()][0],
                #laser_freq_hz=mat_file["Msorted"]["Trials"]["laser"]["brain_area"][()][0],
                #laser_freq_hz=mat_file["Msorted"]["Trials"]["laser"]["laterality"][()][0],
                #laser_freq_hz=mat_file["Msorted"]["Trials"]["laser"]["stim_per"][()][0],
            )
            nwbfile.add_trial_column(name="on_or_off", description="Whether the laser was enabled or disabled.")
            nwbfile.add_trial_column(name="laser_pulse_ms", description="")  # TODO
            nwbfile.add_trial_column(name="laser_freq_hz", description="")  # TODO
            nwbfile.add_trial_column(name="laser_latency_ms", description="")  # TODO
            nwbfile.add_trial_column(name="laser_duration_ms", description="")  # TODO

        for k in range(n_trials):
            trial_kwargs = dict(
                start_time=np.nan,
                stop_time=np.nan,
                trial_type=mat_data["trial_type"][k],
                violated=mat_data["violated"][k],
                is_hit=mat_data["is_hit"][k],
                side=mat_data["side"][k],
                gamma=mat_data["gamma"][k],
                reward_location=mat_data["reward_location"][k],
                poked_r=mat_data["poked_r"][k],
                stim_dur_s=mat_data["stim_dur_s"][k],
                click_diff_hz=mat_data["click_diff_hz"][k]
            )
            if add_pharma:
                trial_kwargs.update(
                    pharma_manipulation=mat_data["pharma_manipulation"][k],
                    pharma_injector_mm=mat_data["pharma_injector_mm"][k],
                    pharma_dose_ng=mat_data["pharma_dose_ng"][k]
                )
            if add_laser:
                trial_kwargs.update(
                    on_or_off=mat_data["on_or_off"][k],
                    laser_pulse_ms=mat_data["laser_pulse_ms"][k],
                    laser_freq_hz=mat_data["laser_freq_hz"][k],
                    laser_latency_ms=mat_data["laser_latency_ms"][k],
                    laser_duration_ms=mat_data["laser_duration_ms"][k]
                )
            nwbfile.add_trial(**trial_kwargs)
