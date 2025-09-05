# Incident Manager - Frontend

A modern React application for managing and viewing audit logs, built with Vite, TypeScript, and Tailwind CSS.

## Features

- **Dashboard**: Overview of audit events with statistics and quick actions
- **Audit Logs**: Browse and filter audit events with pagination
- **Create Events**: Manually create new audit events
- **Event Details**: View detailed information about specific events
- **Real-time Updates**: React Query for efficient data fetching and caching
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Client-side routing
- **React Query** - Data fetching and caching
- **Axios** - HTTP client
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm run test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage

## Project Structure

```
src/
├── components/     # Reusable UI components
├── lib/           # Utilities and API client
├── pages/         # Page components
├── test/          # Test setup
├── App.tsx        # Main app component
├── main.tsx       # App entry point
└── index.css      # Global styles
```

## API Integration

The frontend communicates with the backend API through the `auditApi` client in `src/lib/api.ts`. The API endpoints include:

- `GET /api/v1/audit/events` - List audit events with filtering and pagination
- `GET /api/v1/audit/events/:id` - Get specific audit event details
- `POST /api/v1/audit/events` - Create a new audit event
- `POST /api/v1/audit/events/batch` - Create multiple audit events
- `GET /api/v1/audit/health` - Health check

## Development

### Adding New Pages

1. Create a new component in `src/pages/`
2. Add the route to `src/App.tsx`
3. Update the navigation in `src/components/Layout.tsx` if needed

### Styling

The project uses Tailwind CSS for styling. Custom components are defined in `src/index.css` using the `@layer components` directive.

### State Management

React Query is used for server state management, providing caching, background updates, and optimistic updates out of the box.

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready to be served by a web server.

## Docker

To build and run the frontend with Docker:

```bash
# Build the image
docker build -t audit-frontend .

# Run the container
docker run -p 3000:80 audit-frontend
```

## Testing

The project uses Vitest for unit testing and React Testing Library for component testing.

```bash
# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```
