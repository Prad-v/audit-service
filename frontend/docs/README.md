# Audit Service Documentation

Welcome to the comprehensive documentation for the Audit Service. This documentation will help you understand, set up, and integrate the audit logging system into your applications.

## 📚 Documentation Sections

### [API Reference](api/README.md)
Complete API documentation with examples, authentication methods, and error handling.

### [Quick Start Guide](guides/quick-start.md)
Get up and running with the Audit Service in minutes.

### [Examples](examples/)
Integration examples for various programming languages and frameworks.

### [Deployment](deployment/)
Production deployment guides and configuration options.

## 🚀 Quick Links

- **Live Demo**: [Frontend UI](http://localhost:3000)
- **API Documentation**: [Swagger UI](http://localhost:8000/docs)
- **Health Check**: [API Health](http://localhost:8000/health/)
- **Static Documentation**: [HTML Docs](http://localhost:3000/docs)

## 🏗️ Architecture Overview

The Audit Service is built with a modern, scalable architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Infrastructure │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Docker)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Database)    │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Redis         │
                       │   (Cache)       │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   NATS          │
                       │   (Messaging)   │
                       └─────────────────┘
```

## 🔧 Key Features

- **Secure Audit Logging**: Role-based access control and encryption
- **Real-time Events**: Instant event streaming and monitoring
- **Scalable Architecture**: Built for high-performance with PostgreSQL, Redis, and NATS
- **RESTful API**: Comprehensive REST API with OpenAPI documentation
- **Modern UI**: React-based frontend with real-time updates
- **Docker Support**: Complete containerization for easy deployment

## 📋 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/audit-service.git
   cd audit-service
   ```

2. **Start the services**:
   ```bash
   ./scripts/start.sh start
   ```

3. **Create your first audit event**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/audit/events \
     -H "Content-Type: application/json" \
     -d '{
       "event_type": "user_login",
       "action": "login",
       "status": "success",
       "tenant_id": "demo_tenant",
       "service_name": "demo_service",
       "user_id": "user_123"
     }'
   ```

4. **Explore the UI**: Visit [http://localhost:3000](http://localhost:3000)

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python3 run_tests.py

# Run specific test types
python3 run_tests.py --unit
python3 run_tests.py --integration
python3 run_tests.py --e2e

# Run with continue on fail
python3 run_tests.py --continue-on-fail
```

## 📖 Documentation Structure

```
docs/
├── README.md              # This file
├── index.html             # Static HTML documentation
├── api/                   # API documentation
│   └── README.md         # Complete API reference
├── guides/               # User guides
│   └── quick-start.md    # Quick start guide
├── examples/             # Integration examples
├── deployment/           # Deployment guides
└── assets/              # Documentation assets
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

- **Documentation**: [docs/](docs/) directory
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **GitHub Issues**: [Create an issue](https://github.com/your-org/audit-service/issues)
- **Community**: [Join our Discord](https://discord.gg/audit-service)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using FastAPI, React, and Docker**
