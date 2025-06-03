from app.domain.shared.entity import ImportSpreadsheetsPayload


class RollCallBulkSheet(ImportSpreadsheetsPayload):
    subject_id: str
