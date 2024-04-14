from bson import ObjectId
from typing import Any
from app.models.manage_form import ManageFormModel
from app.domain.manage_form.entity import FormUpdateWithTime, ManageFormInDB


class ManageFormRepository:
    def __init__(self):
        pass

    def create(self, doc: ManageFormInDB) -> ManageFormModel:
        """
        Create new subject in db
        :param subject:
        :return:
        """
        # create subject instance
        new_doc = ManageFormModel(**doc.model_dump())
        # and save it to db
        new_doc.save()
        return new_doc

    def update(self, id: ObjectId, data: FormUpdateWithTime | dict[str, Any]) -> bool:
        try:
            data = data.model_dump(exclude_none=True) if isinstance(data, FormUpdateWithTime) else data
            ManageFormModel.objects(id=id).update_one(**data, upsert=False)
            return True
        except Exception:
            return False

    def find_one(self, conditions: dict[str, str | bool | ObjectId]) -> ManageFormModel | None:
        try:
            doc = ManageFormModel._get_collection().find_one(conditions)
            return ManageFormModel.from_mongo(doc) if doc else None
        except Exception:
            return None
