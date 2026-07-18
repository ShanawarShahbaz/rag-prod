"""
Load test for the RAG API's /query endpoint.

Usage (headless, e.g. 5 users, spawn 1/sec, run for 60s):
  locust -f locustfile.py --host http://127.0.0.1:8000 \
    --headless -u 5 -r 1 -t 60s --csv=loadtest_results

Usage (interactive web UI):
  locust -f locustfile.py --host http://127.0.0.1:8000
  then open http://localhost:8089
"""
import random

from locust import HttpUser, between, task

QUESTIONS = [
    "How does self-attention work in transformers?",
    "What is BERT and how is it pretrained?",
    "What is retrieval-augmented generation?",
    "How does chain-of-thought prompting improve reasoning?",
    "What GPU was used to train GPT-3?",
    "What is the code of conduct email for reporting abuse?",
    "What did Alice find when she followed the rabbit?",
    "Who does Mrs. Bennet want Jane to marry?",
    "What is multi-head attention?",
    "How is BERT fine-tuned for downstream tasks?",
]


class RAGUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def query(self):
        question = random.choice(QUESTIONS)
        self.client.post(
            "/query",
            json={"question": question, "top_k": 3, "candidate_k": 20},
            name="/query",
        )
