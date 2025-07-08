import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';
import { healthRouter } from './routes/health';
import { componentsRouter } from './routes/components';
import { errorHandler } from './middleware/errorHandler';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));

// Logging middleware
app.use(morgan('combined'));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// API routes
app.use('/api/health', healthRouter);
app.use('/api/components', componentsRouter);

// Root route
app.get('/', (req, res) => {
  res.json({
    message: 'Oasis OS Backend API',
    version: '1.0.0',
    status: 'running',
    description: 'Intelligent workspace management system API',
    endpoints: {
      health: '/api/health',
      agents: '/api/components',
      'agent-categories': '/api/components/meta/categories',
      'agent-stats': '/api/components/meta/stats'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method
  });
});

// Error handling middleware
app.use(errorHandler);

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
  console.log(`🎨 Components API: http://localhost:${PORT}/api/components`);
});

export default app; 