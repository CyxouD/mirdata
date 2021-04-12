"""
TONAS Loader

.. admonition:: Dataset Info
    :class: dropdown

    This dataset contains a music collection of 72 sung excerpts representative of three a cappella singing styles
    (Deblas, and two variants of Martinete). It has been developed within the COFLA research project context.
    The distribution is as follows:
    1. 16 Deblas
    2. 36 Martinete 1
    3. 20 Martinete 2

    This collection was built in the context of a study on similarity and style classification of flamenco a cappella
    singing styles (Tonas) by the flamenco expert Dr. Joaquin Mora, Universidad de Sevilla.

    We refer to (Mora et al. 2010) for a comprehensive description of the considered styles and their musical
    characteristics. All 72 excerpts are monophonic, their average duration is 30 seconds and there is enough
    variability for a proper evaluation of our methods, including a variety of singers, recording conditions,
    presence of percussion, clapping, background voices and noise. We also provide manual melodic transcriptions,
    generated by the COFLA team and Cristina López Gómez.

    The annotations are represented by specifying the value (in this case, Notes and F0) at the related timestamps.
    TONAS' note and F0 annotations also have "Energy" information, which refers to the average energy value through
    all the frames in which a note or a F0 value is comprised.

    Using this dataset:
    TONAS dataset can be obtained upon request. Please refer to this link: https://zenodo.org/record/1290722 to
    request access and follow the indications of the .download() method for a proper storing and organization
    of the TONAS dataset.

    Citing this dataset:
    When TONAS is used for academic research, we would highly appreciate if scientific publications of works partly
    based on the TONAS dataset quote the following publication:
    - Music material: Mora, J., Gomez, F., Gomez, E., Escobar-Borrego, F.J., Diaz-Banez, J.M. (2010). Melodic
    Characterization and Similarity in A Cappella Flamenco Cantes. 11th International Society for Music Information
    Retrieval Conference (ISMIR 2010).
    - Transcriptions: Gomez, E., Bonada, J. (in Press). Towards Computer-Assisted Flamenco Transcription: An
    Experimental Comparison of Automatic Transcription Algorithms As Applied to A Cappella Singing.
    Computer Music Journal.


"""
import csv
import os
from typing import cast, TextIO, Tuple, Optional

import librosa
import numpy as np

from mirdata import jams_utils, core, annotations, io


BIBTEX = """
Music material:
@inproceedings{tonas_music,
    author = {Mora, Joaquin and Gómez, Francisco and Gómez, Emilia
              and Borrego, Francisco Javier and Díaz-Báñez, José},
    year = {2010},
    month = {01},
    pages = {351-356},
    title = {Characterization and Similarity in A Cappella Flamenco Cantes.}
}

Transcriptions:
@inproceedings{tonas_annotations,
    author = {E. {Gómez} and J. {Bonada}},
    journal = {Computer Music Journal},
    title = {Towards Computer-Assisted Flamenco Transcription: An Experimental 
           Comparison of Automatic Transcription Algorithms as Applied to A 
           Cappella Singing},
    year = {2013},
    volume = {37},
    number = {2},
    pages = {73-90},
    doi = {10.1162/COMJ_a_00180}}
"""


REMOTES = None

DOWNLOAD_INFO = """
        PLEASE READ CAREFULLY ALL THE INFORMATION SO YOU DON'T MISS ANY STEP:
        Unfortunately, the TONAS dataset is not available to be shared openly. However,
        you can request access to the dataset in the following link, providing a brief
        explanation of what your are going to use the dataset for:
        ==> https://zenodo.org/record/1290722
        Then, unzip the dataset, change the dataset name to: "tonas" (with lowercase),
        and locate it to {}. If you unzip it into a different path, please remember to set the 
        right data_home when initializing the dataset.
"""

LICENSE_INFO = """
The TONAS dataset is offered free of charge for internal non-commercial use only. You can not redistribute it nor 
modify it. Dataset by COFLA team. Copyright © 2012 COFLA project, Universidad de Sevilla. Distribution rights granted 
to Music Technology Group, Universitat Pompeu Fabra. All Rights Reserved.
"""


class NoteData(annotations.NoteData):
    """
    This is an extended version of standard NoteData class to support energy annotation.

    Attributes:
        intervals (np.ndarray): (n x 2) array of intervals
            (as floats) in seconds in the form [start_time, end_time]
            with positive time stamps and end_time >= start_time.
        notes (np.ndarray): array of notes (as floats) in Hz
        energies (np.ndarray): array of energies (as floats) of each note
        confidence (np.ndarray or None): array of confidence values
            between 0 and 1

    """

    def __init__(self, intervals, notes, energies, confidence=None):
        super().__init__(intervals, notes, confidence)
        annotations.validate_array_like(energies, np.ndarray, float)
        annotations.validate_lengths_equal([intervals, notes, energies, confidence])
        self.energies = energies


class F0Data(annotations.F0Data):
    """
    This is an extended version of standard F0Data class to support energy and estimated frequency values annotations.

    Attributes:
        times (np.ndarray): array of time stamps (as floats) in seconds
            with positive, strictly increasing values
        automatic_frequencies (np.ndarray): array of automatically extracted frequency values (as floats)
            in Hz
        frequencies (np.ndarray): array of manually corrected frequency values (as floats)
            in Hz
        energies (np.ndarray): array of energi values (as floats)
        confidence (np.ndarray or None): array of confidence values
            between 0 and 1

    """

    def __init__(
        self, times, automatic_frequencies, frequencies, energies, confidence=None
    ):
        super().__init__(times, frequencies, confidence)
        annotations.validate_array_like(automatic_frequencies, np.ndarray, float)
        annotations.validate_array_like(energies, np.ndarray, float)
        annotations.validate_lengths_equal(
            [times, automatic_frequencies, frequencies, energies, confidence]
        )
        self.automatic_frequencies = automatic_frequencies
        self.energies = energies


class Track(core.Track):
    """TONAS track class

    Args:
        track_id (str): track id of the track
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets/TONAS`

    Attributes:
        f0_path (str): local path where f0 melody annotation file is stored
        notes_path(str): local path where notation annotation file is stored
        audio_path(str): local path where audio file is stored
        track_id (str): track id
        singer (str): performing singer (cantaor)
        title (str): title of the track song
        tuning_frequency (float): tuning frequency of the symbolic notation

    Cached Properties:
        melody (F0Data): annotated melody in extended F0Data format
        notes (NoteData): annotated notes

    """

    def __init__(
        self,
        track_id,
        data_home,
        dataset_name,
        index,
        metadata,
    ):
        super().__init__(
            track_id,
            data_home,
            dataset_name,
            index,
            metadata,
        )

        self.f0_path = self.get_path("f0")
        self.notes_path = self.get_path("notes")

        self.audio_path = self.get_path("audio")

    @property
    def style(self):
        return self._track_metadata.get("style")

    @property
    def singer(self):
        return self._track_metadata.get("singer")

    @property
    def title(self):
        return self._track_metadata.get("title")

    @property
    def tuning_frequency(self):
        return _load_tuning_frequency(self.notes_path)

    @property
    def audio(self) -> Tuple[np.ndarray, float]:
        """The track's audio

        Returns:
            * np.ndarray - audio signal
            * float - sample rate

        """
        return load_audio(self.audio_path)

    @core.cached_property
    def f0(self) -> Optional[F0Data]:
        return load_f0(self.f0_path)

    @core.cached_property
    def notes(self) -> Optional[NoteData]:
        return load_notes(self.notes_path)

    def to_jams(self):
        """Get the track's data in jams format

        Returns:
            jams.JAMS: the track's data in jams format

        """
        return jams_utils.jams_converter(
            audio_path=self.audio_path,
            f0_data=[(self.f0, "pitch_contour")],
            note_data=[(self.notes, "note_hz")],
            metadata=self._track_metadata,
        )


def load_audio(fhandle: str) -> Tuple[np.ndarray, float]:
    """Load a TONAS audio file.

    Args:
        fhandle (str): path to an audio file

    Returns:
        * np.ndarray - the mono audio signal
        * float - The sample rate of the audio file

    """
    return librosa.load(fhandle, sr=44100, mono=True)


@io.coerce_to_string_io
def load_f0(fhandle: TextIO) -> Optional[F0Data]:
    """Load TONAS f0 annotations

    Args:
        fhandle (str or file-like): path or file-like object pointing to f0 annotation file

    Returns:
        F0Data: predominant f0 melody

    """
    times = []
    freqs = []
    freqs_corr = []
    energies = []
    confidence = []
    reader = np.genfromtxt(fhandle)
    for line in reader:
        times.append(float(line[0]))
        energies.append(float(line[1]))
        freqs.append(float(line[2]))
        freqs_corr.append(float(line[3]))
        confidence.append(1.0) if float(line[3]) > 0 else confidence.append(0.0)

    return F0Data(
        np.array(times, dtype="float"),
        np.array(freqs, dtype="float"),
        np.array(freqs_corr, dtype="float"),
        np.array(energies, dtype="float"),
        np.array(confidence, dtype="float"),
    )


@io.coerce_to_string_io
def load_notes(fhandle: TextIO) -> Optional[NoteData]:
    """Load TONAS note data from the annotation files

    Args:
        fhandle (str or file-like): path or file-like object pointing to a notes annotation file

    Returns:
        NoteData: note annotations

    """
    intervals = []
    pitches = []
    energy = []
    confidence = []

    reader = csv.reader(fhandle, delimiter=",")
    tuning = next(reader)[0]
    for line in reader:
        intervals.append([line[0], float(line[0]) + float(line[1])])
        # Convert midi value to frequency
        note_hz = _midi_to_hz(float(line[2]), float(tuning))
        pitches.append(note_hz)
        energy.append(float(line[3]))
        confidence.append(1.0)

    note_data = NoteData(
        np.array(intervals, dtype="float"),
        np.array(pitches, dtype="float"),
        np.array(energy, dtype="float"),
        np.array(confidence, dtype="float"),
    )

    return note_data


@io.coerce_to_string_io
def _load_tuning_frequency(fhandle: TextIO) -> float:
    """Load tuning frequency of the track with re

    Args:
        fhandle (str or file-like): path or file-like object pointing to a notes annotation file

    Returns:
        tuning_frequency (float): returns new tuning frequency considering the deviation

    """

    # Compute tuning frequency
    cents_deviation = float(next(csv.reader(fhandle, delimiter=","))[0])
    tuning_frequency = 440 * (
        2 ** (cents_deviation / 1200)
    )  # Frequency of A (common value is 440Hz)

    return tuning_frequency


def _midi_to_hz(midi_note, tuning_deviation):
    """Function to convert MIDI to Hz with certain tuning freq

    Args:
        midi_note (float): note represented in midi value
        tuning_deviation (float): deviation in cents with respect to 440Hz

    Returns:
        (float): note in Hz considering the new tuning frequency

    """
    tuning_frequency = 440 * (
        2 ** (tuning_deviation / 1200)
    )  # Frequency of A (common value is 440Hz)
    return (tuning_frequency / 32) * (2 ** ((midi_note - 9) / 12))


@core.docstring_inherit(core.Dataset)
class Dataset(core.Dataset):
    """
    The TONAS dataset
    """

    def __init__(self, data_home=None):
        super().__init__(
            data_home,
            name="tonas",
            track_class=Track,
            bibtex=BIBTEX,
            remotes=REMOTES,
            download_info=DOWNLOAD_INFO,
            license_info=LICENSE_INFO,
        )

    @core.cached_property
    def _metadata(self):
        metadata_path = os.path.join(self.data_home, "TONAS-Metadata.txt")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError("Metadata not found. Did you run .download()?")

        metadata = {}
        with open(metadata_path, "r", errors="ignore") as f:
            reader = csv.reader(
                (x.replace("\0", "") for x in f), delimiter="\t"
            )  # Fix wrong byte
            for line in reader:
                if line:  # Do not consider empty lines
                    index = line[0].replace(".wav", "")
                    metadata[index] = {
                        "style": line[1],
                        "title": line[2],
                        "singer": line[3],
                    }

        return metadata

    @core.copy_docs(load_audio)
    def load_audio(self, *args, **kwargs):
        return load_audio(*args, **kwargs)

    @core.copy_docs(load_f0)
    def load_f0(self, *args, **kwargs):
        return load_f0(*args, **kwargs)

    @core.copy_docs(load_notes)
    def load_notes(self, *args, **kwargs):
        return load_notes(*args, **kwargs)
