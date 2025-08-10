# Data Model

## Overview

BNX Link uses a flexible, schema-driven data model that separates concerns into three layers:

```
┌─────────────────────────────────────────────────────────────┐
│                        Object                              │
├─────────────────────────────────────────────────────────────┤
│  Envelope: Metadata, integrity, and system information    │
├─────────────────────────────────────────────────────────────┤
│  Context: Domain-specific metadata and relationships       │
├─────────────────────────────────────────────────────────────┤
│  Body: Core business data and content                      │
└─────────────────────────────────────────────────────────────┘
```

## Object Structure

### Envelope
The envelope contains system-level metadata and integrity information:

```json
{
  "envelope": {
    "version": "1.0",
    "created_at": "2025-08-10T10:00:00Z",
    "created_by": "system",
    "integrity": {
      "algorithm": "sha256",
      "hash": "1dc3d0e4809ec1c49d3ad5c524dadabbb5f80f9d7eb1053e3b5a0c71687f11a6"
    },
    "schema": {
      "type": "EntityRecord",
      "version": "1.0",
      "uri": "schemas/EntityRecord.v1.json"
    }
  }
}
```

### Context
The context layer contains domain-specific metadata and relationships:

```json
{
  "context": {
    "type": "project",
    "category": "space_exploration",
    "tags": ["nasa", "moon", "1960s"],
    "relationships": {
      "parent": null,
      "children": ["mission_apollo_11", "mission_apollo_12"],
      "related": ["kennedy_space_center", "saturn_v"]
    },
    "metadata": {
      "priority": "high",
      "status": "completed",
      "start_date": "1961-05-25",
      "end_date": "1972-12-19"
    }
  }
}
```

### Body
The body contains the core business data:

```json
{
  "body": {
    "name": "Project Apollo",
    "description": "Human spaceflight program that landed the first humans on the Moon",
    "objectives": [
      "Land humans on the Moon",
      "Return them safely to Earth",
      "Establish American leadership in space"
    ],
    "achievements": [
      "6 successful lunar landings",
      "12 astronauts walked on the Moon",
      "Advanced space technology development"
    ]
  }
}
```

## Record Types

### EntityRecord
Entities represent persistent objects in your domain:

**Schema**: [`schemas/EntityRecord.v1.json`](../schemas/EntityRecord.v1.json)

**Purpose**: Store information about people, places, things, concepts, or organizations.

**Example**:
```json
{
  "envelope": {
    "version": "1.0",
    "created_at": "2025-08-10T10:00:00Z",
    "created_by": "system",
    "integrity": {
      "algorithm": "sha256",
      "hash": "1dc3d0e4809ec1c49d3ad5c524dadabbb5f80f9d7eb1053e3b5a0c71687f11a6"
    },
    "schema": {
      "type": "EntityRecord",
      "version": "1.0",
      "uri": "schemas/EntityRecord.v1.json"
    }
  },
  "context": {
    "type": "project",
    "category": "space_exploration",
    "tags": ["nasa", "moon", "1960s"],
    "relationships": {
      "parent": null,
      "children": ["mission_apollo_11", "mission_apollo_12"],
      "related": ["kennedy_space_center", "saturn_v"]
    },
    "metadata": {
      "priority": "high",
      "status": "completed",
      "start_date": "1961-05-25",
      "end_date": "1972-12-19"
    }
  },
  "body": {
    "name": "Project Apollo",
    "description": "Human spaceflight program that landed the first humans on the Moon",
    "objectives": [
      "Land humans on the Moon",
      "Return them safely to Earth",
      "Establish American leadership in space"
    ],
    "achievements": [
      "6 successful lunar landings",
      "12 astronauts walked on the Moon",
      "Advanced space technology development"
    ]
  }
}
```

### ActivityRecord
Activities represent events, actions, or processes:

**Schema**: [`schemas/ActivityRecord.v1.json`](../schemas/ActivityRecord.v1.json)

**Purpose**: Track what happened, when, by whom, and with what resources.

**Example**:
```json
{
  "envelope": {
    "version": "1.0",
    "created_at": "2025-08-10T10:00:00Z",
    "created_by": "system",
    "integrity": {
      "algorithm": "sha256",
      "hash": "aa657141baa2fa60294414623cba73b7df3968ba51f1067547cb4ff63406f09f"
    },
    "schema": {
      "type": "ActivityRecord",
      "version": "1.0",
      "uri": "schemas/ActivityRecord.v1.json"
    }
  },
  "context": {
    "type": "task",
    "category": "documentation",
    "tags": ["readme", "documentation", "setup"],
    "relationships": {
      "parent": "project_setup",
      "children": [],
      "related": ["project_apollo", "documentation_standards"]
    },
    "metadata": {
      "priority": "medium",
      "status": "completed",
      "start_date": "2025-08-10T09:00:00Z",
      "end_date": "2025-08-10T10:00:00Z"
    }
  },
  "body": {
    "name": "Generate README",
    "description": "Create comprehensive documentation for the BNX Link project",
    "action": "documentation_generation",
    "actor": "developer",
    "resources": ["markdown_templates", "project_structure", "api_docs"],
    "outputs": ["README.md", "docs/", "examples/"],
    "metrics": {
      "time_spent": "1h",
      "files_created": 5,
      "lines_written": 150
    }
  }
}
```

## Schema Validation

### JSON Schema
All objects must conform to their respective JSON Schema:

- **EntityRecord**: [`schemas/EntityRecord.v1.json`](../schemas/EntityRecord.v1.json)
- **ActivityRecord**: [`schemas/ActivityRecord.v1.json`](../schemas/ActivityRecord.v1.json)

### Validation Rules
- **Required fields**: All envelope fields are mandatory
- **Type checking**: Strict type validation for all fields
- **Format validation**: Date/time, URI, and hash format validation
- **Custom constraints**: Business rule validation

### Extensibility
- **Additional fields**: Custom metadata in context and body
- **Schema evolution**: Versioned schemas for backward compatibility
- **Domain extensions**: Specialized record types for specific use cases

## Data Relationships

### Reference Integrity
- **Hash-based references**: All object references use SHA-256 hashes
- **Cross-validation**: References are validated against actual objects
- **Circular reference detection**: Prevents infinite loops

### Temporal Relationships
- **Created timestamps**: When the object was first created
- **Modified tracking**: Change history and versioning
- **Expiration**: Optional TTL for temporary data

### Hierarchical Organization
- **Parent-child relationships**: Tree structures for complex data
- **Tag-based grouping**: Flexible categorization and search
- **Namespace isolation**: Dataset separation and access control

## Data Quality

### Integrity Checks
- **Hash verification**: SHA-256 integrity validation
- **Schema compliance**: JSON Schema validation
- **Reference validation**: Cross-reference integrity
- **Data consistency**: Business rule enforcement

### Quality Metrics
- **Completeness**: Required field coverage
- **Accuracy**: Data validation and verification
- **Timeliness**: Freshness of information
- **Consistency**: Cross-object validation

### Data Governance
- **Access controls**: Role-based permissions
- **Audit logging**: Complete operation history
- **Data lineage**: Source and transformation tracking
- **Retention policies**: Data lifecycle management

## Storage Optimization

### Content Addressing
- **Deduplication**: Identical content shares the same hash
- **Compression**: Efficient storage of repeated patterns
- **Indexing**: Fast lookup by hash and metadata

### Performance
- **Lazy loading**: Objects fetched on-demand
- **Caching**: Frequently accessed data in memory
- **Batch operations**: Efficient bulk processing
- **Streaming**: Large object handling

### Scalability
- **Horizontal scaling**: Distributed storage support
- **Sharding**: Hash-based data distribution
- **Replication**: High availability and disaster recovery
- **Backup strategies**: Data protection and recovery
