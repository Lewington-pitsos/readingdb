from readingdb.constants import AnnotatorKeys

class Annotator():
    def __init__(
        self,
        annotator_id: str,
        annotator_group: str,
        annotator_type: str,
        user_id: str,
    ) -> None:
        self.annotator_id = annotator_id
        self.annotator_group = annotator_group
        self.user_id = user_id
        self.annotator_type = annotator_type,

    def item_data(self):
        return {
            AnnotatorKeys.ANNOTATOR_ID: self.annotator_id,
            AnnotatorKeys.ANNOTATOR_TYPE: self.annotator_type,
            AnnotatorKeys.ANNOTATOR_GROUP: self.annotator_group,
            AnnotatorKeys.USER_ID: self.user_id,
        }
    