from celery.backends.mongodb import MongoBackend
from kombu.exceptions import EncodeError
from pymongo.errors import InvalidDocument


class CustomMongoBackend(MongoBackend):
    def decode(self, data):
        """Decode the result field; handle raw dicts directly."""
        # If `data` is already a dictionary, return it as-is
        if isinstance(data, dict):
            return data

        # Otherwise, use the default decoding process
        return super().decode(data)

    def _store_result(self, task_id, result, state, traceback=None, request=None, **kwargs):
        """Store return value and state of an executed task only if the state is FAILURE."""
        if state != "FAILURE":
            # Skip storing the result if the state is not FAILURE
            return result

        meta = self._get_result_meta(
            result=result,
            state=state,
            traceback=traceback,
            request=request,
            format_date=False,
        )
        # Add the _id for mongodb
        meta["task_id"] = task_id

        try:
            self.collection.replace_one({"task_id": task_id}, meta, upsert=True)
        except InvalidDocument as exc:
            raise EncodeError(exc)

        return result
