from readingdb.constants import *



def entry_to_prediction(entry):
    pred = {}

    for f in PredictionReading.FIELDS:
        if f in entry:
            pred[f] = entry[f]

    pred[EntryKeys.TIMESTAMP] = int(entry[EntryKeys.TIMESTAMP])
    
    pred[PredictionReading.BASIS] = {
        PredictionBasis.FILENAME: entry[PredictionBasis.FILENAME] 
    }

    return pred

normalization_map = {
    ReadingTypes.PREDICTION: entry_to_prediction
}

def normalize(entry_type, entry):
    return normalization_map[entry_type](entry)