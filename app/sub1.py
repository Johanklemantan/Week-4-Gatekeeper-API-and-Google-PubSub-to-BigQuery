from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
import os
import json
from google.cloud import bigquery
import datetime as dt

project_id = "week-2-de-blank-space-johan"
subscription_id = "subscription-week4subscription"
timeout = 30.0
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message):
    message.ack()
    str_data = str(message.data).replace("\\", "").replace(
        "rn", "").replace("b\'b\'", "").replace("\'\'", "").replace(" ", "")
    json_data = json.loads(str_data)
    insert = [obj for obj in json_data["activities"]
              if obj["operation"] == "insert"]
    delete = [obj for obj in json_data["activities"]
              if obj["operation"] == "delete"]
    for items in range(len(insert)):
        insert[items]['col_names'].append('time')
        insert[items]['col_types'].append('STRING')
        insert[items]['col_values'].append(str(dt.datetime.now()))
        for k in range(len(insert[items]["col_types"])):
            if insert[items]['col_types'][k] == 'TEXT':
                insert[items]['col_types'][k] = 'STRING'
    for items2 in range(len(delete)):
        for l in delete[items2]['old_value']['col_types']:
            if l == 'TEXT':
                l = 'STRING'
    client = bigquery.Client()
    for j in range(len(insert)):
        tables = client.list_tables(project_id + ".week_4")
        bq_table_name = [table.table_id for table in tables]
        table_id = project_id + ".week_4." + insert[j]["table"]
        ins = {}
        for i in range(len(insert[j]["col_names"])):
            ins[insert[j]["col_names"][i]] = insert[j]["col_values"][i]
        rows_to_insert = [ins]
        if insert[j]['table'] in bq_table_name:
            print(client.insert_rows_json(table_id, rows_to_insert))
            print(client.insert_rows_json(table_id, rows_to_insert)
                  [0]['errors'][0]['location'])
            if client.insert_rows_json(table_id, rows_to_insert)[0]['errors'][0]['message'] == \
                    f"no such field: {client.insert_rows_json(table_id, rows_to_insert)[0]['errors'][0]['location']}.":
                table = client.get_table(table_id)
                new_column = client.insert_rows_json(table_id, rows_to_insert)[
                    0]['errors'][0]['location']
                col_names = insert[j]["col_names"]
                col_types = insert[j]["col_types"]
                original_schema = table.schema
                new_schema = original_schema[:]
                new_schema.append(bigquery.SchemaField(
                    new_column, col_types[col_names.index(new_column)]))
                table.schema = new_schema
                table = client.update_table(table, ["schema"])
                if len(table.schema) == len(original_schema) + 1 == len(new_schema):
                    print("A new column has been added.")
                else:
                    print("The column has not been added.")
            else:
                client.insert_rows_json(table_id, rows_to_insert)
        else:
            schema = []
            for i in range(len(insert[j]["col_names"])):
                field = bigquery.SchemaField(
                    insert[j]["col_names"][i], insert[j]["col_types"][i])
                schema.append(field)
            table = bigquery.Table(table_id, schema=schema)
            table = client.create_table(table)
            print(
                f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
            errors = client.insert_rows_json(
                f"{table.project}.{table.dataset_id}.{table.table_id}", rows_to_insert)
            if errors == []:
                print("New rows have been added.")
            else:
                print("Encountered errors while inserting rows: {}".format(errors))
    for j in range(len(delete)):
        tables = client.list_tables(project_id + ".week_4")
        bq_table_name = [table.table_id for table in tables]
        table_id = project_id + ".week_4." + delete[j]["table"]
        cond = []
        for i in range(len(delete[j]["old_value"]["col_names"])):
            if str(delete[j]["old_value"]["col_types"][i]) == "TEXT":
                where = str(delete[j]["old_value"]["col_names"][i]) + \
                    " = '" + str(delete[j]["old_value"]["col_values"][i]) + "'"
                cond.append(where)
            else:
                where = str(delete[j]["old_value"]["col_names"][i]) + \
                    " = " + str(delete[j]["old_value"]["col_values"][i])
                cond.append(where)
        condition = ' AND '.join(cond)
        delete_query = f""" DELETE FROM `{table_id}` WHERE {condition}"""
        if delete[j]['table'] in bq_table_name:
            query_job = client.query(delete_query)
            query_job.result()
            print(f"Deletion on {delete[j]['table']} success.")
        else:
            print(f"Table does not exist")


streaming_pull_future = subscriber.subscribe(
    subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")
with subscriber:
    try:
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()
