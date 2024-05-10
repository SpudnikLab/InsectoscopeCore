# -*- coding: utf-8 -*-
"""process_detect.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/122UvLzoxwGtGlqVZISydSI-9SrqiT5dk
"""

import concurrent.futures
import numpy as np
from python_speech_features import mfcc
from scipy.spatial.distance import euclidean
import os
import pandas as pd
import concurrent.futures
from scipy.io import wavfile
import time
import json
import librosa

# Function to read CSV data
def read_csv(file_path):
    return pd.read_csv(file_path)

# Function to load audio from file
def load_audio(audio_file):
    return wavfile.read(audio_file)

# Function to match IDs with audio file names
def match_audio_files(csv_data, audio_dir):
    id_to_audio = {}
    for index, row in csv_data.iterrows():
        audio_file = os.path.join(audio_dir, f"{row['id']}.wav")
        if os.path.exists(audio_file):
            id_to_audio[row['id']] = audio_file
    return id_to_audio

def compare_audio(new_audio_path, existing_audios, method='mfcc'):
    if not os.path.exists(new_audio_path):
        return False, False, False

    new_sr, new_audio = wavfile.read(new_audio_path)
    min_distance = float('inf')
    closest_match_id = None

    # Calculate MFCC for the new audio
    new_mfcc = mfcc(new_audio, samplerate=new_sr)

    # Define a helper function for calculating similarity
    def calculate_similarity(existing_id, existing_audio_data):
        existing_sr, existing_audio = existing_audio_data
        existing_mfcc = mfcc(existing_audio, samplerate=existing_sr)
        similarity = euclidean(new_mfcc.mean(axis=0), existing_mfcc.mean(axis=0))
        return existing_id, similarity

    # Iterate over existing audios
    with concurrent.futures.ThreadPoolExecutor() as executor:
        similarity_results = list(executor.map(lambda x: calculate_similarity(*x), existing_audios.items()))

    for id_, similarity in similarity_results:
        print("ID: {id_}.similarity:",similarity)
        if similarity == 0.0:
            closest_match_id = id_
            break
        elif similarity < min_distance:
            min_distance = similarity
            closest_match_id = id_

    return closest_match_id, min_distance, new_audio, new_sr

def extract_features(audio_path):
    # Load audio file
    y, sr = librosa.load(audio_path)

    # Extract features (Mel-frequency cepstral coefficients (MFCC))
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)  # Using 40 MFCCs

    # Compute statistical features from MFCCs
    mfccs_mean = np.mean(mfccs, axis=1)
    mfccs_std = np.std(mfccs, axis=1)

    # Concatenate mean and standard deviation to form feature vector
    features = np.concatenate((mfccs_mean, mfccs_std))

    return features

def classify_sound(audio_path):
    # Extract features from the audio
    features = extract_features(audio_path)

    # Define thresholds for distinguishing between human and mosquito sounds
    # Example thresholds, adjust as needed based on your data
    threshold = 1

    # Apply simple rules to classify the sound
    resultAverage = np.mean(features)
    print(resultAverage)
    if resultAverage > threshold:
        return "Audio"
    elif resultAverage < threshold:
        return "Mosquito"

# 1. Membaca data1.csv dan mencari nilai species untuk id 57
def find_species_for_id(file_path, id_value):
    df = pd.read_csv(file_path)
    species_value = df.loc[df['id'] == id_value, 'species'].iloc[0]
    return species_value

def find_data_for_species(file_path, species_name):
    df = pd.read_csv(file_path)
    result = df.loc[df['Species Name'] == species_name, ['Species Name', 'Disease', 'Danger Level']]
    return result.values.tolist()[0] if not result.empty else None

def processDetect(unique_filename):
    start_time = time.time()

    # CSV file location and audio directory
    csv_file = r"E:\KERJA\spudniklab\InsecstopProjeck\data\metadata\data.csv"
    csv_dangerous_species = r"E:\KERJA\spudniklab\InsecstopProjeck\data\metadata\dangerous_species.csv"
    audio_dir = r"E:\KERJA\spudniklab\InsecstopProjeck\data\audio"

    # Read data from CSV
    csv_data = read_csv(csv_file)

    # Match IDs with audio file names
    id_to_audio = match_audio_files(csv_data, audio_dir)

    # Process audio in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        audio_data = {id_: load_audio(audio_file) for id_, audio_file in id_to_audio.items()}

    # Example of new audio
    new_audio_path = os.path.join(r"E:\KERJA\spudniklab\InsecstopProjeck\upload", unique_filename)

    #check sound tyep
    checkSoundtype = classify_sound(new_audio_path)

    print("Sound Type :",checkSoundtype)
    if checkSoundtype == "Audio":
        return json.dumps({"speciesName": "", "similarityValue": 0, "check_dangerous": "", "status": "Sound Type:Audio"})

    # Compare new audio with existing audio
    closest_match_id,similarity,new_audio, new_sr = compare_audio(new_audio_path, audio_data)


    if closest_match_id is False:
        return json.dumps({"speciesName": "", "similarityValue": 0, "check_dangerous": "", "status": "file not found"})


    print("Similarity value:",similarity)
    if closest_match_id:
        print(f"New audio is similar to the species with ID: {closest_match_id}.")
         # Check dangerous or not
        get_speciesname = find_species_for_id(csv_file, closest_match_id)
        print(f"Species untuk ID {closest_match_id}:", get_speciesname)

        check_dangerous = find_data_for_species(csv_dangerous_species, get_speciesname)

        if similarity == 0.0:
            precentageSimilarity = 100
        else:
            precentageSimilarity = round(similarity)+30

        if precentageSimilarity > 100:
            precentageSimilarity = 100
        elif precentageSimilarity < 40:
            return json.dumps({"speciesName": "", "similarityValue": 0, "check_dangerous": "", "status": "Species not found"})

        print("Percentage Similarity value:",precentageSimilarity)

        if check_dangerous:
            print("Species DANGEROUS", get_speciesname, ":", check_dangerous)
            return json.dumps({"speciesName": get_speciesname, "similarityValue": precentageSimilarity, "check_dangerous": check_dangerous, "status": "Species found"})
        else:
            print("Species NOT DANGEROUS ")
            return json.dumps({"speciesName": get_speciesname, "similarityValue": precentageSimilarity, "check_dangerous": "Low", "status": "Species found"})

    else:
        print("No matching species found.")

        return json.dumps({"speciesName": "", "similarityValue": 0, "check_dangerous": "", "status": "Species not found"})

    print("Total time:", time.time() - start_time)

# if __name__ == "__main__":
#     processDetect("310.wav")