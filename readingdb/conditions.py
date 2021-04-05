CONDITIONS = [
    "LatCrack",
    "LongCrack",
    "CrocodileCrack",
    "Pothole",
    "Lineblur",
    "GoodCondition"
]

CONDITION_CONFS = [f + "Confidence" for f in CONDITIONS]
CONDITION_BIARIES = ["Is" + f + "Fault" for f in CONDITIONS]