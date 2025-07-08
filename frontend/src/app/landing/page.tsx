"use client";

import Link from "next/link";
import { RainbowButton } from "@/components/magicui/rainbow-button";
import { Button } from "@/components/ui/button";
import { TextAnimate } from "@/components/magicui/text-animate";
import { ThemeToggle } from "@/components/theme-toggle";
import { ArrowRight, Play, Zap, Target, Brain, GitBranch, Settings, Database } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background transition-colors duration-500">
      
      {/* Workflow Animation Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Animated workflow nodes */}
        <div className="absolute top-20 left-10 w-4 h-4 bg-blue-400/30 rounded-full animate-pulse"></div>
        <div className="absolute top-32 left-32 w-3 h-3 bg-purple-400/30 rounded-full animate-pulse animation-delay-1000"></div>
        <div className="absolute top-60 left-20 w-5 h-5 bg-cyan-400/30 rounded-full animate-pulse animation-delay-2000"></div>
        
        <div className="absolute top-40 right-16 w-4 h-4 bg-pink-400/30 rounded-full animate-pulse animation-delay-500"></div>
        <div className="absolute top-28 right-40 w-3 h-3 bg-indigo-400/30 rounded-full animate-pulse animation-delay-1500"></div>
        <div className="absolute top-72 right-24 w-5 h-5 bg-violet-400/30 rounded-full animate-pulse animation-delay-2500"></div>

        {/* Connecting lines */}
        <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="line-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{stopColor:'rgb(99 102 241)', stopOpacity:0.1}} />
              <stop offset="50%" style={{stopColor:'rgb(139 92 246)', stopOpacity:0.2}} />
              <stop offset="100%" style={{stopColor:'rgb(236 72 153)', stopOpacity:0.1}} />
            </linearGradient>
          </defs>
          <path d="M 40 80 Q 200 120 128 128" stroke="url(#line-gradient)" strokeWidth="2" fill="none" className="animate-pulse" />
          <path d="M 80 240 Q 180 200 80 288" stroke="url(#line-gradient)" strokeWidth="2" fill="none" className="animate-pulse animation-delay-1000" />
          <path d="M 320 112 Q 420 180 384 288" stroke="url(#line-gradient)" strokeWidth="2" fill="none" className="animate-pulse animation-delay-2000" />
        </svg>

        {/* Floating workflow icons */}
        <div className="absolute top-1/4 left-1/4 animate-float-slow">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-xl flex items-center justify-center backdrop-blur-sm border border-border/50">
            <Settings className="w-6 h-6 text-blue-500/60" />
          </div>
        </div>
        
        <div className="absolute top-1/3 right-1/3 animate-float-slow animation-delay-1500">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-xl flex items-center justify-center backdrop-blur-sm border border-border/50">
            <GitBranch className="w-6 h-6 text-purple-500/60" />
          </div>
        </div>
        
        <div className="absolute bottom-1/3 left-1/3 animate-float-slow animation-delay-3000">
          <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 rounded-xl flex items-center justify-center backdrop-blur-sm border border-border/50">
            <Database className="w-6 h-6 text-cyan-500/60" />
          </div>
        </div>
      </div>

      {/* Header */}
      <header className="relative z-20 border-b border-border bg-card/80 backdrop-blur-md">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div 
                className="text-3xl font-black tracking-tight"
                style={{
                  fontFamily: "'Orbitron', 'Inter', sans-serif",
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
                }}
              >
                OASIS OS
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              <Button 
                variant="ghost" 
                className="hover:bg-accent transition-all duration-300" 
                asChild
              >
                <Link href="/workspace">Login</Link>
              </Button>
              <RainbowButton 
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300" 
                asChild
              >
                <Link href="/workspace">Get Started</Link>
              </RainbowButton>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 py-20">
        <div className="relative z-10 text-center max-w-5xl mx-auto">
          
          {/* Main Title */}
          <div className="mb-12">
            <div 
              className="text-7xl md:text-8xl font-black mb-6 tracking-tight leading-none"
              style={{
                fontFamily: "'Orbitron', 'Inter', sans-serif",
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #667eea 75%, #764ba2 100%)',
                backgroundSize: '400% 400%',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                animation: 'gradient-shift 8s ease-in-out infinite',
                filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.1))'
              }}
            >
              OASIS OS
            </div>
            
            <div className="text-2xl md:text-3xl font-semibold text-foreground mb-4">
              Intelligent Workflow Automation
            </div>
          </div>
          
          <TextAnimate
            className="text-lg md:text-xl text-muted-foreground mb-12 max-w-3xl mx-auto leading-relaxed"
            by="word"
            animation="blurInUp"
          >
            Teach OASIS OS your workflows once, and watch it handle your repetitive tasks forever. 
            From file organization to complex automation - your AI workspace agent learns and executes.
          </TextAnimate>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16">
            <RainbowButton 
              className="text-lg px-10 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300" 
              asChild
            >
              <Link href="/workspace" className="flex items-center gap-2">
                Start Your Journey
                <ArrowRight className="w-5 h-5" />
              </Link>
            </RainbowButton>
            
            <Button 
              variant="outline" 
              className="text-lg px-10 py-4 border-2 hover:bg-accent transition-all duration-300"
            >
              <Play className="w-5 h-5 mr-2" />
              Watch Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 px-6 bg-muted/50 backdrop-blur-sm">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-20">
            <h2 
              className="text-4xl md:text-5xl font-black mb-8 tracking-tight"
              style={{
                fontFamily: "'Orbitron', 'Inter', sans-serif",
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              Why Choose OASIS OS?
            </h2>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              The most advanced workspace automation platform that learns from your behavior and executes tasks with precision.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="group bg-card/70 backdrop-blur-md rounded-2xl p-8 border border-border hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:shadow-primary/10">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Brain className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-foreground">Teach Mode</h3>
              <p className="text-muted-foreground leading-relaxed">
                Record your workflows once and OASIS OS learns to replicate them perfectly. No more repetitive tasks.
              </p>
            </div>
            
            <div className="group bg-card/70 backdrop-blur-md rounded-2xl p-8 border border-border hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:shadow-primary/10">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500/10 to-violet-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Zap className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-foreground">Smart Automation</h3>
              <p className="text-muted-foreground leading-relaxed">
                Execute complex workflows with simple commands. From file management to data processing.
              </p>
            </div>
            
            <div className="group bg-card/70 backdrop-blur-md rounded-2xl p-8 border border-border hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:shadow-primary/10">
              <div className="w-16 h-16 bg-gradient-to-br from-pink-500/10 to-rose-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <Target className="w-8 h-8 text-pink-600 dark:text-pink-400" />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-foreground">Custom Workflows</h3>
              <p className="text-muted-foreground leading-relaxed">
                Create personalized automation flows that adapt to your unique work patterns and requirements.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-24 px-6">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 
            className="text-4xl md:text-5xl font-black mb-8 tracking-tight"
            style={{
              fontFamily: "'Orbitron', 'Inter', sans-serif",
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            Ready to Transform Your Workspace?
          </h2>
          <p className="text-lg text-muted-foreground mb-12 leading-relaxed">
            Join thousands of professionals who have revolutionized their productivity with OASIS OS.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <RainbowButton 
              className="text-lg px-10 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300" 
              asChild
            >
              <Link href="/workspace" className="flex items-center gap-2">
                Start Free Trial
                <ArrowRight className="w-5 h-5" />
              </Link>
            </RainbowButton>
            <Button 
              variant="outline" 
              className="text-lg px-10 py-4 border-2 hover:bg-accent transition-all duration-300"
            >
              Schedule Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Simplified Footer */}
      <footer className="relative border-t border-border py-12 px-6 bg-card/80 backdrop-blur-sm">
        <div className="container mx-auto max-w-6xl text-center">
          <div 
            className="text-3xl font-black mb-6 tracking-tight"
            style={{
              fontFamily: "'Orbitron', 'Inter', sans-serif",
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            OASIS OS
          </div>
          <p className="text-muted-foreground mb-8 text-lg">
            The future of intelligent workspace automation.
          </p>
          
          <div className="border-t border-border pt-8 text-muted-foreground">
            <p>&copy; 2025 OASIS OS. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
} 