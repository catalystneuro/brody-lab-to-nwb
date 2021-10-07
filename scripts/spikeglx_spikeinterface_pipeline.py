# SpikeInterface pipeline for Brody Lab

from pathlib import Path
from pprint import pprint

import spikeextractors as se
import spiketoolkit as st
import spikesorters as ss


n_jobs = 4
chunk_mb = 2000
export_raw_to_phy = False
export_curated_to_phy = True

# Define sorter and params

sorter = "ironclust"
sorter_params = {}


# on the cluster it's better to point to the sorter inside the script
ss.IronClustSorter.set_ironclust_path("/Users/abuccino/Documents/Codes/spike_sorting/sorters/ironclust")
# ss.Kilosort2Sorter.set_kilosort2_path("$HOME/Documents/Codes/spike_sorting/sorters/kilsort2")

# sorter_params = dict(car=False, n_jobs_bin=n_jobs, chunk_mb=chunk_mb)

# Auto curation params

# (Use None to skip one of the curation steps)
isi_violation_threshold = 0.5
snr_threshold = 5
firing_rate_threshold = 0.1

# 1a) Load AP recordings, LF recordings and TTL signals

base_path = Path("/Users/abuccino/Documents/Data/catalyst/brody")
raw_data_path = base_path
session_name = "test_session"
ap_bin_path = Path("/Users/abuccino/Documents/Data/catalyst/brody/test_npix/LRKV_210217_g2_t0.imec0.ap.bin")
lf_bin_path = ap_bin_path.parent / ap_bin_path.name.replace("ap", "lf")
# ap_bin_path = raw_data_path / session_name / f"{session_name}_imec0" / f"{session_name}_g0_t0.imec0.ap.bin"
# lf_bin_path = ap_bin_path.parent / ap_bin_path.name.replace("ap", "lf")


# Make spikeinterface folders

recording_folder = raw_data_path / session_name
spikeinterface_folder = recording_folder / "spikeinterface"
spikeinterface_folder.mkdir(parents=True, exist_ok=True)

# (optional) stub recording for fast testing; set to False for running processing pipeline on entire data

stub_test = True
nsec_stub = 5

recording_ap = se.SpikeGLXRecordingExtractor(ap_bin_path)
recording_lf = se.SpikeGLXRecordingExtractor(lf_bin_path)

if stub_test:
    print("Stub test! Clipping recordings!")
    recording_ap = se.SubRecordingExtractor(recording_ap,
                                            end_frame=int(nsec_stub * recording_ap.get_sampling_frequency()))
    recording_lf = se.SubRecordingExtractor(recording_lf,
                                            end_frame=int(nsec_stub * recording_lf.get_sampling_frequency()))

print(f"Sampling frequency AP: {recording_ap.get_sampling_frequency()}")
print(f"Sampling frequency LF: {recording_lf.get_sampling_frequency()}")

# 2) Pre-processing

apply_cmr = True

if apply_cmr:
    recording_processed = st.preprocessing.common_reference(recording_ap)
else:
    recording_processed = recording_ap

num_frames = recording_processed.get_num_frames()

# rates, amps = st.postprocessing.compute_channel_spiking_activity(
#     recording_processed,
#     n_jobs=16,
#     chunk_mb=4000,
#     start_frame=10 * 30000,
#     end_frame=20 * 30000,
#     detect_threshold=8,
#     recompute_info=True,
#     verbose=True
# )
# 
# 
# fig, axs = plt.subplots(ncols=2)
# sw.plot_activity_map(recording_processed, activity="rate", colorbar=True, ax=axs[0])
# sw.plot_activity_map(recording_processed, activity="amplitude", colorbar=True, ax=axs[1])


# 3) Run spike sorter
print(f"Running {sorter}")
sorting = ss.run_sorter(sorter, recording_processed, output_folder=spikeinterface_folder / sorter / "output",
                        verbose=True, **sorter_params)

# 4) Post-processing: extract waveforms, templates, quality metrics, extracellular features

# Set postprocessing parameters

# Post-processing params
postprocessing_params = st.postprocessing.get_postprocessing_params()
pprint(postprocessing_params)

# (optional) change parameters
postprocessing_params['max_spikes_per_unit'] = 1000  # with None, all waveforms are extracted
postprocessing_params['n_jobs'] = n_jobs  # n jobs
postprocessing_params['chunk_mb'] = chunk_mb  # max RAM usage in Mb
postprocessing_params['verbose'] = True  # max RAM usage in Mb

# Set quality metric list

# Quality metrics
# qc_list = st.validation.get_quality_metrics_list()
# print(f"Available quality metrics: {qc_list}")

# (optional) define subset of qc
qc_list = ['snr', 'isi_violation', 'firing_rate']

# Set extracellular features

# Extracellular features
ec_list = st.postprocessing.get_template_features_list()
print(f"Available EC features: {ec_list}")

# (optional) define subset of ec
ec_list = None  #['peak_to_valley', 'halfwidth']


# Postprocess all sorting outputs

tmp_folder = spikeinterface_folder / sorter / "tmp"
tmp_folder.mkdir(parents=True, exist_ok=True)

# set local tmp folder
sorting.set_tmp_folder(tmp_folder)

# compute waveforms
waveforms = st.postprocessing.get_unit_waveforms(recording_processed, sorting, **postprocessing_params)

# compute templates
templates = st.postprocessing.get_unit_templates(recording_processed, sorting, **postprocessing_params)

# comput EC features
ec = st.postprocessing.compute_unit_template_features(
    recording_processed,
    sorting,
    feature_names=ec_list,
    as_dataframe=True
)

# compute QCs
qc = st.validation.compute_quality_metrics(
    sorting,
    recording=recording_processed,
    metric_names=qc_list,
    as_dataframe=True
)

# export raw to phy
if export_raw_to_phy:
    phy_folder = spikeinterface_folder / sorter / "phy_raw"
    phy_folder.mkdir(parents=True, exist_ok=True)
    st.postprocessing.export_to_phy(recording_processed, sorting, phy_folder,
                                    recompute_info=True)
  
# 5) Automatic curation

# firing rate threshold
if firing_rate_threshold is not None:
    sorting_curated = st.curation.threshold_firing_rates(
        sorting,
        duration_in_frames=num_frames,
        threshold=firing_rate_threshold,
        threshold_sign='less'
    )
else:
    sorting_curated = sorting

# isi violation threshold
if isi_violation_threshold is not None:
    sorting_curated = st.curation.threshold_isi_violations(
        sorting_curated,
        duration_in_frames=num_frames,
        threshold=isi_violation_threshold,
        threshold_sign='greater'
    )
    

# SNR threshold
if snr_threshold is not None:
    sorting_curated = st.curation.threshold_snrs(
        sorting_curated,
        recording=recording_processed,
        threshold=snr_threshold,
        threshold_sign='less'
    )

print(f"{sorter} found {len(sorting_curated.get_unit_ids())} units after auto curation")


# export curated to phy
if export_cutated_to_phy:
    phy_folder = spikeinterface_folder / sorter / "phy_curated"
    phy_folder.mkdir(parents=True, exist_ok=True)
    
    # avoid recomputing waveforms twice
    if export_raw_to_phy:
        recompute_info = False
    else:
        recompute_info = True
        
    st.postprocessing.export_to_phy(recording_processed, sorting_curated, phy_folder, 
                                    recompute_info=recompute_info)


# 7) Save to NWB; writes only the spikes

# The name of the NWBFile containing behavioral or full recording data
nwbfile_path = raw_data_path / session_name / f"{session_name}.nwb"

# Choose the sorting extractor from the notebook environment you would like to write to NWB
chosen_sorting_extractor = sorting_curated

se.NwbSortingExtractor.write_sorting(
    sorting=chosen_sorting_extractor,
    save_path=nwbfile_path,
    overwrite=False  # this appends the file. True would write a new file
)
