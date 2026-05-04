# HIPAA Compliance Considerations

This document describes how Protected Health Information (PHI) flows through the Healthcare RAG system and what would need to change for a production healthcare deployment.

> **Note:** This is a development/study application. The considerations below are documented for awareness — not all are implemented.

---

## How This Application Meets HIPAA Requirements

HIPAA's Security Rule (45 CFR Part 164, Subpart C) defines three categories of safeguards. Below is how each requirement maps to what is **currently implemented** in this application.

### Administrative Safeguards (§ 164.308)

| Requirement | Status | How It's Met |
|-------------|--------|-------------|
| Security management process | Partial | Risk analysis documented in this file (PHI flow mapping, gap analysis). No formal risk management plan. |
| Assigned security responsibility | Not implemented | No designated security officer. Production needs a named individual responsible for HIPAA compliance. |
| Workforce security | Partial | Role-based access (admin/viewer) limits who can upload/delete PHI. No formal onboarding/offboarding procedures. |
| Information access management | Implemented | RBAC enforced via JWT middleware — admin role for write operations, viewer role for read-only. API key support for service accounts. |
| Security awareness training | Not implemented | No training program. Production requires workforce training on PHI handling. |
| Security incident procedures | Not implemented | No incident response plan. Production needs documented procedures for breach detection, containment, notification. |
| Contingency plan | Not implemented | No backup/restore or disaster recovery. In-memory store means all data lost on restart. |
| Evaluation | Partial | Evaluation pipeline tests RAG accuracy. No periodic security evaluation process. |

### Physical Safeguards (§ 164.310)

| Requirement | Status | How It's Met |
|-------------|--------|-------------|
| Facility access controls | N/A (cloud) | Application runs in Docker containers. Production deployment on AWS inherits AWS's SOC 2 / HIPAA physical controls for data centers. |
| Workstation use/security | Not implemented | No policies on where/how the application can be accessed. Production needs endpoint management. |
| Device and media controls | Partial | No persistent media in current design (in-memory store). Pinecone and Bedrock data handled by cloud providers with their own media controls. |

### Technical Safeguards (§ 164.312)

| Requirement | CFR Reference | Status | How It's Met |
|-------------|--------------|--------|-------------|
| **Access controls** | § 164.312(a) | | |
| — Unique user identification | Required | Implemented | Every user has unique `username`. JWT tokens carry `sub` (username) and `jti` (unique token ID). API keys identify services by `service_name`. No shared accounts. |
| — Emergency access procedure | Required | Not implemented | No break-glass account. See Section 2a for production plan. |
| — Automatic logoff | Addressable | Implemented | JWT tokens expire after 60 minutes (`JWT_EXPIRY_MINUTES`). Expired tokens rejected by middleware. Frontend clears session on 401 response. |
| — Encryption/decryption | Addressable | Partial | Bedrock and Pinecone connections use HTTPS (TLS). Local HTTP in dev. Logs use input hashes instead of raw PHI. No application-layer encryption of stored PHI. |
| **Audit controls** | § 164.312(b) | Implemented | Structured JSON logging on every request with: correlation ID, user identity, action, timestamp, duration. LLM calls tracked with: model, tokens, latency, cost, input hash. All logs include correlation IDs for end-to-end request tracing. |
| **Integrity controls** | § 164.312(c) | | |
| — PHI integrity mechanism | Addressable | Not implemented | No checksums, versioning, or tamper detection on stored PHI. See Section 2b for production plan. |
| **Person/entity authentication** | § 164.312(d) | Implemented | JWT-based authentication verifies identity on every API call. Supports both user credentials (username/password → JWT) and service credentials (API key). Tokens are cryptographically signed (HMAC-SHA256). Invalid/expired tokens return 401. |
| **Transmission security** | § 164.312(e) | | |
| — Integrity controls | Addressable | Partial | HTTPS used for all external API calls (Bedrock, Pinecone). Internal Docker network uses HTTP (acceptable for dev, not production). |
| — Encryption | Addressable | Partial | TLS encrypts data to Bedrock and Pinecone. Frontend-to-backend is HTTP in dev. See Section 4 for full encryption details. |

### Summary: What's Implemented vs. What's Not

**Implemented now (in this application):**
- Unique user IDs with JWT authentication (`backend/auth.py`)
- Role-based access control — admin vs. viewer (`backend/auth.py:require_admin`)
- API key authentication for service-to-service calls (`backend/auth.py:API_KEYS`)
- Automatic session expiry via JWT token TTL
- Structured audit logging with correlation IDs (`backend/logging_config.py`)
- LLM call tracking — model, tokens, latency, cost per invocation (`backend/services/rag.py`)
- PHI-safe logging — input hashes logged instead of raw content
- Transmission encryption to external services (Bedrock, Pinecone via HTTPS)
- PHI flow documentation (this file)

**Documented but not implemented (production requirements):**
- Enterprise identity provider with MFA
- Emergency break-glass access procedure
- PHI integrity verification (checksums, versioning, soft-deletes)
- Application-layer encryption of PHI at rest
- TLS for all internal connections
- Immutable audit log storage with 6-year retention
- Signed BAAs with AWS and Pinecone
- Incident response and contingency plans
- Security awareness training program

---

## 1. How PHI Flows Through the System

```
User uploads EOB document (contains PHI: patient name, DOB, member ID, diagnosis codes, etc.)
    │
    ▼
FastAPI backend receives file as plaintext
    │
    ▼
Chunker splits document by section (Patient Info, Service Lines, Diagnosis Codes, etc.)
    │
    ▼
Each chunk sent to AWS Bedrock (Titan Embed) to generate vector embeddings
    │  ← PHI leaves our system boundary here
    ▼
Embeddings + chunk metadata (including raw text, patient name) stored in Pinecone
    │  ← PHI stored in third-party system here
    ▼
User submits a query
    │
    ▼
Query embedding generated via Bedrock, similarity search runs against Pinecone
    │
    ▼
Top-k chunks (containing PHI) sent to AWS Bedrock (Claude) for answer generation
    │  ← PHI leaves our system boundary again
    ▼
LLM response returned to user through the API
```

**Where PHI exists at each layer:**

| Location | PHI Present | Details |
|----------|-------------|---------|
| Uploaded document | Yes | Full EOB text: names, DOB, member IDs, diagnosis codes, dollar amounts |
| In-memory document store | Yes | Raw text held in Python dict (no persistence, lost on restart) |
| Bedrock API requests | Yes | Chunk text sent for embedding and generation |
| Pinecone vector store | Yes | Chunk text stored in metadata fields (`text`, `patient_name`) |
| Bedrock API responses | Yes | Generated answers may reference PHI from source documents |
| API responses to frontend | Yes | Answer text and source chunks displayed to user |
| Application logs | Partial | Request metadata logged; question text logged; PHI content not directly logged but input hashes recorded |

---

## 2. HIPAA Technical Safeguards

### 2a. Access Controls (45 CFR § 164.312(a))

HIPAA requires four access control mechanisms:

**Unique User Identification (Required)**
- Every user must have a unique identifier — no shared accounts.
- **Current:** Each user has a unique `username` and JWT tokens contain `sub` (username), `jti` (unique token ID), and `role`. API keys identify services by name.
- **Production:** Integrate with enterprise IdP (Okta, Azure AD) where unique user IDs are centrally managed. Map IdP user IDs to application roles. Prohibit shared/generic accounts in policy and enforce programmatically.

**Automatic Logoff (Addressable)**
- Sessions must terminate after a period of inactivity to prevent unauthorized access from unattended workstations.
- **Current:** JWT tokens expire after 60 minutes (`JWT_EXPIRY_MINUTES`). No refresh tokens — user must re-authenticate after expiry.
- **Production:** Reduce token expiry to 15 minutes for PHI-access sessions. Implement refresh token rotation (single-use refresh tokens). Add frontend idle detection — prompt re-authentication after 10 minutes of inactivity. Invalidate tokens server-side on logout (requires a token blocklist or short-lived tokens with session store).

**Emergency Access Procedure (Required)**
- A process must exist to access PHI during an emergency when normal access controls fail.
- **Current:** Not implemented.
- **Production:** Create a "break-glass" admin account stored in a sealed envelope or hardware security module. Access requires two-person authorization (dual control). All break-glass access must trigger an immediate alert to the security team and be logged with enhanced detail. Break-glass credentials must be rotated after every use.

**Encryption and Decryption (Addressable)**
- See Section 3 below for full encryption details.

### 2b. Integrity Controls (45 CFR § 164.312(c))

HIPAA requires mechanisms to ensure PHI is not improperly altered or destroyed.

**Current implementation gaps:**
- In-memory document store has no change tracking — PHI can be overwritten or deleted with no record of the original state
- No checksums or hashes on stored PHI to detect tampering
- Pinecone metadata can be overwritten via upsert with no versioning

**Production requirements:**
- **Document versioning:** Every upload creates an immutable version. Deletions are soft-deletes (mark as deleted, retain for audit). No in-place updates.
- **Integrity verification:** Store SHA-256 hash of each document and chunk at ingestion time. Periodically verify hashes to detect corruption or tampering.
- **Database constraints:** Use append-only tables for PHI records. UPDATE and DELETE operations on PHI tables should be restricted to admin roles and logged.
- **Vector store integrity:** Record chunk hashes at upsert time. Validate on retrieval that stored text matches expected hash.
- **Backup verification:** Regular integrity checks on backups to ensure PHI can be restored accurately.

---

## 3. Production Healthcare Deployment Changes

### Authentication and Identity
- **Current:** In-memory user store with hardcoded accounts, SHA-256 password hashing
- **Production:** Integrate with enterprise identity provider (Okta, Azure AD, AWS Cognito). Use bcrypt or Argon2 for any local password hashing. Implement token refresh/rotation. Add MFA requirement for PHI access.

### Data Persistence
- **Current:** In-memory Python dict, lost on container restart
- **Production:** PostgreSQL with Transparent Data Encryption (TDE) on encrypted EBS volumes. All PHI columns encrypted at the application layer before storage.

### Secrets Management
- **Current:** JWT secret and API keys in environment variables
- **Production:** AWS Secrets Manager or HashiCorp Vault. Rotate secrets on schedule. No secrets in environment variables, Docker images, or source control.

### Network Security
- **Current:** HTTP between containers in Docker Compose, CORS-restricted origins
- **Production:** TLS termination at load balancer (ALB with ACM certificates). Internal service mesh with mTLS. VPC with private subnets for backend services. WAF for public-facing endpoints.

### Rate Limiting and Abuse Prevention
- **Current:** None
- **Production:** Rate limiting per user/role. Request size limits. Input validation and sanitization to prevent prompt injection.

### Logging and Monitoring
- **Current:** Structured JSON logs to stdout with correlation IDs
- **Production:** Ship logs to SIEM (Splunk, CloudWatch Logs with KMS encryption). Separate audit log stream with immutable storage. Alert on anomalous access patterns.

---

## 4. Data Encryption

### At Rest
| Component | Current State | Production Requirement |
|-----------|--------------|----------------------|
| Document store | In-memory (no disk) | Encrypted database (PostgreSQL with TDE, encrypted EBS) |
| Pinecone | Pinecone encrypts data at rest by default (AES-256) | Verify encryption is enabled; consider customer-managed keys if available |
| Application logs | Written to stdout (container ephemeral storage) | Encrypted log storage (CloudWatch with KMS, S3 with SSE-KMS) |
| Backups | None | Encrypted backups with separate key management |

### In Transit
| Connection | Current State | Production Requirement |
|------------|--------------|----------------------|
| User → Frontend | HTTP (localhost) | HTTPS with TLS 1.2+ (ACM certificate on ALB) |
| Frontend → Backend | HTTP via nginx proxy | HTTPS or internal mTLS |
| Backend → Bedrock | HTTPS (boto3 default) | HTTPS — already compliant |
| Backend → Pinecone | HTTPS (Pinecone client default) | HTTPS — already compliant |

---

## 5. Audit Logging Requirements

HIPAA requires covered entities and business associates to track access to PHI. An audit trail must record:

### Required Audit Events
- **Authentication:** All login attempts (success and failure), token issuance, logouts
- **PHI Access:** Every query that retrieves or displays PHI — who accessed it, when, what was accessed
- **PHI Modification:** Document uploads, deletions, any changes to stored PHI
- **Administrative Actions:** User role changes, system configuration changes, evaluation runs
- **Export/Download:** Any action that moves PHI outside the system boundary

### Required Audit Fields
Each audit log entry should contain:
- Timestamp (UTC, ISO 8601)
- User identity (username, role)
- Action performed
- Resource accessed (document ID, not PHI content)
- Correlation ID (to trace across services)
- Source IP address
- Success/failure status
- PHI access flag (boolean — was PHI viewed or transmitted)

### Retention and Integrity
- **Retention period:** Minimum 6 years per HIPAA (45 CFR § 164.530(j))
- **Immutability:** Logs must be write-once. Use S3 with Object Lock or equivalent to prevent tampering.
- **Access controls:** Audit logs themselves must be access-controlled. Only compliance/security roles should read them.

### Current Implementation
The application logs structured JSON with correlation IDs, request metadata, and LLM invocation details. The `input_hash` field allows tracking prompt usage without storing PHI in logs. Production would need to add explicit audit events for all PHI access and ship to immutable, encrypted storage.

---

## 6. BAA Implications for LLM API Providers

A Business Associate Agreement (BAA) is required with any third party that creates, receives, maintains, or transmits PHI on behalf of a covered entity.

### AWS Bedrock
- **BAA available:** Yes. AWS offers a BAA that covers Bedrock as an eligible HIPAA service.
- **Action required:** The AWS BAA must be explicitly signed through AWS Artifact before processing PHI. It is not automatic.
- **Coverage:** Covers both the embedding model (Titan Embed) and the generation model (Claude via Bedrock). The BAA covers AWS infrastructure — data in transit and at rest within AWS.
- **Important:** Anthropic's Claude models accessed through Bedrock are covered under the AWS BAA. This is different from using Anthropic's API directly.

### Pinecone
- **BAA available:** Must be verified with Pinecone's sales/compliance team. As of this writing, Pinecone's standard terms may not include BAA coverage.
- **Risk:** PHI (patient names, chunk text) is stored in Pinecone metadata. Without a BAA, this is a HIPAA violation.
- **Alternatives if no BAA:**
  - Amazon OpenSearch Serverless (covered under AWS BAA)
  - PostgreSQL with pgvector on Amazon RDS (covered under AWS BAA)
  - Self-hosted vector store on encrypted infrastructure

### Anthropic Direct API
- **Not used in this application** (we use Claude through Bedrock)
- If used directly: Anthropic offers a BAA for enterprise customers. Must be negotiated separately.
- Bedrock route is simpler for HIPAA compliance since it falls under the existing AWS BAA.

### Summary of BAA Status

| Provider | PHI Transmitted | BAA Available | BAA Signed | Action Needed |
|----------|----------------|---------------|------------|---------------|
| AWS Bedrock | Yes (embeddings + generation) | Yes | Must verify | Sign BAA via AWS Artifact |
| Pinecone | Yes (chunk text in metadata) | Verify | No | Contact Pinecone or migrate to BAA-covered alternative |
| Anthropic (via Bedrock) | Yes (indirect) | Covered by AWS BAA | Via AWS | No additional action if AWS BAA is signed |

---

## Summary of Gaps (Current → Production)

| Area | Current | Gap | Priority |
|------|---------|-----|----------|
| Unique user IDs | JWT with username + jti | Need enterprise IdP with centralized unique IDs | High |
| Automatic logoff | 60-min token expiry | Need 15-min expiry, idle detection, refresh rotation | High |
| Emergency access | Not implemented | Need break-glass procedure with dual control + alerts | High |
| PHI integrity | No change tracking or checksums | Need versioning, soft-deletes, hash verification | High |
| User auth | In-memory, hardcoded | Need enterprise IdP, MFA | High |
| Data at rest | In-memory, no encryption | Need encrypted persistent storage | High |
| BAA coverage | None signed | AWS BAA required, Pinecone BAA TBD | High |
| Audit logging | Basic structured logs | Need immutable, PHI-aware audit trail | High |
| TLS | HTTP in dev | Need HTTPS everywhere | High |
| Secrets | Env vars | Need secrets manager | Medium |
| Rate limiting | None | Need per-user rate limits | Medium |
| Log retention | Ephemeral | Need 6-year encrypted retention | Medium |
