# file-storage Specification

## Purpose
Stores and reads uploaded files (trade agreements first) in an S3-compatible bucket, RustFS locally, behind one async interface shared by web-api and ai-api.

## Requirements
### Requirement: Uploaded files SHALL be stored in an S3-compatible bucket behind one interface

The system SHALL store uploaded file bytes through a `FileStore` that can put, get and delete an object by key. The configured implementation SHALL talk to an S3-compatible service using `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY` and `S3_SECRET_KEY`, with path-style addressing. Web-api and ai-api SHALL use the same implementation.

Local development SHALL run RustFS through docker compose. Object keys SHALL begin with the owning company's id, so one company's files never share a prefix with another's.

#### Scenario: A file round-trips

- **WHEN** a file is put under a key and read back
- **THEN** the bytes read are the bytes put

#### Scenario: Keys are per company

- **WHEN** an agreement is uploaded for a company
- **THEN** its object key starts with `companies/<company id>/agreements/`

### Requirement: The bucket SHALL exist before files are stored

At startup, web-api SHALL create the configured bucket if it doesn't exist. When storage isn't configured or can't be reached, it SHALL log that and keep running, and uploads SHALL fail with `503 Service Unavailable` saying storage is unavailable.

#### Scenario: First start

- **WHEN** web-api starts against an empty RustFS
- **THEN** the bucket exists afterwards

#### Scenario: Storage down

- **WHEN** an agreement is uploaded while the store can't be reached
- **THEN** the response is 503, and no agreement or file row is left behind

### Requirement: Stored files SHALL only reach the browser through an authorised endpoint

The browser SHALL NOT be given bucket URLs or credentials. A stored file SHALL be served by an API endpoint that first checks that the caller may see the owning company.

#### Scenario: Another organization's file

- **WHEN** a user asks for the document of an agreement belonging to a company outside their organization
- **THEN** the response is 404 and no bytes are sent
