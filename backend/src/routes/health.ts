import { Router, Request, Response } from 'express';

const router = Router();

// Basic health check endpoint
router.get('/', (req: Request, res: Response) => {
  const healthcheck = {
    uptime: process.uptime(),
    message: 'OK',
    timestamp: Date.now(),
    env: process.env.NODE_ENV || 'development',
    version: process.env.npm_package_version || '1.0.0',
    memory: {
      used: process.memoryUsage().heapUsed / 1024 / 1024,
      total: process.memoryUsage().heapTotal / 1024 / 1024
    }
  };

  res.status(200).json(healthcheck);
});

// Detailed health check
router.get('/detailed', (req: Request, res: Response) => {
  const healthcheck = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    version: '1.0.0',
    system: {
      platform: process.platform,
      arch: process.arch,
      nodeVersion: process.version,
      pid: process.pid
    },
    memory: {
      used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024 * 100) / 100,
      total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024 * 100) / 100,
      rss: Math.round(process.memoryUsage().rss / 1024 / 1024 * 100) / 100,
      external: Math.round(process.memoryUsage().external / 1024 / 1024 * 100) / 100
    },
    cpu: {
      usage: process.cpuUsage()
    }
  };

  res.status(200).json(healthcheck);
});

export { router as healthRouter }; 