from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# 1) Spark session
spark = (
    SparkSession.builder
    .appName("kafka-spark-structured-streaming-demo")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# 2) JSON schema for Kafka 'value'
schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("user",     StringType(), True),
    StructField("event",    StringType(), True),   # e.g., "click","purchase"
    StructField("amount",   DoubleType(), True),   # optional
    StructField("ts",       StringType(), True)    # ISO-8601 string
])

# 3) Read stream from Kafka
raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "events")
    .option("startingOffsets", "earliest")    # dev-friendly
    .option("maxOffsetsPerTrigger", 1000)
    .load()
)

# Cast bytes -> string, parse JSON, convert ts to TimestampType
parsed = (
    raw
    .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING) AS json")
    .select(from_json(col("json"), schema).alias("data"))
    .select("data.*")
    .withColumn("ts", to_timestamp("ts"))
)

# 4) Watermark + dedup (effectively-once with unique event_id)
dedup = (
    parsed
    .withWatermark("ts", "10 minutes")
    .dropDuplicates(["event_id"])
)

# 5) Tumbling window aggregation: counts per event every 10 seconds
agg = (
    dedup
    .groupBy(window(col("ts"), "10 seconds"), col("event"))
    .count()
)

# 6A) Console sink - see changing counts live
console_q = (
    agg.writeStream
    .queryName("console_counts")
    .outputMode("update")
    .format("console")
    .option("truncate", "false")
    .option("numRows", 50)
    .option("checkpointLocation", "./chk/console")
    .start()
)

# 6B) Kafka sink - append finalized window results to 'events_agg'
to_kafka = (
    agg
    .selectExpr(
        "CAST(event AS STRING) AS key",
        "to_json(named_struct("
        "  'start', CAST(window.start AS STRING),"
        "  'end',   CAST(window.end   AS STRING),"
        "  'event', event,"
        "  'count', count"
        ")) AS value"
    )
    .writeStream
    .queryName("kafka_sink")
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("topic", "events_agg")
    .option("checkpointLocation", "./chk/events_agg")
    .outputMode("append")
    .start()
)

spark.streams.awaitAnyTermination()
