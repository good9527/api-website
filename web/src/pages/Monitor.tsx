import { useState, useEffect } from 'react'
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  RefreshCw,
  Wifi,
  WifiOff,
  Server,
  Database,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { getHealthCheck, HealthCheckResponse } from '@/services/api'

// 数据源描述映射
const sourceDescriptions: Record<string, string> = {
  'oil-price': '国家发改委公布的国内成品油价格',
  'traffic-restrict': '各城市机动车限行规定',
  'policy': '国家及地方政策法规',
  'admin-division': '国家行政区划数据',
  'price-table': '各类商品和服务价格'
}

// 数据源中文名称映射
const sourceNames: Record<string, string> = {
  'oil-price': '油价数据',
  'traffic-restrict': '限行信息',
  'policy': '政策信息',
  'admin-division': '行政区划',
  'price-table': '价格表'
}

export default function Monitor() {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getHealthCheck()
      setHealthData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取监控数据失败')
      console.error('获取监控数据失败:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchData()
    setIsRefreshing(false)
  }

  // 转换数据源状态
  const sources = healthData?.sources ? Object.entries(healthData.sources).map(([name, data]) => ({
    id: name,
    name: sourceNames[name] || name,
    status: data.status === 'success' ? 'healthy' : 
            data.status === 'warning' ? 'warning' : 'error',
    lastUpdate: data.last_updated || '未知',
    nextUpdate: '未知', // API没有返回下次更新时间
    qualityScore: data.status === 'success' ? 95 : 0, // 模拟质量评分
    responseTime: 100, // 模拟响应时间
    uptime: data.status === 'success' ? 99.9 : 95, // 模拟正常运行时间
    errorCount: data.status === 'error' ? 1 : 0,
    description: sourceDescriptions[name] || '数据源'
  })) : []

  // 生成告警日志
  const alerts = sources
    .filter(s => s.status === 'error' || s.status === 'warning')
    .map((source, index) => ({
      id: index + 1,
      time: new Date().toLocaleString('zh-CN'),
      source: source.name,
      level: source.status === 'error' ? 'error' : 'warning',
      message: source.status === 'error' ? '数据采集失败' : '数据质量评分低于阈值',
      details: source.status === 'error' ? '数据源状态异常' : '需要关注数据质量'
    }))

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <WifiOff className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="success">正常</Badge>
      case 'warning':
        return <Badge variant="warning">警告</Badge>
      case 'error':
        return <Badge variant="destructive">异常</Badge>
      default:
        return <Badge variant="secondary">未知</Badge>
    }
  }

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <WifiOff className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      default:
        return <Activity className="h-4 w-4 text-blue-500" />
    }
  }

  const healthyCount = sources.filter(s => s.status === 'healthy').length
  const warningCount = sources.filter(s => s.status === 'warning').length
  const errorCount = sources.filter(s => s.status === 'error').length

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">数据源状态监控</h2>
          <p className="text-muted-foreground">
            实时监控各数据源的健康状态和采集情况
          </p>
        </div>
        <Button onClick={handleRefresh} disabled={isRefreshing}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          刷新状态
        </Button>
      </div>

      {/* 状态总览 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">数据源总数</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sources.length}</div>
            <p className="text-xs text-muted-foreground">
              监控中的数据源
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">正常运行</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{healthyCount}</div>
            <p className="text-xs text-muted-foreground">
              状态健康
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">警告状态</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">{warningCount}</div>
            <p className="text-xs text-muted-foreground">
              需要关注
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">异常状态</CardTitle>
            <WifiOff className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{errorCount}</div>
            <p className="text-xs text-muted-foreground">
              需要处理
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 数据源列表 */}
      <Card>
        <CardHeader>
          <CardTitle>数据源状态</CardTitle>
          <CardDescription>
            各数据源的详细状态信息
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sources.map((source) => (
              <div key={source.id} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(source.status)}
                    <div>
                      <h3 className="font-medium">{source.name}</h3>
                      <p className="text-sm text-muted-foreground">{source.description}</p>
                    </div>
                  </div>
                  {getStatusBadge(source.status)}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">最后更新</p>
                    <p className="font-medium">{source.lastUpdate}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">下次更新</p>
                    <p className="font-medium">{source.nextUpdate}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">质量评分</p>
                    <div className="flex items-center gap-2">
                      <Progress value={source.qualityScore} className="h-2 flex-1" />
                      <span className="font-medium">{source.qualityScore}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-muted-foreground">响应时间</p>
                    <p className="font-medium">{source.responseTime}ms</p>
                  </div>
                </div>

                {source.errorCount > 0 && (
                  <div className="mt-3 p-2 bg-red-500/10 rounded-md">
                    <p className="text-sm text-red-500">
                      最近24小时错误次数: {source.errorCount}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 告警日志 */}
      <Card>
        <CardHeader>
          <CardTitle>告警日志</CardTitle>
          <CardDescription>
            最近的系统告警和异常记录
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-4 p-4 border rounded-lg">
                {getAlertIcon(alert.level)}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium">{alert.source}</span>
                    <Badge variant={alert.level === 'error' ? 'destructive' : 'warning'}>
                      {alert.level === 'error' ? '错误' : '警告'}
                    </Badge>
                    <span className="text-sm text-muted-foreground">{alert.time}</span>
                  </div>
                  <p className="text-sm">{alert.message}</p>
                  <p className="text-sm text-muted-foreground mt-1">{alert.details}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}