from readingdb.constants import *

def entry_to_prediction(entry):
    pred = {}

    for f in PredictionReading.FIELDS:
        if f in entry:
            pred[f] = entry[f]
    
    pred[PredictionReading.BASIS] = {
        PredictionBasis.FILENAME: entry[PredictionBasis.FILENAME] 
    }

    return pred