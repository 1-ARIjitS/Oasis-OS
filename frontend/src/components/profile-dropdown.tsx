"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function ProfileDropdown() {
  const [userName] = React.useState("Arijit Samal")
  const [avatar] = React.useState("👨‍💻")

  const handleProfileAction = (action: string) => {
    switch (action) {
      case 'profile':
        alert('Profile Settings - Update your personal information, preferences, and workspace settings.');
        break;
      case 'account':
        alert('Account Settings - Manage your subscription, billing information, and security settings.');
        break;
      case 'usage':
        alert('Usage Statistics - View your automation usage, time saved, and workflow performance metrics.');
        break;
      case 'billing':
        alert('Billing - Manage your subscription plan, payment methods, and billing history.');
        break;
      case 'support':
        alert('Support - Get help with OASIS OS features, troubleshooting, and technical assistance.');
        break;
      case 'docs':
        alert('Documentation - Access comprehensive guides, API documentation, and tutorials.');
        break;
      case 'logout':
        if (confirm('Are you sure you want to log out of OASIS OS?')) {
          alert('Logging out... You will be redirected to the landing page.');
          window.location.href = '/landing';
        }
        break;
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-10 w-10 rounded-full border-2 border-primary/20 hover:border-primary/40 transition-colors">
          <span className="text-2xl">{avatar}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{userName}</p>
            <p className="text-xs leading-none text-muted-foreground">
              samalarijit.01@gmail.com
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleProfileAction('profile')} className="cursor-pointer">
          🏠 Profile Settings
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleProfileAction('account')} className="cursor-pointer">
          ⚙️ Account Settings
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleProfileAction('usage')} className="cursor-pointer">
          📊 Usage Statistics
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleProfileAction('billing')} className="cursor-pointer">
          💳 Billing
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleProfileAction('support')} className="cursor-pointer">
          🤝 Support
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleProfileAction('docs')} className="cursor-pointer">
          📖 Documentation
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleProfileAction('logout')} className="text-red-600 cursor-pointer">
          🚪 Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 