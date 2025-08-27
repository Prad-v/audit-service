# High-Transaction Audit Log Framework

A scalable audit log framework designed to handle 1M+ transactions per day, built with FastAPI, PostgreSQL, Redis, and NATS for local development, with cloud migration path to Google Cloud Platform.

## Features

- **High Performance**: Handle 1M+ audit events per day
- **Multi-tenant**: Secure tenant isolation
- **Real-time Processing**: NATS-based message streaming
- **Rich Querying**: Advanced filtering and search capabilities
- **Export Support**: CSV and JSON export functionality
- **Cloud Ready**: Migration path to GCP BigQuery and Pub/Sub
- **Developer Portal**: Backstage.io integration
- **Client SDKs**: Python and Go SDKs with async support

## Architecture

- **Backend**: FastAPI with async/await support
- **Database**: PostgreSQL (local) → BigQuery (production)
- **Cache**: Redis for query optimization
- **Message Queue**: NATS (local) → Pub/Sub (production)
- **Frontend**: Backstage.io with custom audit log plugin
- **Deployment**: Docker Compose (local) → Kubernetes (production)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- Make (optional, for convenience commands)

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd audit-service
```

2. Start local services:
```bash
make dev-up
# or
docker-compose up -d
```

3. Run database migrations:
```bash
make migrate
```

4. Start the API server:
```bash
make dev-api
```

5. Start the frontend (in another terminal):
```bash
make dev-frontend
```

6. Access the services:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- NATS Monitoring: http://localhost:8222

## Development Commands

```bash
# Start all services
make dev-up

# Stop all services
make dev-down

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Build all containers
make build

# View logs
make logs
```

## Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed project organization.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system architecture and design decisions.

## API Documentation

Once the server is running, visit http://localhost:8000/docs for interactive API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.