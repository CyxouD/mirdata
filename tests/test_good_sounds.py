# -*- coding: utf-8 -*-

import numpy as np

from mirdata.datasets import good_sounds
from tests.test_utils import run_track_tests


def test_track():
    default_trackid = "1"
    data_home = "tests/resources/mir_datasets/good_sounds"
    track = good_sounds.Track(default_trackid, data_home=data_home)

    expected_attributes = {
        'audio_path': 'tests/resources/mir_datasets/good_sounds/good-sounds/sound_files/flute_almudena_reference/akg/0000.wav',
        'track_id': '1'
    }

    expected_property_types = {
        'get_pack_info': dict,
        'get_ratings_info': list,
        'get_sound_info': dict,
        'get_take_info': dict
    }

    run_track_tests(track, expected_attributes, expected_property_types)

    audio, sr = track.audio
    assert sr == 22050, "sample rate {} is not 44100".format(sr)
    assert audio.shape == (176400,), "audio shape {} was not (176400,)".format(
        audio.shape
    )


def test_to_jams():
    data_home = "tests/resources/mir_datasets/good_sounds"
    track = good_sounds.Track("1", data_home=data_home)
    jam = track.to_jams()
    ground_truth_sound = {
                "id": 1,
                "instrument": "flute",
                "note": "C",
                "octave": 4,
                "dynamics": "mf",
                "recorded_at": "2013-10-28 12:00:00.000000",
                "location": "upf studio",
                "player": "almudena",
                "bow_velocity": None,
                "bridge_position": None,
                "string": None,
                "csv_file": 1,
                "csv_id": 1,
                "pack_filename": "0000.wav",
                "pack_id": 1,
                "attack": 105810,
                "decay": 110629,
                "sustain": None,
                "release": 332406,
                "offset": 343765,
                "reference": 1,
                "klass": "good-sound",
                "comments": None,
                "semitone": 48,
                "pitch_reference": 442
    }
    ground_truth_take = {
                "id": 1,
                "microphone": "akg",
                "filename": "tests/resources/mir_datasets/good_sounds/good-sounds/sound_files/flute_almudena_reference/akg/0000.wav",
                "original_filename": "AKG-costado-Left-01 render 001",
                "freesound_id": None,
                "sound_id": 1,
                "goodsound_id": None
    }
    ground_truth_ratings = []
    ground_truth_pack = {
        "id": 1,
        "name": "flute_almudena_reference",
        "description": "Play reference notes"
    }
    assert jam["sandbox"].sound == ground_truth_sound
    assert jam["sandbox"].take == ground_truth_take
    assert jam["sandbox"].pack == ground_truth_pack
    assert jam["sandbox"].ratings == ground_truth_ratings


