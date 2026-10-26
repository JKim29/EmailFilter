from pyspark.sql.functions import regexp_extract
+
+@dlt.table(
+    name="email_data",
+    comment="",
+    table_properties={"quality":"bronze"}
+)
+
+def raw_json():
+    return(
+        spark.readStream.format("cloudFiles")
+            .option("cloudFiles.format", "json")
+            .option("cloudFiles.schemaEvolutionMode", "rescue")
+            .load(f"/Volumes/email_filter/00_landing/raw")
+    )