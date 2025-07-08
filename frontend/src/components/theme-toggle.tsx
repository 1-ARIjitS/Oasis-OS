"use client"

import * as React from "react"
import { useTheme } from "next-themes"
import { Sun, Moon } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      className="relative h-10 w-10 rounded-full"
    >
      <div className="relative w-full h-full flex items-center justify-center">
        {theme === "light" ? (
          <Moon className="h-4 w-4 transition-all duration-300 rotate-0 scale-100" />
        ) : (
          <Sun className="h-4 w-4 transition-all duration-300 rotate-0 scale-100" />
        )}
      </div>
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
} 