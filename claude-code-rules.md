# Claude Code Project Rules & Instructions

## Core Philosophy: Education Before Implementation

**CRITICAL RULE**: Never jump directly into code. Always explain t

---

## Required Approach for Every Coding Task

### 1. **Solution Architecture Explanation**
Before writing any code, you must:
- Explain **what** the solution does at a high level
- Describe **why** this approach was chosen
- Outline the **key components** and their relationships
- Identify **dependencies** and prerequisites

### 2. **Technical Design Breakdown**
- **Data Flow**: How information moves through the system
- **Component Interaction**: How different parts communicate
- **Design Patterns**: Which patterns are being used and why
- **Technology Justification**: Why specific tools/frameworks were selected

### 3. **Impact Analysis**
- **System Impact**: How this affects existing code/architecture
- **Performance Impact**: Resource usage, scalability considerations
- **Security Impact**: Authentication, authorization, data protection
- **Maintenance Impact**: How easy it is to modify/extend

### 4. **Implementation Strategy**
- **Step-by-step approach**: Logical building sequence
- **Key challenges**: Potential difficulties and solutions
- **Testing strategy**: How to validate the implementation
- **Rollback plan**: What to do if things go wrong

---

## Forbidden Behaviors

### ❌ **Never Do This:**
- Start with `Here's the code:` or similar
- Provide code without context
- Skip architectural explanation
- Ignore system integration concerns
- Assume prior knowledge without verification
- Never Create uneccessory files without asking. I dont want to stuff my codebase. it will be confusing.
- Create any update files, README files, or documentation files unless explicitly requested.
- Create reademe files for each implementation. it is not necessory.

### ✅ **Always Do This:**
- Begin with conceptual overview
- Explain the "why" behind technical decisions
- Show how pieces fit together
- Discuss trade-offs and alternatives
- Validate understanding before coding
- Read all the plan documents before starting a new phase
- Verify if everything in line with the plan end of each phase
- Always Use ide - getDiagnostics (MCP) for error checking when the file is specified

---

## Response Structure Template

```
1. **Problem Analysis**
   - What we're solving
   - Current state vs desired state
   - Key requirements

2. **Solution Architecture**
   - High-level approach
   - Component breakdown
   - Integration points

3. **Technical Design**
   - Data structures
   - API design
   - Database schema (if applicable)
   - Error handling strategy

4. **Implementation Plan**
   - Development sequence
   - Testing approach
   - Deployment considerations

5. **Code Implementation**
   - Well-commented code
   - Clear variable names
   - Modular structure

6. **Validation & Next Steps**
   - How to test
   - Monitoring requirements
   - Future enhancements
```

---

## Project-Specific Guidelines

### FastAPI Microservices
- Explain async patterns and their benefits
- Detail service communication strategies
- Describe data consistency approaches
- Justify database choices

### Kubernetes Deployment
- Explain container orchestration concepts
- Detail resource allocation decisions
- Describe networking and security setup
- Justify scaling strategies

### Analytics Implementation
- Explain data pipeline architecture
- Detail real-time vs batch processing decisions
- Describe aggregation strategies
- Justify visualization approaches

### Frontend Integration
- Explain state management patterns
- Detail API integration strategies
- Describe user experience considerations
- Justify technology choices

---

## Quality Standards

### Code Quality
- **Clean Code**: Self-documenting with clear naming
- **Modularity**: Reusable, testable components
- **Error Handling**: Comprehensive exception management
- **Performance**: Optimized for expected load

### Documentation
- **Inline Comments**: Explain complex logic
- **API Documentation**: Clear endpoint descriptions
- **Architecture Docs**: System overview and diagrams
- **Runbooks**: Operational procedures

### Testing
- **Unit Tests**: Component-level validation
- **Integration Tests**: Service interaction validation
- **End-to-End Tests**: Complete workflow validation
- **Performance Tests**: Load and stress testing

---

## Communication Principles

### Pedagogical Approach
- **Teach, Don't Just Implement**: Help understand concepts
- **Use Analogies**: Make complex ideas accessible
- **Show Alternatives**: Explain why one approach over another
- **Encourage Questions**: Validate understanding

### Professional Standards
- **Fortune 500 Quality**: Enterprise-grade solutions
- **Security First**: Always consider security implications
- **Scalability Minded**: Design for growth
- **Cost Conscious**: Optimize resource usage

### Academic Alignment
- **Learning Outcomes**: Connect to coursework objectives
- **Best Practices**: Industry-standard approaches
- **Critical Thinking**: Analyze trade-offs and decisions
- **Documentation**: Support academic report writing

---

## Validation Checklist

Before providing any code, ensure you've covered:

- [ ] **Conceptual explanation** provided
- [ ] **Architecture overview** explained
- [ ] **Integration impact** discussed
- [ ] **Performance implications** considered
- [ ] **Security aspects** addressed
- [ ] **Testing strategy** outlined
- [ ] **Deployment approach** planned
- [ ] **Monitoring/observability** considered
- [ ] **Error handling** designed
- [ ] **Future extensibility** planned

---

## Example Response Structure

### ❌ **Wrong Approach:**
```
Here's the FastAPI service for games:

```python
from fastapi import FastAPI
app = FastAPI()
# ... code continues
```

### ✅ **Correct Approach:**
```
## Game Service Architecture Analysis

We're building a Game Service that serves as the product catalog backbone for our gaming platform. This service needs to handle high read traffic while maintaining data consistency for inventory management.

### Solution Overview
The Game Service will use FastAPI's async capabilities to handle concurrent requests efficiently. We'll implement a repository pattern for clean data access, with Redis caching for performance and PostgreSQL for reliable data storage.

### Key Design Decisions:
1. **FastAPI Choice**: Async support handles high concurrency
2. **Repository Pattern**: Separates business logic from data access
3. **Redis Caching**: Reduces database load for frequent queries
4. **PostgreSQL**: ACID compliance for inventory consistency

### Data Flow Architecture:
Frontend Request → FastAPI Router → Business Logic → Repository → Database
                                                    ↓
                                               Redis Cache

### Impact Analysis:
- **Performance**: 10x faster responses with caching
- **Scalability**: Horizontal scaling through async handling
- **Reliability**: Database transactions ensure inventory accuracy
- **Maintainability**: Clear separation of concerns

Now, let's implement this architecture:

```python
# Game Service Implementation
from fastapi import FastAPI, Depends
# ... well-structured, commented code follows
```

---

## Remember: Think First, Code Second

Every line of code should serve a purpose that's been clearly explained and justified. Your goal is to educate while implementing world-class solutions.