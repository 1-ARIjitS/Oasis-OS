import { Router, Request, Response } from 'express';

const router = Router();

// Mock data for Oasis OS agents
const components = [
  {
    id: 'workspace-agent',
    name: 'Workspace Agent',
    description: 'Sets up folders, auto-generates docs, organizes files',
    category: 'automation',
    difficulty: 'advanced',
    dependencies: ['fs', 'path'],
    tags: ['workspace', 'automation', 'organization', 'productivity']
  },
  {
    id: 'file-agent',
    name: 'File Agent',
    description: 'Finds files, renames, sorts by context',
    category: 'file-management',
    difficulty: 'medium',
    dependencies: ['fs', 'glob'],
    tags: ['files', 'search', 'organization', 'context']
  },
  {
    id: 'note-agent',
    name: 'Note Agent',
    description: 'Creates daily notes, pulls content from meetings',
    category: 'documentation',
    difficulty: 'medium',
    dependencies: ['markdown', 'date-fns'],
    tags: ['notes', 'meetings', 'documentation', 'daily']
  },
  {
    id: 'focus-agent',
    name: 'Focus Agent',
    description: 'Minimizes notifications, sets focus timers',
    category: 'productivity',
    difficulty: 'easy',
    dependencies: ['notification-api'],
    tags: ['focus', 'productivity', 'timer', 'notifications']
  },
  {
    id: 'project-tracker',
    name: 'Project Tracker',
    description: 'Tracks project status, deadlines, and progress',
    category: 'project-management',
    difficulty: 'medium',
    dependencies: ['database'],
    tags: ['projects', 'tracking', 'deadlines', 'status']
  },
  {
    id: 'time-tracker',
    name: 'Time Tracker',
    description: 'Automatically tracks time spent on projects',
    category: 'productivity',
    difficulty: 'medium',
    dependencies: ['timer', 'analytics'],
    tags: ['time', 'tracking', 'productivity', 'analytics']
  },
  {
    id: 'email-agent',
    name: 'Email Agent',
    description: 'Manages email drafts and follow-ups',
    category: 'communication',
    difficulty: 'advanced',
    dependencies: ['email-api'],
    tags: ['email', 'communication', 'drafts', 'follow-up']
  },
  {
    id: 'backup-agent',
    name: 'Backup Agent',
    description: 'Automatically backs up important files',
    category: 'security',
    difficulty: 'medium',
    dependencies: ['fs', 'cloud-storage'],
    tags: ['backup', 'security', 'files', 'automation']
  },
  {
    id: 'template-agent',
    name: 'Template Agent',
    description: 'Generates project templates and boilerplate',
    category: 'automation',
    difficulty: 'easy',
    dependencies: ['fs', 'handlebars'],
    tags: ['templates', 'boilerplate', 'automation', 'projects']
  },
  {
    id: 'analytics-agent',
    name: 'Analytics Agent',
    description: 'Provides insights on productivity and workflow',
    category: 'analytics',
    difficulty: 'advanced',
    dependencies: ['analytics', 'charts'],
    tags: ['analytics', 'insights', 'productivity', 'data']
  }
];

// Get all components
router.get('/', (req: Request, res: Response) => {
  const { category, difficulty, search } = req.query;
  
  let filteredComponents = components;
  
  // Filter by category
  if (category && typeof category === 'string') {
    filteredComponents = filteredComponents.filter(
      comp => comp.category.toLowerCase() === category.toLowerCase()
    );
  }
  
  // Filter by difficulty
  if (difficulty && typeof difficulty === 'string') {
    filteredComponents = filteredComponents.filter(
      comp => comp.difficulty.toLowerCase() === difficulty.toLowerCase()
    );
  }
  
  // Search by name or description
  if (search && typeof search === 'string') {
    const searchLower = search.toLowerCase();
    filteredComponents = filteredComponents.filter(
      comp => 
        comp.name.toLowerCase().includes(searchLower) ||
        comp.description.toLowerCase().includes(searchLower) ||
        comp.tags.some(tag => tag.toLowerCase().includes(searchLower))
    );
  }
  
  res.json({
    components: filteredComponents,
    total: filteredComponents.length,
    filters: {
      category,
      difficulty,
      search
    }
  });
});

// Get component categories
router.get('/meta/categories', (req: Request, res: Response) => {
  const categories = [...new Set(components.map(comp => comp.category))];
  res.json({ categories });
});

// Get component difficulties
router.get('/meta/difficulties', (req: Request, res: Response) => {
  const difficulties = [...new Set(components.map(comp => comp.difficulty))];
  res.json({ difficulties });
});

// Get component statistics
router.get('/meta/stats', (req: Request, res: Response) => {
  const stats = {
    total: components.length,
    byCategory: components.reduce((acc, comp) => {
      acc[comp.category] = (acc[comp.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
    byDifficulty: components.reduce((acc, comp) => {
      acc[comp.difficulty] = (acc[comp.difficulty] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
    totalTags: [...new Set(components.flatMap(comp => comp.tags))].length
  };
  
  res.json(stats);
});

// Get component by ID (must be last to avoid conflicts)
router.get('/:id', (req: Request, res: Response) => {
  const { id } = req.params;
  const component = components.find(comp => comp.id === id);
  
  if (!component) {
    res.status(404).json({
      error: 'Component not found',
      id
    });
    return;
  }
  
  res.json(component);
});

export { router as componentsRouter }; 