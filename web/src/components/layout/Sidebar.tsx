import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Activity, 
  FileText, 
  History, 
  Download, 
  Settings,
  Database,
  BarChart3,
  TrendingUp,
  TestTube
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

const routes = [
  {
    label: '数据展示',
    icon: LayoutDashboard,
    href: '/',
    description: '仪表板和图表'
  },
  {
    label: '状态监控',
    icon: Activity,
    href: '/monitor',
    description: '数据源状态'
  },
  {
    label: 'API文档',
    icon: FileText,
    href: '/api-docs',
    description: '接口文档'
  },
  {
    label: '历史查询',
    icon: History,
    href: '/history',
    description: '历史数据'
  },
  {
    label: '数据下载',
    icon: Download,
    href: '/download',
    description: '下载中心'
  },
  {
    label: '管理后台',
    icon: Settings,
    href: '/admin',
    description: '系统管理'
  },
  {
    label: 'API测试',
    icon: TestTube,
    href: '/api-test',
    description: '测试API连接'
  }
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-72 lg:fixed lg:inset-y-0 lg:border-r lg:bg-card lg:dark:bg-card/50">
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary">
            <Database className="w-4 h-4 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold">API Platform</span>
            <span className="text-xs text-muted-foreground">数据平台</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-1">
          {routes.map((route) => {
            const Icon = route.icon
            const isActive = location.pathname === route.href
            
            return (
              <Button
                key={route.href}
                variant={isActive ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start h-12 px-3",
                  isActive && "bg-secondary"
                )}
                asChild
              >
                <Link to={route.href}>
                  <Icon className={cn(
                    "mr-3 h-4 w-4",
                    isActive ? "text-primary" : "text-muted-foreground"
                  )} />
                  <div className="flex flex-col items-start">
                    <span className="text-sm font-medium">{route.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {route.description}
                    </span>
                  </div>
                </Link>
              </Button>
            )
          })}
        </nav>

        <Separator className="my-4" />

        {/* Quick Stats */}
        <div className="space-y-3">
          <h3 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            快速统计
          </h3>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                <span className="text-sm">数据源</span>
              </div>
              <span className="text-sm font-semibold">5</span>
            </div>
            
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span className="text-sm">今日更新</span>
              </div>
              <span className="text-sm font-semibold">3</span>
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-4 border-t">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span>系统运行正常</span>
        </div>
      </div>
    </aside>
  )
}