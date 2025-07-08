import { Request, Response, NextFunction } from 'express';

interface AppError extends Error {
  statusCode?: number;
  status?: string;
  isOperational?: boolean;
}

export const errorHandler = (
  err: AppError,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  let error = { ...err };
  error.message = err.message;

  // Log error
  console.error(err);

  // Default error values
  let statusCode = 500;
  let message = 'Internal Server Error';

  // Custom error handling
  if (err.statusCode) {
    statusCode = err.statusCode;
    message = err.message;
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    statusCode = 400;
    message = 'Validation Error';
  }

  // Mongoose cast error
  if (err.name === 'CastError') {
    statusCode = 400;
    message = 'Resource not found';
  }

  // Duplicate key error
  if ((err as any).code === 11000) {
    statusCode = 400;
    message = 'Duplicate field value entered';
  }

  res.status(statusCode).json({
    success: false,
    error: {
      message,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    }
  });
}; 