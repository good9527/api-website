import { Link, useLocation } from 'react-router-dom'
import { 
  Menu, 
  Moon, 
  Sun, 
  Bell, 
  Search,
  RefreshCw,
  ExternalLink
} from 'lucide-react'
import { useTheme } from '@/components/common/ThemeProvider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from '@/components/ui/sheet'
import Sidebar from './Sidebar'

export default function Header() {
  const location = useLocation()
  const { theme, setTheme } = useTheme()

  const getPageTitle = () => {
    const titles: Record<string, string> = {
      '/': '数据展示仪表板',
      '/monitor': '数据源状态监控',
      '/api-docs': 'API文档',
      '/history': '历史数据查询',
      '/download': '数据下载中心',
      '/admin': '管理后台'
    }
    return titles[location.pathname] || 'API Platform'
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center px-6">
        {/* Mobile menu */}
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="lg:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">打开菜单</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0">
            <Sidebar />
          </SheetContent>
        </Sheet>

        {/* Page title */}
        <div className="flex-1 flex items-center gap-4">
          <h1 className="text-lg font-semibold">{getPageTitle()}</h1>
          
          {/* Search */}
          <div className="hidden md:flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="搜索..."
                className="w-64 pl-8"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Refresh */}
          <Button variant="ghost" size="icon" title="刷新数据">
            <RefreshCw className="h-4 w-4" />
          </Button>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-4 w-4" />
                <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 text-xs">
                  3
                </Badge>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              <div className="flex items-center justify-between p-2">
                <span className="text-sm font-medium">通知</span>
                <Button variant="ghost" size="sm">
                  全部标记已读
                </Button>
              </div>
              <div className="space-y-1 p-2">
                <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-muted">
                  <div className="w-2 h-2 mt-2 rounded-full bg-green-500" />
                  <div className="flex-1 space-y-1">
                    <p className="text-sm">油价数据更新成功</p>
                    <p className="text-xs text-muted-foreground">2分钟前</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-muted">
                  <div className="w-2 h-2 mt-2 rounded-full bg-yellow-500" />
                  <div className="flex-1 space-y-1">
                    <p className="text-sm">限行数据采集警告</p>
                    <p className="text-xs text-muted-foreground">15分钟前</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-muted">
                  <div className="w-2 h-2 mt-2 rounded-full bg-blue-500" />
                  <div className="flex-1 space-y-1">
                    <p className="text-sm">系统维护通知</p>
                    <p className="text-xs text-muted-foreground">1小时前</p>
                  </div>
                </div>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Theme toggle */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                <span className="sr-only">切换主题</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setTheme("light")}>
                浅色
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setTheme("dark")}>
                深色
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setTheme("system")}>
                系统
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* External link */}
          <Button variant="ghost" size="icon" asChild>
            <a href="/api/health.json" target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4" />
              <span className="sr-only">查看API</span>
            </a>
          </Button>
        </div>
      </div>
    </header>
  )
}