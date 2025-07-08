"use client";

import { useState, useRef, useEffect } from "react";

import { Meteors } from "@/components/magicui/meteors";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { ShineBorder } from "@/components/magicui/shine-border";

import { Button } from "@/components/ui/button";
import { AnimatedBeam } from "@/components/magicui/animated-beam";
import { ThemeToggle } from "@/components/theme-toggle";
import { ProfileDropdown } from "@/components/profile-dropdown";
import { WorkflowBackground } from "@/components/workflow-background";

interface Project {
  id: string;
  name: string;
  status: "Active" | "In Review" | "Complete";
  items: string[];
  progress: number;
  timeSaved?: string;
  dueDate?: string;
  description: string;
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  category: string;
}

const projects: Project[] = [
  {
    id: "website",
    name: "Edit Website Presentation",
    description: "Updating presentation with new visual elements and improved design",
    status: "Active",
    items: [
      "🎨 New brand elements integrated",
      "📊 Interactive charts added", 
      "✨ Animation effects applied",
      "🔄 Client feedback pending"
    ],
    progress: 78,
    timeSaved: "4.2h",
    dueDate: "Tomorrow"
  },
  {
    id: "excel",
    name: "Excel Bookkeeping",
    description: "Automated financial data processing and report generation",
    status: "In Review",
    items: [
      "💰 Q4 financial data processed",
      "📈 Monthly reports generated", 
      "🔍 Audit trails created",
      "📧 Sent to accounting team"
    ],
    progress: 92,
    timeSaved: "6.8h",
    dueDate: "Friday"
  },
  {
    id: "forms",
    name: "PDF Form Filling from Spreadsheets",
    description: "Automated form population from structured data sources",
    status: "Active",
    items: [
      "📄 Form templates mapped",
      "🗂️ Data sources linked", 
      "⚡ Automation workflows active",
      "📋 Batch processing enabled"
    ],
    progress: 65,
    timeSaved: "3.5h",
    dueDate: "Next Week"
  }
];

const defaultWorkflows: Workflow[] = [
  { id: "email", name: "Email Organization", description: "Sort and categorize incoming emails", category: "Productivity" },
  { id: "files", name: "File Management", description: "Organize downloads and documents", category: "Organization" },
  { id: "backup", name: "Daily Backup", description: "Backup important files and folders", category: "Maintenance" },
  { id: "reports", name: "Weekly Reports", description: "Generate and send weekly summaries", category: "Reporting" },
  { id: "calendar", name: "Calendar Sync", description: "Sync events across platforms", category: "Productivity" }
];

// Backend API base URL. Use environment variable if available, otherwise default to localhost.
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function WorkspacePage() {
  const [selectedNav, setSelectedNav] = useState("home");
  const [workflowName, setWorkflowName] = useState("");
  const [selectedWorkflow, setSelectedWorkflow] = useState("");
  const [customQuery, setCustomQuery] = useState("");
  // Execution mode: 'online' uses GPT-4.1 (OpenAI), 'offline' uses local Llama model
  const [executionMode, setExecutionMode] = useState<string>("online");
  const [today, setToday] = useState<string>("");

  const containerRef = useRef<HTMLDivElement>(null);
  const projectRef = useRef<HTMLDivElement>(null);
  const workflowRef = useRef<HTMLDivElement>(null);

  // Set date on client side to avoid hydration mismatch
  useEffect(() => {
    setToday(new Date().toLocaleDateString('en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    }));
  }, []);

  const navItems = [
    { id: "home", label: "Home", icon: "🏠" },
    { id: "projects", label: "Projects", icon: "📂" },
    { id: "workflows", label: "Workflows", icon: "⚙️" },
    { id: "notes", label: "Notes", icon: "📝" },
    { id: "files", label: "Files", icon: "📄" },
    { id: "settings", label: "Settings", icon: "🔧" },
  ];

  // Create workflow execution popup
  const createPopup = (title: string, message: string, type: 'recording' | 'executing') => {
    // Minimize screen
    document.body.style.transform = "scale(0.85)";
    document.body.style.transition = "transform 0.5s ease";
    
    // Create overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(10px);
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
    `;

    const popup = document.createElement('div');
    popup.style.cssText = `
      background: linear-gradient(135deg, #1e293b, #334155);
      border: 2px solid #3b82f6;
      border-radius: 20px;
      padding: 40px;
      text-align: center;
      color: white;
      max-width: 500px;
      width: 90%;
      box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
      animation: popupEnter 0.3s ease-out;
    `;

    if (type === 'recording') {
      popup.innerHTML = `
        <div style="margin-bottom: 20px;">
          <div style="width: 80px; height: 80px; background: #ef4444; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; animation: pulse 2s infinite;">
            🔴
          </div>
          <h2 style="font-size: 28px; font-weight: bold; margin: 0 0 10px;">${title}</h2>
          <p style="font-size: 16px; color: #cbd5e1; margin: 0 0 30px;">${message}</p>
          <button id="pauseBtn" style="background: linear-gradient(45deg, #ef4444, #dc2626); border: none; color: white; padding: 15px 30px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s;">
            ⏸️ Pause Recording
          </button>
        </div>
      `;
    } else {
      popup.innerHTML = `
        <div style="margin-bottom: 20px;">
          <div style="width: 80px; height: 80px; background: linear-gradient(45deg, #3b82f6, #8b5cf6); border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; animation: spin 2s linear infinite;">
            ⚡
          </div>
          <h2 style="font-size: 28px; font-weight: bold; margin: 0 0 10px;">${title}</h2>
          <p style="font-size: 16px; color: #cbd5e1; margin: 0;">${message}</p>
        </div>
      `;
    }

    overlay.appendChild(popup);
    document.body.appendChild(overlay);

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
      @keyframes popupEnter {
        from { opacity: 0; transform: scale(0.8) translateY(-20px); }
        to { opacity: 1; transform: scale(1) translateY(0); }
      }
      @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
      }
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);

    return { overlay, popup, style };
  };

  const closePopup = (overlay: HTMLElement, style: HTMLElement) => {
    document.body.style.transform = "scale(1)";
    overlay.remove();
    style.remove();
  };

  const showNotification = (message: string, type: 'success' | 'info' = 'success') => {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${type === 'success' ? 'linear-gradient(45deg, #10b981, #059669)' : 'linear-gradient(45deg, #3b82f6, #1d4ed8)'};
      color: white;
      padding: 16px 24px;
      border-radius: 12px;
      z-index: 10000;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
      animation: slideIn 0.3s ease-out;
      font-weight: 500;
    `;
    notification.textContent = message;

    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from { opacity: 0; transform: translateX(100%); }
        to { opacity: 1; transform: translateX(0); }
      }
    `;
    document.head.appendChild(style);
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
      style.remove();
    }, 4000);
  };

  const handleTeachWorkflow = async () => {
    if (!workflowName.trim()) return;

    try {
      // Call backend to start recording
      const res = await fetch(`${API_BASE}/start_recording/${encodeURIComponent(workflowName.trim())}`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showNotification(`❌ Failed to start recording: ${err.detail ?? res.statusText}`, 'info');
        return;
      }

      // Show recording popup
      const { overlay, popup, style } = createPopup(
        'Recording Workflow',
        'Voice and screen are being recorded. Complete your task and click pause when finished.',
        'recording'
      );

      const pauseBtn = popup.querySelector('#pauseBtn') as HTMLButtonElement;
      pauseBtn?.addEventListener('click', async () => {
        pauseBtn.disabled = true;
        pauseBtn.textContent = '⏳ Stopping...';

        try {
          const stopRes = await fetch(`${API_BASE}/stop_recording`, { method: 'POST' });
          if (!stopRes.ok) {
            const err = await stopRes.json().catch(() => ({}));
            showNotification(`❌ Failed to stop recording: ${err.detail ?? stopRes.statusText}`, 'info');
            pauseBtn.disabled = false;
            pauseBtn.textContent = '⏸️ Pause Recording';
            return;
          }
          closePopup(overlay, style);
          setTimeout(() => {
            showNotification(`✅ Workflow "${workflowName}" saved successfully! Added to your Workflows tab.`);
            setWorkflowName("");
          }, 500);
        } catch (err) {
          console.error(err);
          showNotification('❌ Error communicating with backend', 'info');
        }
      });
    } catch (err) {
      console.error(err);
      showNotification('❌ Error communicating with backend', 'info');
    }
  };

  const handleExecuteWorkflow = async () => {
    if (!selectedWorkflow) return;

    const selectedWf = defaultWorkflows.find((wf) => wf.id === selectedWorkflow);
    if (!selectedWf) return;

    // Show executing popup immediately
    const { overlay, style } = createPopup(
      'Executing Workflow',
      `Running "${selectedWf.name}" automation...`,
      'executing'
    );

    try {
      const res = await fetch(`${API_BASE}/run_workflow/complex`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        closePopup(overlay, style);
        showNotification(`❌ Workflow execution failed: ${err.detail ?? res.statusText}`, 'info');
        return;
      }
      // After backend confirms completion, close popup and notify
      closePopup(overlay, style);
      showNotification(`✅ Workflow "${selectedWf.name}" executed successfully!`);
    } catch (err) {
      console.error(err);
      closePopup(overlay, style);
      showNotification('❌ Error communicating with backend', 'info');
    }
  };

  const handleCustomWorkflow = async () => {
    if (!customQuery.trim()) return;
    
    const { overlay, style } = createPopup(
      'Processing Custom Workflow',
      'AI is analyzing and executing your custom task...',
      'executing'
    );

    try {
      console.log('Starting workflow execution...', { query: customQuery });
      
      // Start workflow execution
      const modelToSend = executionMode === "online" ? "gpt-4.1" : "llama-3.3-70b-versatile";

      const executeResponse = await fetch('http://localhost:8000/api/v1/workflow/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          query: customQuery,
          model: modelToSend
        })
      });

      console.log('Execute response status:', executeResponse.status);

      if (!executeResponse.ok) {
        const errorText = await executeResponse.text();
        console.error('Execute response error:', errorText);
        throw new Error(`Failed to start workflow: ${executeResponse.status} - ${errorText}`);
      }

      const executeData = await executeResponse.json();
      const workflowId = executeData.workflow_id;

      // Poll for workflow status
      const checkStatus = async (): Promise<boolean> => {
        try {
          const statusResponse = await fetch(`http://localhost:8000/api/v1/workflow/${workflowId}/status`, {
            headers: {
              'Accept': 'application/json',
            }
          });
          
          if (!statusResponse.ok) {
            const errorText = await statusResponse.text();
            console.error('Status response error:', errorText);
            throw new Error(`Failed to get status: ${statusResponse.status} - ${errorText}`);
          }

          const statusData = await statusResponse.json();
          console.log('Workflow status:', statusData);
          
          if (statusData.status === 'completed') {
            closePopup(overlay, style);
            setTimeout(() => {
              showNotification('✅ Workflow successfully executed!');
              setCustomQuery("");
            }, 500);
            return true;
          } else if (statusData.status === 'failed') {
            throw new Error(statusData.message || 'Workflow execution failed');
          } else if (statusData.status === 'cancelled') {
            throw new Error('Workflow was cancelled');
          }
          
          // Still running, check again in 2 seconds
          return false;
        } catch (error) {
          console.error('Error checking workflow status:', error);
          throw error;
        }
      };

      // Poll every 2 seconds for up to 5 minutes
      const maxAttempts = 150; // 5 minutes with 2-second intervals
      let attempts = 0;
      
      const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
          const isComplete = await checkStatus();
          
          if (isComplete || attempts >= maxAttempts) {
            clearInterval(pollInterval);
            
            if (attempts >= maxAttempts) {
              throw new Error('Workflow timeout - taking too long to complete');
            }
          }
        } catch (error) {
          clearInterval(pollInterval);
          throw error;
        }
      }, 2000);

    } catch (error) {
      console.error('Workflow execution error:', error);
      closePopup(overlay, style);
      setTimeout(() => {
        showNotification(`❌ Workflow failed: ${error instanceof Error ? error.message : 'Unknown error'}`, 'info');
      }, 500);
    }
  };

  const handleNavigation = (navId: string) => {
    setSelectedNav(navId);
    
    const navActions = {
      home: () => showNotification('Welcome to your workspace dashboard', 'info'),
      projects: () => showNotification('Projects view - Manage your active projects and track progress', 'info'),
      workflows: () => showNotification('Workflows center - Create and manage your automations', 'info'),
      notes: () => showNotification('Notes workspace - Access your daily notes and meeting summaries', 'info'),
      files: () => showNotification('File manager - Organize and search through your documents', 'info'),
      settings: () => showNotification('Workspace settings - Customize your OASIS OS experience', 'info'),
    };

    navActions[navId as keyof typeof navActions]?.();
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Enhanced Sidebar */}
      <aside className="w-80 border-r border-border bg-card/50 backdrop-blur-xl">
        <div className="p-8">
          {/* Enhanced OASIS OS Branding */}
          <div className="mb-8">
            <h1 className="text-4xl font-black bg-gradient-to-r from-cyan-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3 tracking-wider">
              OASIS OS
            </h1>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-muted-foreground font-medium">Workspace Agent Active</span>
            </div>
          </div>
        </div>
        
        <nav className="px-6 space-y-3">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavigation(item.id)}
              className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl text-sm font-semibold transition-all duration-300 ${
                selectedNav === item.id
                  ? "bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-700 dark:text-blue-300 shadow-lg border-2 border-blue-500/30"
                  : "hover:bg-gradient-to-r hover:from-slate-100 hover:to-blue-100 dark:hover:from-slate-700 dark:hover:to-slate-600 hover:text-slate-700 dark:hover:text-slate-200"
              }`}
            >
              <span className="text-2xl">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Enhanced Workflow Status */}
        <div className="p-6 mt-8">
          <div className="bg-gradient-to-r from-emerald-500/10 to-blue-500/10 rounded-2xl p-6 border-2 border-emerald-500/20">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-emerald-500 text-2xl">✨</span>
              <span className="text-sm font-bold">Active Automations</span>
            </div>
            <div className="text-3xl font-black bg-gradient-to-r from-emerald-500 to-blue-500 bg-clip-text text-transparent">
              <NumberTicker value={7} />
            </div>
            <div className="text-xs text-muted-foreground font-medium">Running workflows</div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-background">
        {/* Enhanced Header */}
        <header className="border-b border-border bg-card/50 backdrop-blur-md px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-700 to-slate-900 dark:from-slate-200 dark:to-slate-400 bg-clip-text text-transparent">
                Workspace Dashboard
              </h2>
              <div className="text-sm text-muted-foreground font-medium">
                {today}
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <ProfileDropdown />
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-8 space-y-10">
          {/* Enhanced Workspace Overview */}
          <section>
            <h2 className="text-4xl font-black mb-3 bg-gradient-to-r from-cyan-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Workspace Overview
            </h2>
            <p className="text-muted-foreground mb-10 text-lg">Monitor your active projects and automation performance</p>

            {/* Projects Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-10" ref={containerRef}>
              {projects.map((project, index) => (
                <ShineBorder
                  key={project.id}
                  className="relative"
                  shineColor={
                    project.status === "Active"
                      ? ["#3b82f6", "#8b5cf6"]
                      : project.status === "In Review"
                      ? ["#f59e0b", "#eab308"]
                      : ["#10b981", "#059669"]
                  }
                >
                  <div className="p-8 bg-card/90 rounded-2xl backdrop-blur-sm" ref={index === 0 ? projectRef : undefined}>
                    <div className="flex justify-between items-start mb-5">
                      <div>
                        <h3 className="font-bold text-xl mb-2">{project.name}</h3>
                        <p className="text-sm text-muted-foreground leading-relaxed">{project.description}</p>
                      </div>
                      <span
                        className={`text-xs px-4 py-2 rounded-full font-bold ${
                          project.status === "Active"
                            ? "bg-blue-500/20 text-blue-700 dark:text-blue-300"
                            : project.status === "In Review"
                            ? "bg-yellow-500/20 text-yellow-700 dark:text-yellow-300"
                            : "bg-green-500/20 text-green-700 dark:text-green-300"
                        }`}
                      >
                        {project.status}
                      </span>
                    </div>
                    
                    {/* Enhanced Progress Bar */}
                    <div className="mb-6">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="font-medium">Progress</span>
                        <span className="font-bold">{project.progress}%</span>
                      </div>
                      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-1000 shadow-sm"
                          style={{ width: `${project.progress}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    <ul className="space-y-3 mb-6">
                      {project.items.map((item, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-center gap-3">
                          <span className="text-xs">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                    
                    <div className="flex justify-between items-center text-sm">
                      <div className="text-muted-foreground">
                        Due: <span className="text-foreground font-bold">{project.dueDate}</span>
                      </div>
                      <div className="font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        {project.timeSaved} saved
                      </div>
                    </div>
                  </div>
                </ShineBorder>
              ))}
            </div>

            {/* Enhanced Stats Grid */}
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-6">
              <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-2xl p-8 border-2 border-blue-500/20 backdrop-blur-sm">
                <div className="text-4xl font-black bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent mb-3">
                  <NumberTicker value={14.3} decimalPlaces={1} />h
                </div>
                <p className="text-sm text-muted-foreground font-medium">Time saved this week</p>
              </div>
              <div className="bg-gradient-to-br from-emerald-500/10 to-green-500/10 rounded-2xl p-8 border-2 border-emerald-500/20 backdrop-blur-sm">
                <div className="text-4xl font-black bg-gradient-to-r from-emerald-500 to-green-500 bg-clip-text text-transparent mb-3">
                  <NumberTicker value={3} />
                </div>
                <p className="text-sm text-muted-foreground font-medium">Active projects</p>
              </div>
              <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-2xl p-8 border-2 border-amber-500/20 backdrop-blur-sm">
                <div className="text-4xl font-black bg-gradient-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent mb-3">
                  <NumberTicker value={32} />
                </div>
                <p className="text-sm text-muted-foreground font-medium">Files organized today</p>
              </div>
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl p-8 border-2 border-purple-500/20 backdrop-blur-sm">
                <div className="text-4xl font-black bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent mb-3">
                  <NumberTicker value={7} />
                </div>
                <p className="text-sm text-muted-foreground font-medium">Workflows running</p>
              </div>
            </div>
          </section>

          {/* Create your own Workflow automation */}
          <section className="relative">
            <h2 className="text-4xl font-black mb-8 bg-gradient-to-r from-cyan-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Create your own Workflow automation
            </h2>
            
            {/* Top Row: Teach Mode and Default Workflow */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Teach Mode Box */}
              <div className="bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-2xl p-8 border-2 border-blue-500/20 hover:border-blue-500/40 transition-all duration-300 backdrop-blur-sm">
                <div className="text-5xl mb-6">🧠</div>
                <h3 className="text-2xl font-bold mb-3">Teach Mode</h3>
                <p className="text-muted-foreground mb-8 text-sm leading-relaxed">
                  Teach your own agentic OS to replicate a task you do so that you never think of it again.
                </p>
                
                <div className="space-y-5">
                  <input
                    type="text"
                    placeholder="Enter workflow name..."
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    className="w-full px-6 py-4 rounded-xl border-2 bg-background/50 backdrop-blur-sm focus:outline-none focus:ring-4 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                  />
                  
                  <Button
                    onClick={handleTeachWorkflow}
                    disabled={!workflowName.trim()}
                    className="w-full py-4 text-lg font-bold bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-xl transition-all duration-300"
                  >
                    ▶️ Teach
                  </Button>
                </div>
              </div>

              {/* Perform Default Workflow Box */}
              <div className="bg-gradient-to-br from-emerald-500/5 to-green-500/5 rounded-2xl p-8 border-2 border-emerald-500/20 hover:border-emerald-500/40 transition-all duration-300 backdrop-blur-sm">
                <div className="text-5xl mb-6">⚡</div>
                <h3 className="text-2xl font-bold mb-3">Perform Default Workflow</h3>
                <p className="text-muted-foreground mb-8 text-sm leading-relaxed">
                  Execute pre-built workflows to automate common tasks instantly.
                </p>
                
                <div className="space-y-5">
                  <select
                    value={selectedWorkflow}
                    onChange={(e) => setSelectedWorkflow(e.target.value)}
                    className="w-full px-6 py-4 rounded-xl border-2 bg-background/50 backdrop-blur-sm focus:outline-none focus:ring-4 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all"
                  >
                    <option value="">Select a workflow...</option>
                    {defaultWorkflows.map((workflow) => (
                      <option key={workflow.id} value={workflow.id}>
                        {workflow.name} - {workflow.category}
                      </option>
                    ))}
                  </select>
                  
                  <Button
                    onClick={handleExecuteWorkflow}
                    disabled={!selectedWorkflow}
                    className="w-full py-4 text-lg font-bold bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 rounded-xl transition-all duration-300"
                  >
                    ▶️ Execute
                  </Button>
                </div>
              </div>
            </div>

            {/* Bottom Row: Custom Workflows */}
            <div className="max-w-4xl mx-auto" ref={workflowRef}>
              <div className="bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-2xl p-8 border-2 border-purple-500/20 hover:border-purple-500/40 transition-all duration-300 backdrop-blur-sm">
                <div className="text-5xl mb-6">🎯</div>
                <h3 className="text-2xl font-bold mb-3">Perform Custom Workflows</h3>
                <p className="text-muted-foreground mb-8 text-sm leading-relaxed">
                  Describe any task in detail and let AI execute it for you.
                </p>
                
                <div className="space-y-5">
                  <textarea
                    placeholder="Describe your task in detail... (e.g., 'Organize all PDF files in Downloads folder by date and move invoices to Finance folder')"
                    value={customQuery}
                    onChange={(e) => setCustomQuery(e.target.value)}
                    rows={4}
                    className="w-full px-6 py-4 rounded-xl border-2 bg-background/50 backdrop-blur-sm focus:outline-none focus:ring-4 focus:ring-purple-500/30 focus:border-purple-500 resize-none transition-all"
                  />
                  
                  {/* Execution mode selection: Online (GPT-4.1) vs Offline (local Llama) */}
                  <select
                    value={executionMode}
                    onChange={(e) => setExecutionMode(e.target.value)}
                    className="w-full px-6 py-4 rounded-xl border-2 bg-background/50 backdrop-blur-sm focus:outline-none focus:ring-4 focus:ring-purple-500/30 focus:border-purple-500 transition-all"
                  >
                    <option value="online">Online</option>
                    <option value="offline">Offline</option>
                  </select>

                  <div className="text-xs text-muted-foreground mb-3 flex items-center gap-2">
                    <span>💡</span>
                    <span>Be specific about what you want to achieve for best results</span>
                  </div>
                  
                  <Button
                    onClick={handleCustomWorkflow}
                    disabled={!customQuery.trim()}
                    className="w-full py-4 text-lg font-bold bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-xl transition-all duration-300"
                  >
                    ▶️ Execute Query
                  </Button>
                </div>
              </div>
            </div>

            {/* Add animated beams between elements */}
            {containerRef.current && projectRef.current && workflowRef.current && (
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={projectRef}
                toRef={workflowRef}
                curvature={50}
                startYOffset={10}
                endYOffset={-10}
              />
            )}
          </section>
        </div>

        {/* Enhanced Background Effects */}
        <div className="fixed inset-0 w-full h-full -z-10 opacity-5 dark:opacity-10">
          <Meteors number={12} />
        </div>
        
        {/* Use the WorkflowBackground component for floating particles */}
        <WorkflowBackground />
      </main>
    </div>
  );
} 