# AI Engineering Lab 8 — RAG / Retrieval

**Date:** September 11, 2026  
**Status:** Completed — first-pass scope

## Goal

Understand Retrieval-Augmented Generation (RAG) by building the mechanics directly rather than hiding them behind a framework.

Target flow:

```text
question
  ↓
retrieve relevant knowledge
  ↓
add retrieved knowledge to prompt
  ↓
LLM generates answer from retrieved evidence
  ↓
include source attribution
```

The lab deliberately started with a tiny local knowledge base and progressively improved retrieval so each step was observable.

---

## Initial Knowledge Base

`rag_lab.py` used three small security policy / incident-response statements as stand-ins for real playbooks:

```python
documents = [
    {
        "id": "doc1",
        "text": "Compromised user accounts should have active sessions revoked before password reset."
    },
    {
        "id": "doc2",
        "text": "Private IP addresses should not be submitted to external reputation services."
    },
    {
        "id": "doc3",
        "text": "High-risk account disabling requires human approval before execution."
    }
]
```

These were treated as a miniature IR policy/playbook repository.

---

## Step 1 — Deterministic Keyword Retrieval

The first retriever used explicit keyword checks to make the retrieval boundary obvious.

```text
question
→ deterministic keyword matcher
→ one matching document
→ LLM
```

Example:

```text
What should I do with a compromised user account?
```

retrieved `doc1`, which was then injected into the LLM prompt.

### Key lesson

At this stage:

- retrieval was deterministic/static;
- generation was LLM-based.

The LLM did not choose the document. Python selected the document and supplied it to the model.

### Limitation

A hand-written keyword map does not scale and cannot reliably match semantically equivalent wording.

---

## Step 2 — RAG Answer Function

Added an `answer_with_rag()` flow:

```text
answer_with_rag(question)
→ retrieve(question)
→ retrieved context
→ prompt augmentation
→ LLM answer
```

The prompt instructed the model to answer only from retrieved policy text.

A no-match path returned:

```text
No relevant document found.
```

This prevented the LLM from being called when retrieval found no supporting knowledge.

---

## Step 3 — Word-Frequency Vectors + Cosine Similarity

The keyword matcher was replaced with a simple bag-of-words vector representation.

```text
text
→ tokenize
→ word-frequency vector
→ cosine similarity
```

Cosine similarity was implemented manually for learning purposes.

### Test

Question:

```text
What should I do with a compromised user account?
```

`doc1` received the highest score at about `0.301` and the LLM returned the expected revoke-session guidance.

### Failure test

Question:

```text
What should I do after an account takeover?
```

The simple word-frequency retriever ranked `doc3` highest at about `0.118` instead of `doc1`.

### Key lesson

Cosine similarity alone does not create semantic understanding. The quality of the vector representation matters.

A bag-of-words vector can compare word overlap but does not know that:

```text
account takeover ≈ compromised account
```

---

## Step 4 — Real Embeddings

Added OpenAI embeddings:

```python
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

The embedding model converts text into a high-dimensional numeric vector intended to capture semantic relationships.

The query and documents were embedded into the same vector space and compared with cosine similarity.

### Important conceptual distinction

```text
Embedding model
text → numeric vector

LLM
retrieved context → natural-language reasoning / answer
```

The embedding model is used for retrieval representation. The LLM is used later for generation.

### Embedding Q&A

**Q: Is an embedding represented as a vector?**  
Yes. It is a long ordered list of floating-point values.

**Q: Is it the same thing as the LLM's internal embeddings?**  
No. LLMs internally embed tokens as part of transformer processing, but the RAG application explicitly calls a separate embedding model to create vectors for search/retrieval.

**Q: What happens with a page of text?**  
It can be embedded as one vector, but long inputs can blur multiple topics together. Real RAG systems commonly split larger documents into chunks and embed chunks separately. Chunking was discussed but intentionally not implemented in this first-pass lab.

**Q: Does a security analyst/engineer need to implement cosine similarity manually?**  
No. The concept is more important than memorizing the implementation. Security work benefits more from understanding similarity behavior, thresholds, false matches, missed matches, and retrieval poisoning risks.

---

## Step 5 — Observed Ambiguous Semantic Retrieval

For:

```text
What should I do after an account takeover?
```

semantic embedding retrieval produced approximately:

```text
doc1 ≈ 0.44
doc3 ≈ 0.45
```

`doc3` barely outranked `doc1`.

This was treated as a meaningful result rather than forcing one document to be "correct." Both documents were related to account-response actions, and the query itself was broad.

### Key lesson

Top-1 retrieval can pick a wrong-but-related document when several candidates are semantically close.

---

## Step 6 — Top-K Retrieval

Changed retrieval from one winner to the top two matches:

```text
query
→ score all documents
→ sort descending
→ take top 2
→ give both to LLM
```

This allowed the LLM to see both the account-compromise guidance and the approval requirement instead of forcing a `0.45` vs `0.44` choice.

For the account-takeover question, the generated answer correctly combined:

1. revoke active sessions before password reset (`doc1`);
2. obtain human approval before high-risk account disabling (`doc3`).

---

## Step 7 — Source Attribution

Retrieved context was labeled with document IDs:

```text
[doc1] ...
[doc3] ...
```

The LLM was instructed to cite the document IDs it used.

Observed answer:

```text
After an account takeover:
1. Revoke all active sessions before resetting the password. (doc1)
2. If disabling the account is considered high-risk, obtain human approval before doing so. (doc3)
```

### Key lesson

RAG is more useful when the answer is inspectable. Source attribution provides a way to verify which retrieved evidence supported the generated answer.

---

## Step 8 — Minimum Similarity Threshold

Added a minimum score in addition to top-k ranking:

```python
def retrieve(question, top_k=2, min_score=0.30):
    ...
```

Only candidates above the threshold were returned.

This changed the retrieval behavior from:

```text
always return the least-bad documents
```

to:

```text
return relevant candidates or return nothing
```

### Negative test

Question:

```text
What is our policy for deleting malware samples?
```

returned:

```text
No relevant document found.
```

The `0.30` value was explicitly treated as a lab value, not a universal production threshold. Real thresholds should be tuned against an evaluation set.

---

## Step 9 — Precomputed Document Embeddings

Initially, every question recomputed embeddings for all documents. The lab was improved so document embeddings are computed once:

```python
for doc in documents:
    doc["embedding"] = get_embedding(doc["text"])
```

Each query now only needs a new query embedding, while stored document embeddings are reused.

```text
indexing/startup
→ embed documents once

query time
→ embed question
→ compare against stored vectors
→ retrieve
```

This is much closer to real RAG indexing architecture.

### Q: Are embeddings stable enough to store?

For practical application design, the same text using the same embedding model and settings can be treated as a stable representation for indexing. If the source text changes, or the embedding model/dimensions change, the indexed embedding should be regenerated.

---

## Step 10 — Grounding / Unsupported Detail Test

Question:

```text
After an account takeover, how long should we wait before resetting the password?
```

Scores were approximately:

```text
doc1: 0.5769
doc2: 0.1947
doc3: 0.4586
```

The model answered that the retrieved policies **do not specify a waiting period**, then stated only the supported guidance about revoking sessions before reset and cited `doc1`.

This demonstrated an important distinction:

```text
relevant retrieval ≠ evidence for every requested detail
```

The model should acknowledge missing support instead of inventing a policy value.

---

# Questions and Answers

## Is RAG related to Microsoft Graph?

Microsoft Graph is not RAG itself. It can be a source from which a RAG application retrieves Microsoft 365 content such as SharePoint, OneDrive, Teams, or Outlook data.

```text
Microsoft Graph = how an application accesses M365 data
RAG = how relevant external knowledge is retrieved and supplied to a generative model
```

## Is RAG a bipartite-graph/correlation technique?

No. Graph analytics can be used inside retrieval systems, but RAG means retrieval-augmented generation: retrieve relevant knowledge and provide it to a generative model.

## Does RAG always involve an LLM?

The "generation" side normally involves an LLM or another generative model. Retrieval by itself is information retrieval/search; it becomes RAG when retrieved information augments generation.

## Would scalable retrieval use an LLM to map keywords?

Usually not. A common scalable baseline is:

```text
documents → embeddings → vector index
query → embedding → similarity search → top results → LLM
```

LLMs may later help with query rewriting or reranking, but basic semantic retrieval does not require a full LLM for each match.

## How does this relate to SOAR?

Traditional SOAR is primarily deterministic workflow orchestration and execution:

```text
alert → enrich → branch → action → ticket/notification
```

RAG retrieves knowledge for reasoning:

```text
incident/question → retrieve policy/playbook → LLM interprets evidence
```

A modern security architecture could combine them:

```text
alert
→ SOAR gathers facts
→ RAG retrieves relevant policy/playbook
→ LLM interprets facts + guidance
→ deterministic policy / approval gate
→ SOAR executes approved action
```

Embeddings can help bridge wording differences that rigid text matching may miss—for example `account takeover`, `compromised account`, and `account hijack` may retrieve the same relevant guidance. Embeddings should improve knowledge retrieval, not replace deterministic authorization for high-impact actions.

---

# Security Implications

RAG introduces security and reliability concerns that are distinct from normal LLM prompting:

- wrong-but-related retrieval can ground a model in the wrong policy;
- thresholds that are too low may admit irrelevant evidence;
- thresholds that are too high may miss useful evidence;
- top-1 retrieval can be brittle when several candidates are close;
- retrieved documents themselves can be malicious or poisoned;
- source authorization matters: a user must not retrieve documents they are not allowed to access;
- citations help inspection but do not prove the retrieved source itself is trustworthy;
- an LLM should not convert retrieved guidance directly into privileged actions without deterministic policy/approval controls.

These risks connect RAG directly to AI application security.

---

# What Was Demonstrated vs. Not Yet Demonstrated

## Demonstrated

- local RAG knowledge base;
- deterministic keyword retrieval;
- word-frequency vectors;
- manual cosine similarity;
- failure of lexical vectors on semantic wording;
- OpenAI embedding API use;
- semantic similarity retrieval;
- top-k retrieval;
- minimum similarity threshold;
- source attribution;
- precomputed/stored document embeddings;
- "no relevant source" behavior;
- unsupported-detail grounding test;
- understanding of embedding-vs-LLM responsibilities;
- understanding of RAG/SOAR integration boundaries.

## Not yet demonstrated

- document chunking;
- vector database / approximate nearest-neighbor index;
- FAISS / pgvector / OpenSearch / managed vector service;
- metadata filtering;
- hybrid lexical + semantic retrieval;
- reranking;
- automated retrieval evaluation such as recall@k / hit@k;
- threshold tuning from a labeled evaluation corpus;
- retrieval poisoning tests;
- document-level access control / tenant isolation;
- large realistic corpus;
- production persistence and indexing jobs.

---

# Advanced-Lab Direction

An advanced RAG lab should not consist of manually writing hundreds of documents. A better exercise would use a few realistic IR/security documents that naturally produce roughly 20–30 chunks, then focus on the retrieval pipeline:

```text
real documents
→ chunk
→ embed/index once
→ metadata
→ semantic / hybrid retrieval
→ top-k
→ rerank
→ threshold
→ grounded answer with citations
→ retrieval + generation evaluation
```

The point is to create enough overlap and ambiguity to expose retrieval quality problems without wasting time on data entry.

---

# Strict Progress Assessment

**RAG / Retrieval: 1.5 → 3.0**

Reason: implemented an end-to-end first-pass RAG pipeline with real embeddings, semantic similarity, reusable document indexing, top-k retrieval, thresholding, grounded generation, citation/source IDs, negative retrieval testing, and an unsupported-detail grounding test.

The score remains low-intermediate because the implementation was guided and used only three short documents. No chunking, vector database, metadata filtering, reranking, hybrid retrieval, automated retrieval metrics, or production-scale indexing was implemented.

No other score is increased for this lab to avoid double-counting existing LLM API, evaluation, and security knowledge.