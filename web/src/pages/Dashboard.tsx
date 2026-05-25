import { useState, useEffect } from 'react'
import { 
  BarChart3, 
  TrendingUp, 
  Database, 
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  RefreshCw
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatNumber, formatPercent } from '@/lib/utils'
import { getHealthCheck, getSystemStatus, HealthCheckResponse } from '@/services/api'

export default function Dashboard() {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [systemStatus, setSystemStatus] = useState<{
    totalSources: number
    healthySources: number
    warningSources: number
    errorSources: number
    lastUpdate: string | null
  } | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const [health, status] = await Promise.all([
        getHealthCheck(),
        getSystemStatus()
      ])
      
      setHealthData(health)
      setSystemStatus(status)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取数据失败')
      console.error('获取Dashboard数据失败:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleRefresh = () => {
    fetchData()
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">数据展示仪表板</h2>
          <p className="text-muted-foreground">
            实时监控数据平台运行状态和关键指标
          </p>
        </div>
        <Button onClick={handleRefresh} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          刷新数据
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              数据源总数
            </CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? '-' : systemStatus?.totalSources || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500 flex items-center">
                <ArrowUpRight className="h-3 w-3 mr-1" />
                {isLoading ? '加载中...' : `${systemStatus?.healthySources || 0} 个正常运行`}
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              健康数据源
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {isLoading ? '-' : systemStatus?.healthySources || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500 flex items-center">
                <ArrowUpRight className="h-3 w-3 mr-1" />
                状态正常
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              警告数据源
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">
              {isLoading ? '-' : systemStatus?.warningSources || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-yellow-500 flex items-center">
                <ArrowUpRight className="h-3 w-3 mr-1" />
                需要关注
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              异常数据源
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {isLoading ? '-' : systemStatus?.errorSources || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-red-500 flex items-center">
                <ArrowUpRight className="h-3 w-3 mr-1" />
                需要处理
              </span>
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 图表区域 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* 折线图 */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>数据更新趋势</CardTitle>
            <CardDescription>
              近6个月各数据源更新次数统计
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center justify-center bg-muted/50 rounded-lg">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-muted-foreground">图表区域</p>
                <p className="text-sm text-muted-foreground">需要集成 Recharts 组件</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 饼图 */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>数据源分布</CardTitle>
            <CardDescription>
              各类数据源占比情况
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center justify-center bg-muted/50 rounded-lg">
              <div className="text-center">
                <Database className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-muted-foreground">饼图区域</p>
                <p className="text-sm text-muted-foreground">需要集成 Recharts 组件</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 最近更新 */}
      <Card>
        <CardHeader>
          <CardTitle>数据源状态</CardTitle>
          <CardDescription>
            各数据源最新采集状态
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="p-4 border border-red-200 rounded-lg bg-red-50">
              <p className="text-red-600">加载失败: {error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-2"
                onClick={handleRefresh}
              >
                重试
              </Button>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center p-8">
              <RefreshCw className="h-6 w-6 animate-spin mr-2" />
              <span>加载中...</span>
            </div>
          ) : healthData?.sources ? (
            <div className="space-y-4">
              {Object.entries(healthData.sources).map(([sourceName, sourceData]) => (
                <div key={sourceName} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className={`w-2 h-2 rounded-full ${
                      sourceData.status === 'success' ? 'bg-green-500' : 
                      sourceData.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <p className="font-medium">{sourceName}</p>
                      <p className="text-sm text-muted-foreground">
                        {sourceData.last_updated ? 
                          `最后更新: ${new Date(sourceData.last_updated).toLocaleString('zh-CN')}` : 
                          '暂无更新时间'
                        }
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant={sourceData.status === 'success' ? 'success' : 'warning'}>
                      {sourceData.status === 'success' ? '成功' : 
                       sourceData.status === 'warning' ? '警告' : '异常'}
                    </Badge>
                    {sourceData.records_count !== undefined && (
                      <span className="text-sm text-muted-foreground">
                        {sourceData.records_count} 条记录
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-muted-foreground">
              暂无数据源信息
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}