# Architecture

## Overview

BNX Link follows a layered architecture that separates storage, organization, and access patterns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raw Objects   │    │   References    │    │   Manifests     │
│                 │    │                 │    │                 │
│ • JSON files    │    │ • Human IDs     │    │ • Object sets   │
│ • SHA-256 hash  │    │ • Date stamps   │    │ • Integrity     │
│ • Immutable     │    │ • Hash pointers │    │ • Snapshots     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │    Channels     │
                    │                 │
                    │ • Environment   │
                    │ • Promotion     │
                    │ • Current state │
                    └─────────────────┘
```

## Data Flow

### 1. Object Creation
- JSON files are canonicalized (sorted keys, normalized whitespace)
- SHA-256 hash is computed
- File is stored under `data/objects/<hash-prefix>/<full-hash>.json`

### 2. Reference Creation
- Human-readable references are created in `data/refs/`
- Each ref maps a logical ID + date to an object hash
- Example: `data/refs/entity/project_apollo/2025-08-10.json`

### 3. Manifest Building
- Manifests group related objects together
- Each manifest has its own integrity hash
- Stored in `data/manifests/<dataset>/<id>.json`

### 4. Channel Promotion
- Channels point to specific manifests
- Environment progression: `dev` → `staging` → `prod`
- Current state tracked in `data/channels.yaml`

## Storage Layout

```
data/
├── objects/           # Content-addressed storage
│   ├── 1d/
│   │   └── 1dc3d0e4809ec1c49d3ad5c524dadabbb5f80f9d7eb1053e3b5a0c71687f11a6.json
│   └── aa/
│       └── aa657141baa2fa60294414623cba73b7df3968ba51f1067547cb4ff63406f09f.json
├── refs/              # Human-readable pointers
│   ├── entity/
│   │   └── project_apollo/
│   │       └── 2025-08-10.json
│   └── activity/
│       └── task_generate_readme/
│           └── 2025-08-10.json
├── manifests/         # Object set snapshots
│   └── core/
│       └── dev-seed.json
├── channels.yaml      # Current channel state
└── ledger.ndjson      # Audit trail
```

## API & Agent Interaction

### API Layer
- **FastAPI** with JWT authentication
- **Scope-based access control** for different operations
- **View transformations** (raw, redacted, LLM-optimized)
- **Rate limiting** and audit logging

### Agent CLI
- **Interactive console** for dataset exploration
- **Pipe-based processing** (summarizer, redactor, validator)
- **Context-aware** object loading and display
- **Direct API integration** for real-time data

### DuckDB Projection
- **SQL queries** against structured object views
- **Automatic schema inference** from JSON
- **Performance optimization** for analytical workloads
- **Real-time updates** as objects change

## Security Model

### Authentication
- JWT tokens with configurable algorithms
- Development: HS256 (shared secret)
- Production: RS256 (asymmetric keys)

### Authorization
- **Scopes**: Fine-grained permission control
- **Purpose-based access**: Different views for different use cases
- **Audit logging**: Complete trail of all operations

### Data Protection
- **Redaction profiles**: Configurable data masking
- **Access controls**: Environment-based restrictions
- **Integrity verification**: Hash-based tamper detection

## Performance Considerations

### Storage
- **Content addressing**: Deduplication and integrity
- **Lazy loading**: Objects fetched on-demand
- **Caching**: Manifest and reference caching

### API
- **Async processing**: Non-blocking I/O operations
- **Connection pooling**: Efficient database connections
- **Response compression**: Reduced bandwidth usage

### Agent
- **Streaming**: Large object processing
- **Memory management**: Efficient object loading
- **Background processing**: Non-blocking operations

## Extensibility

### Custom Object Types
- **JSON Schema validation**: Type safety and documentation
- **Plugin architecture**: Custom processors and views
- **Domain-specific extensions**: Business logic integration

### Integration Points
- **Webhook support**: External system notifications
- **Event streaming**: Real-time data updates
- **Export formats**: Multiple output formats
- **API clients**: Language-specific libraries

## Monitoring & Observability

### Metrics
- **Request rates**: API usage patterns
- **Response times**: Performance monitoring
- **Error rates**: Reliability tracking
- **Storage usage**: Capacity planning

### Logging
- **Structured logging**: Machine-readable logs
- **Audit trail**: Complete operation history
- **Debug information**: Development assistance
- **Security events**: Access and authorization logs

