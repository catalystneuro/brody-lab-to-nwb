from .neobaseextractor import NeoBaseRecordingExtractor


class SpikeGadgetsRecordingExtractor(NeoBaseRecordingExtractor):

    extractor_name = 'SpikeGadgets'
    mode = 'file'
    installed = True
    NeoRawIOClass = 'SpikeGadgetsRawIO'
