# Data Service

**English** | [Tiếng Việt](README-vn.md)

> Distributed data infrastructure for the Xime Base Platform — managing object storage, capability-based authorization, shard routing, and data lifecycle.

> 🔒 **Version notice.** This public repository is a **reference / learning edition** and will **soon stop receiving updates**. Active development continues in a **private edition used for commercial purposes**, which includes advanced capabilities not published here. In brief, the private edition adds: multi-level encryption for private data (moving toward end-to-end), a dedicated key-management infrastructure, and a high-performance engine for heavy data processing. The technical details of these features are intentionally **not** part of this public edition.

---

Data Service is one of the core services of the **Xime Base Platform**. It provides a generic, reusable data infrastructure layer for all applications built on the platform — without knowing anything about business domain.

It is also the **first real application built with the [XIME Framework](https://github.com/nguyen-huu-thang/xime-framework)**, serving as a practical validation of the framework in a production-grade microservice context.

```
Application Services (social, ecommerce, SaaS, AI)
               ↓ store / retrieve via object_id
          Data Service       ← manages storage, permission, lifecycle
               ↓
      PostgreSQL + Local Disk
```

---

## What Data Service Does

Everything in the platform is a `DataObject` — image, video, document, dataset, AI artifact, attachment.

Data Service handles:

- **Object storage** — upload, serve, and delete binary content (blob)
- **Metadata management** — object type, visibility, status, versioning
- **Capability-based authorization** — READ, WRITE, DELETE, SHARE, DOWNLOAD per identity
- **Immutable shard routing** — each identity maps to a fixed data shard, forever
- **Data lifecycle** — ACTIVE → ARCHIVED → SOFT_DELETED → PURGED
- **Audit trail** — record every read, write, share, and delete operation
- **Multi-tenant isolation** — per-tenant data context

## What Data Service Does NOT Do

- Does not know that an object is a "profile picture" or a "product image" — that is the application service's responsibility
- Does not call `user-service` or `profile-service` — it only knows `identity_id`
- Does not implement business workflows — it is pure infrastructure

---

## Key Design Decisions

### Identity-Centric Ownership

Every object has an owner. The owner is always an `identity_id` — not a user, profile, or tenant. This keeps Data Service reusable across any subject type: human users, bots, AI agents, service accounts.

### Immutable Data Placement

```
identity_id → hash → partition → data shard (fixed forever)
```

Once an object is created in shard `DATA_SHARD_07`, it stays there permanently. No cross-shard migrations.

### Metadata + Blob Separation

```
PostgreSQL  ←  object metadata (id, owner, permission, status, storage_pointer)
Local Disk  ←  binary content (served via FastAPI with auth check)
```

The database stores only a `storage_pointer` (relative file path), never the binary content.

### Capability-Based Authorization

```
JWT → identity_id → load ACL → evaluate capability → ALLOW / DENY
```

Capabilities: `READ`, `WRITE`, `DELETE`, `SHARE`, `DOWNLOAD`  
Roles: `OWNER`, `EDITOR`, `CONTRIBUTOR`, `VIEWER`

---

## Quick Start

```bash
python -m app.main
```

---

## Architecture

Data Service follows **Hexagonal Architecture** (Ports and Adapters) on top of the XIME Framework:

```
app/
├── api/              ← Adapter layer (REST, gRPC handlers)
├── application/      ← Use cases, ports, DTOs
├── domain/           ← Pure domain model (DataObject, ObjectPermission, ...)
├── infrastructure/   ← SQLAlchemy repositories, local disk storage adapter
├── integration/      ← Identity Service client, Trust Service key sync
└── config/           ← XIME DI binding, routing, security config
```

The XIME Framework handles automatic dependency injection from constructor type hints — no annotations, no decorators, no manual wiring.

---

## Documentation

| Document | Description |
|---|---|
| [Overview](docs/en/overview.md) | Role, boundaries, and position in Base Platform |
| [Architecture](docs/en/architecture.md) | Layer structure, XIME DI, directory layout |
| [Data Model](docs/en/data-model.md) | DataObject model, database schema |
| [Authorization](docs/en/authorization.md) | Capability-based ACL, role model, auth flow |
| [Storage](docs/en/storage.md) | Metadata vs blob separation, local disk storage |
| [Integration](docs/en/integration.md) | Identity Service, Trust Service, JWT verification |

---

## Base Platform Services

| Service | Role |
|---|---|
| `trust-service` | Trust infrastructure — CA, mTLS, JWT signing keys |
| `identity-service` | Authentication infrastructure — JWT, refresh tokens |
| `user-service` | Human Identity Domain Service |
| `data-service` | **Data infrastructure** — object storage, permission |
| `notification-service` | Notification delivery |
| `payment-service` | Payment processing |

---

## XIME Framework

Data Service is the **reference application** for the XIME Framework. It demonstrates:

- Constructor injection with `Protocol`-based ports
- Directory-driven DI with explicit package scanning
- Fail-fast startup validation
- Explicit transaction management
- Hexagonal architecture patterns at production scale

→ [XIME Framework](../xime%20framework/README.md)

---

## Project Status

This public edition has completed 14 implementation phases — domain layer, persistence, authorization, API adapters, JWT verification, testing, and Trust Service integration (mTLS, bootstrap certificate, key sync, schedulers) — and is published as a reference for the XIME Framework.

It will **soon stop being updated**: further development continues in the private commercial edition (see the version notice at the top of this page).

---

## License

MIT
