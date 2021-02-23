# -*- coding: utf-8 -*-
"""Da-TACOS Dataset Loader

.. admonition:: Dataset Info
    :class: dropdown

    Da-TACOS: a dataset for cover song identification and understanding. It contains two subsets, 
    namely the benchmark subset (for benchmarking cover song identification systems) and the cover 
    analysis subset (for analyzing the links among cover songs), with pre-extracted features and 
    metadata for 15,000 and 10,000 songs, respectively. The annotations included in the metadata 
    are obtained with the API of SecondHandSongs.com. All audio files we use to extract features 
    are encoded in MP3 format and their sample rate is 44.1 kHz. Da-TACOS does not contain any 
    audio files. For the results of our analyses on modifiable musical characteristics using the 
    cover analysis subset and our initial benchmarking of 7 state-of-the-art cover song identification 
    algorithms on the benchmark subset, you can look at our publication.

    For organizing the data, we use the structure of SecondHandSongs where each song is called a 
    ‘performance’, and each clique (cover group) is called a ‘work’. Based on this, the file names 
    of the songs are their unique performance IDs (PID, e.g. P_22), and their labels with respect 
    to their cliques are their work IDs (WID, e.g. W_14).

    Metadata for each song includes:

    - performance title,
    - performance artist,
    - work title,
    - work artist,
    - release year,
    - SecondHandSongs.com performance ID,
    - SecondHandSongs.com work ID,
    - whether the song is instrumental or not.
    
    In addition, we matched the original metadata with MusicBrainz to obtain MusicBrainz ID (MBID), 
    song length and genre/style tags. We would like to note that MusicBrainz related information is 
    not available for all the songs in Da-TACOS, and since we used just our metadata for matching, 
    we include all possible MBIDs for a particular songs.

    For facilitating reproducibility in cover song identification (CSI) research, we propose a framework 
    for feature extraction and benchmarking in our supplementary repository: acoss. The feature extraction 
    component is designed to help CSI researchers to find the most commonly used features for CSI in a 
    single address. The parameter values we used to extract the features in Da-TACOS are shared in the 
    same repository. Moreover, the benchmarking component includes our implementations of 7 state-of-the-art 
    CSI systems. We provide the performance results of an initial benchmarking of those 7 systems on the 
    benchmark subset of Da-TACOS. We encourage other CSI researchers to contribute to acoss with implementing 
    their favorite feature extraction algorithms and their CSI systems to build up a knowledge base where 
    CSI research can reach larger audiences.

    Pre-extracted features
    ^^^^^^^^^^^^^^^^^^^^^^

    The list of features included in Da-TACOS can be seen below. All the features are extracted with acoss 
    repository that uses open-source feature extraction libraries such as Essentia, LibROSA, and Madmom.

    To facilitate the use of the dataset, we provide two options regarding the file structure.

    1. In da-tacos_benchmark_subset_single_files and da-tacos_coveranalysis_subset_single_files folders, 
    we organize the data based on their respective cliques, and one file contains all the features for 
    that particular song.

    .. code-block:: python

        {
            "chroma_cens": numpy.ndarray,
            "crema": numpy.ndarray,
            "hpcp": numpy.ndarray,
            "key_extractor": {
                "key": numpy.str_,
                "scale": numpy.str_,_
                "strength": numpy.float64
            },
            "madmom_features": {
                "novfn": numpy.ndarray,
                "onsets": numpy.ndarray,
                "snovfn": numpy.ndarray,
                "tempos": numpy.ndarray
            }
            "mfcc_htk": numpy.ndarray,
            "tags": list of (numpy.str_, numpy.str_)
            "label": numpy.str_,
            "track_id": numpy.str_
        }


    2. In da-tacos_benchmark_subset_FEATURE and da-tacos_coveranalysis_subset_FEATURE folders, 
    the data is organized based on their cliques as well, but each of these folders contain only one 
    feature per song. For instance, if you want to test your system that uses HPCP features, you can 
    download da-tacos_benchmark_subset_hpcp to access the pre-computed HPCP features. An example for 
    the contents in those files can be seen below:

    .. code-block:: python

        {
            "hpcp": numpy.ndarray,
            "label": numpy.str_,
            "track_id": numpy.str_
        }

"""
import json
import logging
import os
from typing import Optional, TextIO

import deepdish as dd
from jams import JAMS
import numpy as np

from mirdata import download_utils, jams_utils, core, io

LICENSE_INFO = """
Creative Commons Attribution Non Commercial Share Alike 4.0 International
"""
BIBTEX = """@inproceedings{yesiler2019,
    author = "Furkan Yesiler and Chris Tralie and Albin Correya and Diego F. Silva and Philip Tovstogan and Emilia G{\'{o}}mez and Xavier Serra",
    title = "{Da-TACOS}: A Dataset for Cover Song Identification and Understanding",
    booktitle = "Proc. of the 20th Int. Soc. for Music Information Retrieval Conf. (ISMIR)",
    year = "2019",
    pages = "327--334",
    address = "Delft, The Netherlands"
}"""
REMOTES = {
    "metadata": download_utils.RemoteFileMetadata(
        filename="da-tacos_metadata.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_metadata.zip?download=1",
        checksum="b8aed83c45687a6bac76de3da1799237",
        destination_dir=".",
    ),
    "benchmark_cens": download_utils.RemoteFileMetadata(
        filename="da-tacos_benchmark_subset_cens.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_benchmark_subset_cens.zip?download=1",
        checksum="842a8112d7ece43059d3f04dd4a3ee65",
        destination_dir=".",
    ),
    "benchmark_crema": download_utils.RemoteFileMetadata(
        filename="da-tacos_benchmark_subset_crema.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_benchmark_subset_crema.zip?download=1",
        checksum="c702a3b97a60081311bf8e7fae7b433b",
        destination_dir=".",
    ),
    "benchmark_hpcp": download_utils.RemoteFileMetadata(
        filename="da-tacos_benchmark_subset_hpcp.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_benchmark_subset_hpcp.zip?download=1",
        checksum="f92cf3d00cc3195572381d6bbcc086de",
        destination_dir=".",
    ),
    "benchmark_key": download_utils.RemoteFileMetadata(
        filename="da-tacos_benchmark_subset_key.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_benchmark_subset_key.zip?download=1",
        checksum="f4e6b05fa9ab46002357f371a8b0e97e",
        destination_dir=".",
    ),
    "benchmark_madmom": download_utils.RemoteFileMetadata(
        filename="da-tacos_benchmark_subset_madmom.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_benchmark_subset_madmom.zip?download=1",
        checksum="8beb1d8fa39f95b79d5f502a41fd5f0c",
        destination_dir=".",
    ),
    "benchmark_mfcc": download_utils.RemoteFileMetadata(
        filename="da-tacos_benchmark_subset_mfcc.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_benchmark_subset_mfcc.zip?download=1",
        checksum="a3be0cd80754043a8c238cf501062789",
        destination_dir=".",
    ),
    "coveranalysis_tags": download_utils.RemoteFileMetadata(
        filename="da-tacos_coveranalysis_subset_tags.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_coveranalysis_subset_tags.zip?download=1",
        checksum="4b9d4cd5beca571e1d614c9a77580f8c",
        destination_dir=".",
    ),
    "coveranalysis_cens": download_utils.RemoteFileMetadata(
        filename="da-tacos_coveranalysis_subset_cens.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_coveranalysis_subset_cens.zip?download=1",
        checksum="b141652eb633d3d8086f74b92bd12e14",
        destination_dir=".",
    ),
    "coveranalysis_crema": download_utils.RemoteFileMetadata(
        filename="da-tacos_coveranalysis_subset_crema.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_coveranalysis_subset_crema.zip?download=1",
        checksum="70252fe115e1ab4c4d74698d4ad68f4b",
        destination_dir=".",
    ),
    "coveranalysis_hpcp": download_utils.RemoteFileMetadata(
        filename="da-tacos_coveranalysis_subset_hpcp.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_coveranalysis_subset_hpcp.zip?download=1",
        checksum="961784fc2419214adf05504e9fc56cc2",
        destination_dir=".",
    ),
    "coveranalysis_key": download_utils.RemoteFileMetadata(
        filename="da-tacos_coveranalysis_subset_key.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_coveranalysis_subset_key.zip?download=1",
        checksum="6e72db855bad5805a67382bd318eee9c",
        destination_dir=".",
    ),
    "coveranalysis_madmom": download_utils.RemoteFileMetadata(
        filename="da-tacos_coveranalysis_subset_madmom.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_coveranalysis_subset_madmom.zip?download=1",
        checksum="42482eedfe9d9a8be9db3611b9d343b4",
        destination_dir=".",
    ),
    "coveranalysis_mfcc": download_utils.RemoteFileMetadata(
        filename="da-tacos_coveranalysis_subset_mfcc.zip",
        url="https://zenodo.org/record/3520368/files/da-tacos_coveranalysis_subset_mfcc.zip?download=1",
        checksum="11371910cad7012daaa81a5fe9dfa1c0",
        destination_dir=".",
    ),
}


class Track(core.Track):
    """da_tacos track class

    Args:
        track_id (str): track id of the track

    Attributes:
        subset (str): subset which the track belongs to
        work_id (str): id of work's original track
        label (str): alias of work_id
        performance_id (str): id of cover track
        cens_path (str): cens annotation path
        crema_path (str): crema annotation path
        hpcp_path (str): hpcp annotation path
        key_path (str): key annotation path
        madmom_path (str): madmom annotation path
        mfcc_path (str): mfcc annotation path
        tags_path (str): tags annotation path
        track_id (str): track id
        work_title (str): title of the work
        work_artist (str): original artist of the work
        performance_title (str): title of the performance
        performance_artist (str): artist of the performance
        release_year (str): release year
        is_instrumental (bool): True if the track is instrumental
        performance_artist_mbid (str): musicbrainz id of the performance artist
        mb_performances (dict): musicbrainz ids of performances

    Cached Properties:
        cens (np.ndarray): chroma-cens features
        hpcp (np.ndarray): hpcp features
        key (dict): key data, with keys 'key', 'scale', and 'strength'
        madmom (dict): dictionary of madmom analysis features
        mfcc (np.ndarray): mfcc features
        tags (list): list of tags

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

        self.track_id = track_id
        self._data_home = data_home
        self.cens_path = self.get_path("cens")
        self.crema_path = self.get_path("crema")
        self.hpcp_path = self.get_path("hpcp")
        self.key_path = self.get_path("key")
        self.madmom_path = self.get_path("madmom")
        self.mfcc_path = self.get_path("mfcc")
        self.tags_path = self.get_path("tags")

        self.subset = self.track_id.split("#")[0]
        self.work_id = self.track_id.split("#")[1]
        self.label = self.work_id
        self.performance_id = self.track_id.split("#")[2]

    @property
    def work_title(self) -> str:
        return self._track_metadata.get("work_title")

    @property
    def work_artist(self) -> str:
        return self._track_metadata.get("work_artist")

    @property
    def performance_title(self) -> str:
        return self._track_metadata.get("perf_title")

    @property
    def performance_artist(self) -> str:
        return self._track_metadata.get("perf_artist")

    @property
    def release_year(self) -> str:
        return self._track_metadata.get("release_year")

    @property
    def is_instrumental(self) -> bool:
        return self._track_metadata.get("instrumental") == "Yes"

    @property
    def performance_artist_mbid(self) -> str:
        return self._track_metadata.get("perf_artist_mbid")

    @property
    def mb_performances(self) -> dict:
        return self._track_metadata.get("mb_performances")

    @core.cached_property
    def cens(self) -> Optional[np.ndarray]:
        return load_cens(self.cens_path)

    @core.cached_property
    def crema(self) -> Optional[np.ndarray]:
        return load_crema(self.crema_path)

    @core.cached_property
    def hpcp(self) -> Optional[np.ndarray]:
        return load_hpcp(self.hpcp_path)

    @core.cached_property
    def key(self) -> Optional[dict]:
        return load_key(self.key_path)

    @core.cached_property
    def madmom(self) -> Optional[dict]:
        return load_madmom(self.madmom_path)

    @core.cached_property
    def mfcc(self) -> Optional[np.ndarray]:
        return load_mfcc(self.mfcc_path)

    @core.cached_property
    def tags(self) -> Optional[list]:
        return load_tags(self.tags_path)

    def to_jams(self) -> JAMS:
        """Get the track's data in jams format

        Returns:
            jams.JAMS: the track's data in jams format

        """
        return jams_utils.jams_converter(
            metadata={
                "duration": 0.0,
                "work_id": self.work_id,
                "performance_id": self.performance_id,
                "subset": self.subset,
                "label": self.label,
                "cens": self.cens,
                "crema": self.crema,
                "hpcp": self.hpcp,
                "key": self.key,
                "madmom": self.madmom,
                "mfcc": self.mfcc,
                "tags": self.tags,
            }
        )


@io.coerce_to_string_io
def load_cens(fhandle: TextIO):
    """Load da_tacos cens features from a file

    Args:
        fhandle (str or file-like): File-like object or path to chroma-cens file

    Returns:
        np.ndarray: cens features

    """
    return dd.io.load(fhandle.name)["chroma_cens"]


@io.coerce_to_string_io
def load_crema(fhandle: TextIO):
    """Load da_tacos crema features from a file

    Args:
        fhandle (str or file-like): File-like object or path to crema file

    Returns:
        np.ndarray: crema features

    """
    return dd.io.load(fhandle.name)["crema"]


@io.coerce_to_string_io
def load_hpcp(fhandle: TextIO):
    """Load da_tacos hpcp features from a file

    Args:
        fhandle (str or file-like): File-like object or path to hpcp file

    Returns:
        np.ndarray: hpcp features

    """
    return dd.io.load(fhandle.name)["hpcp"]


@io.coerce_to_string_io
def load_key(fhandle: TextIO):
    """Load da_tacos key features from a file.

    Args:
        fhandle (str or file-like): File-like object or path to key file

    Returns:
        dict: key

    Examples:
        {'key': 'C', 'scale': 'major', 'strength': 0.8449875116348267}

    """
    return dd.io.load(fhandle.name)["key_extractor"]


@io.coerce_to_string_io
def load_madmom(fhandle: TextIO):
    """Load da_tacos madmom features from a file

    Args:
        fhandle (str or file-like): File-like object or path to madmom file

    Returns:
        dict: madmom features, with keys 'novfn', 'onsets', 'snovfn', 'tempos

    """
    return dd.io.load(fhandle.name)["madmom_features"]


@io.coerce_to_string_io
def load_mfcc(fhandle: TextIO):
    """Load da_tacos mfcc from a file

    Args:
        fhandle (str or file-like): File-like object or path to mfcc file

    Returns:
        np.ndarray: mfcc

    """
    return dd.io.load(fhandle.name)["mfcc_htk"]


@io.coerce_to_string_io
def load_tags(fhandle: TextIO):
    """Load da_tacos tags from a file

    Args:
        fhandle (str or file-like): File-like object or path to tags file

    Returns:
        list: tags, in the form [(tag, confidence), ...]

    Example:
        [('rock', '0.127'), ('pop', '0.014'), ...]

    """
    return dd.io.load(fhandle.name)["tags"]


@core.docstring_inherit(core.Dataset)
class Dataset(core.Dataset):
    """
    The Da-TACOS genre dataset
    """

    def __init__(self, data_home=None):
        super().__init__(
            data_home,
            name="da_tacos",
            track_class=Track,
            bibtex=BIBTEX,
            remotes=REMOTES,
            license_info=LICENSE_INFO,
        )

    @core.cached_property
    def _metadata(self):
        metadata_index = {}
        metadata_paths = []
        subsets = ["benchmark", "coveranalysis"]
        for subset in subsets:
            path_subset = os.path.join(
                self.data_home,
                "da-tacos_metadata",
                "da-tacos_" + subset + "_subset_metadata.json",
            )
            if not os.path.exists(path_subset):
                raise FileNotFoundError(
                    "Metadata file {} not found. Did you run .download()?".format(
                        path_subset
                    )
                )

            metadata_paths.append(path_subset)

        for subset, path_subset in zip(subsets, metadata_paths):
            with open(path_subset) as f:
                meta = json.load(f)
            for work_id in meta.keys():
                for performance_id in meta[work_id].keys():
                    track_id = subset + "#" + work_id + "#" + performance_id
                    metadata_index[track_id] = meta[work_id][performance_id]

        return metadata_index

    @core.copy_docs(load_cens)
    def load_cens(self, *args, **kwargs):
        return load_cens(*args, **kwargs)

    @core.copy_docs(load_crema)
    def load_crema(self, *args, **kwargs):
        return load_crema(*args, **kwargs)

    @core.copy_docs(load_hpcp)
    def load_hpcp(self, *args, **kwargs):
        return load_hpcp(*args, **kwargs)

    @core.copy_docs(load_key)
    def load_key(self, *args, **kwargs):
        return load_key(*args, **kwargs)

    @core.copy_docs(load_mfcc)
    def load_mfcc(self, *args, **kwargs):
        return load_mfcc(*args, **kwargs)

    @core.copy_docs(load_madmom)
    def load_madmom(self, *args, **kwargs):
        return load_madmom(*args, **kwargs)

    @core.copy_docs(load_tags)
    def load_tags(self, *args, **kwargs):
        return load_tags(*args, **kwargs)

    def filter_index(self, search_key):
        """Load from da_tacos genre dataset the indexes that match with search_key.

        Args:
            search_key (str): regex to match with folds, mbid or genres

        Returns:
             dict: {`track_id`: track data}

        """
        data = {k: v for k, v in self._index["tracks"].items() if search_key in k}
        return data

    def benchmark_tracks(self):
        """Load from da_tacos dataset the benchmark subset tracks.

        Returns:
            dict: {`track_id`: track data}

        """
        return self.filter_index("benchmark#")

    def coveranalysis_tracks(self):
        """Load from da_tacos dataset the coveranalysis subset tracks.

        Returns:
            dict: {`track_id`: track data}

        """
        return self.filter_index("coveranalysis#")
