Kafka + Spark Streaming Demo 🚀
=================================

This is a simple, hands-on lab that shows how to connect Apache Spark Structured Streaming with Apache Kafka using Docker.
It reads events from a Kafka topic called `events`, counts them in 10-second time windows, and writes the results back to another Kafka topic called `events_agg`.

🛠️ What you’ll learn
---------------------
- How to spin up Kafka quickly using Docker  
- How to publish JSON events into Kafka  
- How Spark reads from Kafka in real time  
- How to group events by type (like `click`, `purchase`) and by time windows  
- How Spark writes results back into Kafka  

⚡ Quickstart
-------------

1. Clone this repo:
   git clone https://github.com/<your-username>/kafka-spark-lab.git
   cd kafka-spark-lab

2. Start Kafka with Docker:
   docker compose up -d

   This will start a Kafka broker at `localhost:9092`.

3. Create Kafka topics:
   docker exec -it kafka bash -lc "/opt/bitnami/kafka/bin/kafka-topics.sh --create --topic events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1"
   docker exec -it kafka bash -lc "/opt/bitnami/kafka/bin/kafka-topics.sh --create --topic events_agg --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1"

4. Run the Spark job:
   spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 kafka_stream.py

5. Send some test events 🎯  
   Open a Kafka producer:
   docker exec -it kafka bash -lc "/opt/bitnami/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic events"

   Then paste some JSON lines (timestamps should be current/UTC):
   {"event_id":"e1","user":"u1","event":"click","ts":"2025-08-25T04:10:01Z"}
   {"event_id":"e2","user":"u2","event":"purchase","ts":"2025-08-25T04:10:05Z"}

6. Watch the results:  
   Open another terminal to consume from the aggregated topic:
   docker exec -it kafka bash -lc "/opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic events_agg --from-beginning"

   You’ll see JSON like:
   {"start":"2025-08-25 04:10:00","end":"2025-08-25 04:10:10","event":"click","count":1}
   {"start":"2025-08-25 04:10:00","end":"2025-08-25 04:10:10","event":"purchase","count":1}

🛑 How to stop things
----------------------
- Stop Spark: press Ctrl + C in the Spark terminal.  
- Stop Kafka: docker compose down  

📂 Project Structure
---------------------
kafka-spark-lab/
│── docker-compose.yml   # Spins up Kafka broker
│── kafka_stream.py      # Spark Structured Streaming job
│── README.txt           # This guide
│── chk/                 # Spark checkpoint dirs (auto-created, can be deleted)

💡 Notes
---------
- withWatermark("ts","10 minutes") lets Spark handle slightly late events.  
- dropDuplicates(["event_id"]) ensures each event is counted only once.  
- The Spark console shows live updates; the Kafka sink shows finalized results per window.  

✨ Why this project?
---------------------
This is a learning exercise to understand how Kafka and Spark work together.  
It’s not production-ready — but it’s a solid starting point to explore streaming pipelines.
