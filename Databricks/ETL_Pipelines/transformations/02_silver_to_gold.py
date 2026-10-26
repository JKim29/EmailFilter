import pandas as pd
from pyspark.sql.functions import col, lit, concat, pandas_udf, count, desc, min, max
from typing import Iterator
import random

catalog = "email_filter"
silver_schema = "02_silver"
gold_schema = "03_gold"


@dlt.table(
    name=f"{catalog}.{gold_schema}.unread_aggregated_emails",
    table_properties={
        "quality": "gold"
    }
)

def unread_emails():
    return(
        dlt.read(f"{catalog}.{silver_schema}.email")
        .where(col("status") == "unread")
        .groupBy("emailFrom")
        .agg(
            count("*").alias("unread_count"),
            min(col("date")).alias("min_date"),
            max(col("date")).alias("max_date"),
        )
        .orderBy(desc("unread_count"))
    )

@dlt.table(
    name=f"{catalog}.{gold_schema}.all_aggregated_emails",
    table_properties={
        "quality": "gold"
    }
)
def all_emails():
    return(
        dlt.read(f"{catalog}.{silver_schema}.email")
        .groupBy("emailFrom", "status")
        .agg(
            count("*").alias("total_count"),
            min(col("date")).alias("min_date"),
            max(col("date")).alias("max_date"),
        )
        .orderBy(desc("unread_count"))
    )
