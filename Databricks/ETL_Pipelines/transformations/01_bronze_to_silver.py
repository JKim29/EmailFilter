from pyspark.sql.functions import (
    col, to_date, date_format, trim, initcap,
    split, size, when, concat, lit, abs,
    to_timestamp, regexp_extract, coalesce, array_contains
)

catalog = "email_filter"
bronze_schema = "01_bronze"
silver_schema = "02_silver"

# Clean Emails
@dlt.table(
    name=f"{catalog}.{silver_schema}.email",
    comment="Cleaned emails",
    table_properties={
        "quality": "silver"
    }
)

@dlt.expect_all_or_drop({
    "id": "id IS NOT NULL",
})

def email():
    df = dlt.readStream(f"{catalog}.{bronze_schema}.email")

    email_from = trim(coalesce(
        regexp_extract(col("from"), r"<([^>]+)>", 1),
        col("from"),
    ))

    status = when(col("status").contains("UNREAD"), "unread").otherwise("read")

    return(
        df
        .withColumn("date", to_date(col("date")))
        .withColumn("emailFrom", email_from)
        .withColumn("status", status)
        .drop("_rescued_data")
    )