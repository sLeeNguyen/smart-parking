from elasticsearch import Elasticsearch

es = Elasticsearch([{"host": "es-smartparking", "port": 9200, "timeout": 60}])

default_settings = {
    "index": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
    },
}

parking_history_infex_settings = {
    "settings": default_settings,
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "car_id": {"type": "keyword"},
            "time_in": {"type": "date"},
            "time_out": {"type": "date"},
            "user_id": {"type": "keyword"},
            "fees": {"type": "integer"},
        }
    }
}


def init():
    print("elasticsearch setup")
    if not es.indices.exists(index="parking_history"):
        es.indices.create(index="parking_history", body=parking_history_infex_settings)


def index_parking_history(id, car_id, time_in, user_id, **kwargs):
    body = {
        "id": id,
        "car_id": car_id,
        "time_in": time_in,
        "user_id": user_id,
        "time_out": None,
        "fees": None,
    }
    body.update(kwargs)
    return es.index(index="parking_history", body=body, id=id)


def update_parking_history_time_out(id, time_out, fees):
    body_update = {
        "doc": {
            "time_out": time_out,
            "fees": fees
        }
    }
    es.update(index="parking_history", body=body_update, id=id)


def analysis_parking_history(begin_time, end_time, timezone):
    script = {
        "size": 0,
        "aggs": {
            "in_analysis": {
                "filter": {
                    "range": {
                        "time_in": {
                            "gte": begin_time.strftime("%Y-%m-%d"),
                            "lte": end_time.strftime("%Y-%m-%d"),
                            "time_zone": timezone
                        }
                    }
                },
                "aggs": {
                    "group_by_hour": {
                        "terms": {
                            "script": {
                                "lang": "painless",
                                "source": "doc['time_in'].value.withZoneSameInstant(ZoneId.of(\"%s\")).getHour()" % timezone
                            },
                            "min_doc_count": 1,
                            "order": {
                                "_key": "asc"
                            }
                        }
                    }
                }
            },
            "out_analysis": {
                "filter": {
                    "range": {
                        "time_out": {
                            "gte": begin_time.strftime("%Y-%m-%d"),
                            "lte": end_time.strftime("%Y-%m-%d"),
                            "time_zone": timezone
                        }
                    }
                },
                "aggs": {
                    "group_by_hour": {
                        "terms": {
                            "script": {
                                "lang": "painless",
                                "source": "doc['time_out'].value.withZoneSameInstant(ZoneId.of(\"%s\")).getHour()" % timezone
                            },
                            "min_doc_count": 1,
                            "order": {
                                "_key": "asc"
                            }
                        }
                    }
                }
            }
        }
    }
    filter_path = ["aggregations"]
    return es.search(index="parking_history", body=script, filter_path=filter_path)
