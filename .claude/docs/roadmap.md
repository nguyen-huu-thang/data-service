# Roadmap — Các điểm cần cân nhắc hoàn thiện trong tương lai

> Tài liệu ghi lại các vấn đề kiến trúc và distributed systems có thể cần bổ sung khi hệ thống phát triển lớn hơn.
>
> **Không áp dụng ngay** — cần đánh giá kỹ trước khi triển khai. Ưu tiên phát triển core platform trước.

---

## 1. Service Governance Layer

Hiện tại đã có: service, shard, tenant, routing, distributed placement.

Tương lai có thể cần: service registry, shard registry, service discovery, health management, dynamic routing metadata, configuration distribution.

Các câu hỏi cần trả lời:
- Shard nào đang active / readonly / unhealthy / đang migrate?
- Tenant đang dùng shard nào?
- Service endpoint nào còn hoạt động?

Có thể nghiên cứu: Consul, etcd, ZooKeeper, Kubernetes service discovery.

---

## 2. Event-Driven Architecture

Hiện tại các service chủ yếu dùng RPC / direct call.

Tương lai có thể cần: internal event bus, asynchronous communication, event streaming.

Ví dụ flow:
```
ObjectCreatedEvent → analytics-service, audit-service, notification-service
```

Các vấn đề cần nghiên cứu: eventual consistency, retry, dead-letter queue, event ordering, idempotency, event replay, event versioning.

Có thể nghiên cứu: Kafka, Pulsar, NATS, Redis Streams, RabbitMQ.

---

## 3. Distributed Workflow / Saga

Khi hệ thống có flow nhiều bước (payment, order, inventory) cần cân nhắc: saga pattern, workflow orchestration.

Có thể nghiên cứu: Temporal, Camunda, choreography saga.

---

## 4. Outbox / Inbox Pattern

Database transaction và event publish thường không atomic tuyệt đối.

Giải pháp: lưu event vào database → worker publish sau → retry nếu lỗi.

Mục tiêu: tăng reliability, hỗ trợ eventual consistency, tránh mất dữ liệu.

---

## 5. Observability Platform

Khi số lượng service tăng lớn, debug distributed system sẽ khó hơn.

Cần: centralized logging, distributed tracing, metrics, alerting.

Có thể nghiên cứu: OpenTelemetry, Prometheus, Grafana, Loki, Jaeger.

Các chỉ số cần quan sát: request latency, cross-service tracing, shard health, retry rate, error rate, event lag.

---

## 6. Advanced Search Architecture

Tương lai có thể cần: full-text search, ranking, recommendation, graph traversal, social query.

Có thể nghiên cứu: Elasticsearch, OpenSearch, graph database, CQRS projection.

---

## 7. Advanced Shard Management

Hiện tại đã có: immutable placement, shard growth, soft/hard limit.

Tương lai có thể cần: shard auto provisioning, hot shard detection, geo routing, tenant isolation.

Các bài toán khó: shard split, shard merge, shard migration, multi-region shard.

---

## 8. Multi-Region Architecture

Khi hệ thống phục vụ nhiều khu vực (VN, Singapore, EU, US), cần: region-aware routing, geo replication, regional failover.

---

## 9. Security Hardening

Tương lai có thể cân nhắc: hardware-backed key management (HSM), zero-trust internal communication, PKI automation.

Có thể nghiên cứu: Vault, SPIFFE / SPIRE.

---

## 10. Rate Limiting / Abuse Protection

Khi hệ thống public internet quy mô lớn: rate limiting, bot detection, login brute-force protection, API abuse protection.

---

## 11. Cache Strategy

Khi traffic tăng lớn: distributed cache, cache invalidation, shard-aware cache routing.

Các vấn đề cần nghiên cứu: stale cache, hot key problem, cache eviction strategy.

---

## 12. CQRS / Materialized View

Một số bài toán query lớn (feed generation, analytics, recommendation) có thể cần: CQRS, read model riêng, materialized projection.

**Không nên áp dụng sớm nếu chưa thực sự cần.**

---

## 13. Data Retention / Archival (quan trọng với Data Service)

Khi blob storage tăng lớn: cold storage strategy, archival, historical data retention, backup lifecycle.

---

## Nguyên tắc quan trọng

> Ưu tiên hiện tại: core platform ổn định, service boundary rõ ràng, routing đơn giản, data consistency hợp lý, khả năng scale cơ bản.
>
> Chỉ mở rộng khi: thật sự có bottleneck, có dữ liệu thực tế, có nhu cầu production rõ ràng.
