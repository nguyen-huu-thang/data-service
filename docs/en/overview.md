# Overview

**English** | [Tiếng Việt](../vn/overview.md)

---

## What is Data Service?

Data Service is the **distributed data infrastructure** of the Xime Base Platform.

Its role is to provide a single, consistent layer for storing, accessing, and managing any binary data across all applications on the platform — without understanding what that data means in business terms.

```
Application Services
  post-service    → stores post_image_object_id
  product-service → stores product_image_object_id
  chat-service    → stores attachment_object_id
         ↓  (all use object_id references)
    Data Service  ← owns the actual data
         ↓
  PostgreSQL  +  Local Disk
```

---

## Position in Base Platform

The Xime Base Platform is divided into two layers:

### Base Platform (core services)

Generic, reusable, domain-independent services built once and shared across all applications:

| Service | Role |
|---|---|
| `trust-service` | Trust infrastructure — CA, mTLS, JWT signing keys |
| `identity-service` | Authentication — JWT issuance, refresh tokens |
| `user-service` | Human Identity Domain — credentials, profile data |
| `data-service` | **Data infrastructure — this service** |
| `notification-service` | Notification delivery |
| `payment-service` | Payment processing |

### Application Layer (business services)

Application-specific logic that uses Base Platform as a foundation:

- **Social Network**: post-service, comment-service, media-service
- **Ecommerce**: product-service, order-service
- **SaaS / AI**: workspace-service, dataset-service, ai-agent-service

Data Service serves all of these without knowing anything about their domain.

---

## Design Philosophy

| Question | Answer |
|---|---|
| What is Data Service? | Data infrastructure |
| What does it store? | Any binary object — image, video, document, dataset, AI artifact |
| Who is the owner? | Always an `identity_id` (not a user, profile, or business entity) |
| Does it know business context? | No — it only knows ownership, storage, permission, and lifecycle |
| Does it call other domain services? | No — it only integrates with `identity-service` (for JWT) and `trust-service` (for mTLS) |

---

## Core Concepts

### Everything is a DataObject

There are no specialized tables for `image`, `video`, or `document`. Every piece of data is a `DataObject` with a type field. Application services determine the business meaning; Data Service only stores and serves.

### Identity-Centric Ownership

Every object is owned by an `identity_id`. This makes Data Service subject-agnostic — it works the same for human users, bots, AI agents, and service accounts.

### Immutable Data Placement

When an object is created, it is assigned to a shard based on the owner's `identity_id`. That assignment is permanent — the object never migrates to another shard.

```
identity_id → hash → partition → DATA_SHARD_XX  (fixed forever)
```

### Capability-Based Authorization

Access to an object is governed by an Access Control List (ACL). Each entry in the ACL grants a specific role to an identity. Roles map to a set of capabilities.

```
READ, WRITE, DELETE, SHARE, DOWNLOAD
```

### Metadata + Blob Separation

The database stores only metadata and a storage pointer. The actual binary content lives on disk and is served via FastAPI with an authorization check on every request.

---

## What Data Service Is NOT

- Not a social post service — application services hold the business context
- Not a CDN — blob serving is direct with authorization, not optimized for public distribution (yet)
- Not an image processing service — transformation and resizing are application concerns
- Not a search service — it uses a deterministic routing model, not full-text search

---

## Reference Application for XIME Framework

Data Service is the **first production application built with the XIME Framework**. This serves two purposes:

1. **Practical validation** — proves the framework works end-to-end in a real service
2. **Reference implementation** — demonstrates best practices for building services with XIME: hexagonal architecture, constructor injection, explicit bindings, port/adapter pattern

The lessons from building Data Service directly inform XIME Framework's design.
