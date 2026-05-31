# Step 2: Technical Control Baseline — Methodology

## Research Context

This module addresses a fundamental challenge in automated compliance: 
**How do we represent the "As-Is" state of enterprise infrastructure 
in a format that can be automatically compared against regulatory requirements?**

## Design Decisions

### 1. OSCAL Component-Definition as Output Format
**Why OSCAL?**
- NIST standard with global recognition
- Tool-agnostic (works with any GRC platform)
- Aligns with Step 1's OSCAL Catalog output
- Enables "Policy-as-Code" approaches

**Trade-offs:**
- More verbose than custom JSON
- Requires understanding of OSCAL schema
- Limited tooling ecosystem (but growing)

### 2. Strategy Pattern for Multi-Cloud Support
**Why Strategy Pattern?**
- Clean separation of cloud-specific logic
- Easy to add new providers (GCP, OCI)
- Consistent interface for downstream analysis

**Trade-offs:**
- More boilerplate code
- Requires careful abstraction design

### 3. Pydantic for Data Validation
**Why Pydantic?**
- Type safety at runtime
- Automatic JSON serialization
- Clear error messages for malformed data
- Industry standard for Python data validation

## Socio-Technical Friction Points

During implementation, we identified several friction points:

1. **Authentication Complexity**: Different cloud providers have different 
   authentication models. Azure's DefaultAzureCredential tries 5+ methods, 
   which can be confusing for users.

2. **Permission Requirements**: Collecting comprehensive baselines requires 
   broad read permissions, which may conflict with least-privilege principles.

3. **Regional Variations**: Some controls behave differently in different 
   Azure regions, requiring region-aware logic.

4. **API Rate Limits**: Large enterprises may hit Azure API rate limits, 
   requiring throttling and retry logic.

## Limitations & Future Work

- **AWS Support**: Not yet implemented (planned for Step 2.5)
- **GCP Support**: Planned for future release
- **Real-time Monitoring**: Current implementation is point-in-time; 
  future versions will support continuous monitoring
- **Custom Control Categories**: Users cannot yet define custom categories

## Testing Strategy

- **Mocked Cloud Responses**: All tests use mock data to avoid 
  requiring real cloud credentials
- **Schema Validation**: Output is validated against OSCAL schema
- **Edge Cases**: Tested with empty environments, permission errors, 
  and malformed responses
