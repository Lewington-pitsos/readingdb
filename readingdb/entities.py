ENTITIES = [
    'LatCrack',
    'LongCrack',
    'CrocodileCrack',
    'Pothole',
    'Lineblur',
    'GoodCondition'
]

ENTITY_CONFS = [f + 'Confidence' for f in ENTITIES]
ENTITY_BIARIES = ['Is' + f + 'Fault' for f in ENTITIES]