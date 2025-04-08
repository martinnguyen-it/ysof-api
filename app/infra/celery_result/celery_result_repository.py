"""CeleryResult repository module"""

from datetime import datetime, timezone
from typing import Any, List

import pymongo

from app.models.celery_result import CeleryResultModel


class CeleryResultRepository:
    def __init__(self):
        pass

    def list(
        self,
        page_index: int = 1,
        page_size: int = 20,
        match_pipeline: dict[str, Any] | None = None,
        sort: dict[str, int] | None = None,
    ) -> list[CeleryResultModel]:
        pipeline = []
        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})

        pipeline.extend(
            [
                {"$sort": sort if sort else {"date_done": -1}},
                {"$skip": page_size * (page_index - 1)},
                {"$limit": page_size},
            ]
        )

        try:
            docs = CeleryResultModel.objects().aggregate(pipeline)
            return [CeleryResultModel.from_mongo(doc) for doc in docs] if docs else []
        except Exception as e:
            print(e)
            return []

    def count_list(
        self,
        match_pipeline: dict[str, Any] | None = None,
    ) -> int:
        pipeline = []

        if match_pipeline is not None:
            pipeline.append({"$match": match_pipeline})
        pipeline.append({"$count": "document_count"})

        try:
            docs = CeleryResultModel.objects().aggregate(pipeline)
            return list(docs)[0]["document_count"]
        except Exception:
            return 0

    def mark_resolved_failed(self, task_ids: List[str], is_undo: bool) -> bool:
        try:
            operations = [
                pymongo.UpdateOne(
                    {"task_id": task_id},
                    {"$set": {"resolved": not is_undo, "updated_at": datetime.now(timezone.utc)}},
                    upsert=False,
                )
                for task_id in task_ids
            ]
            CeleryResultModel._get_collection().bulk_write(operations)
            return True
        except Exception:
            return False
