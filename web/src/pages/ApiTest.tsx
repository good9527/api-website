import { useState, useEffect } from 'react'
import { 
  TestTube, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  Server,
  Database,
  Activity
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getHealthCheck, getSourcesMetadata, HealthCheckResponse, SourcesResponse } from '@/services/api'

export default function ApiTest() {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [sourcesData, setSourcesData] = useState<SourcesResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Array<{
    name: string
    status: 'success' | 'error' | 'loading'
    message: string
  }>>([])

  const runTests = async () => {
    setIsLoading(true)
    setError(null)
    setTestResults([])

    const results: Array<{
      name: string
      status: 'success' | 'error' | 'loading'
      message: string
    }> = []

    // 测试1: 健康检查API
    try {
      setTestResults(prev => [...prev, { name: '健康检查API', status: 'loading', message: '测试中...' }])
      const health = await getHealthCheck()
      setHealthData(health)
      results.push({
        name: '健康检查API',
        status: 'success',
        message: `成功获取 ${Object.keys(health.sources || {}).length} 个数据源状态`
      })
    } catch (err) {
      results.push({
        name: '健康检查API',
        status: 'error',
        message: err instanceof Error ? err.message : '请求失败'
      })
    }

    // 测试2: 数据源元数据API
    try {
      setTestResults(prev => [...prev, { name: '数据源元数据API', status: 'loading', message: '测试中...' }])
      const sources = await getSourcesMetadata()
      setSourcesData(sources)
      results.push({
        name: '数据源元数据API',
        status: 'success',
        message: `成功获取 ${sources.sources?.length || 0} 个数据源信息`
      })
    } catch (err) {
      results.push({
        name: '数据源元数据API',
        status: 'error',
        message: err instanceof Error ? err.message : '请求失败'
      })
    }

    // 测试3: 油价数据API
    try {
      setTestResults(prev => [...prev, { name: '油价数据API', status: 'loading', message: '测试中...' }])
      const response = await fetch('/api/v1/oil-price/latest.json')
      if (response.ok) {
        const data = await response.json()
        results.push({
          name: '油价数据API',
          status: 'success',
          message: `成功获取油价数据，包含 ${data.data?.prices?.length || 0} 条记录`
        })
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (err) {
      results.push({
        name: '油价数据API',
        status: 'error',
        message: err instanceof Error ? err.message : '请求失败'
      })
    }

    // 测试4: 限行信息API
    try {
      setTestResults(prev => [...prev, { name: '限行信息API', status: 'loading', message: '测试中...' }])
      const response = await fetch('/api/v1/traffic-restrict/latest.json')
      if (response.ok) {
        const data = await response.json()
        results.push({
          name: '限行信息API',
          status: 'success',
          message: `成功获取限行信息，包含 ${data.data?.restrictions?.length || 0} 个城市`
        })
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (err) {
      results.push({
        name: '限行信息API',
        status: 'error',
        message: err instanceof Error ? err.message : '请求失败'
      })
    }

    setTestResults(results)
    setIsLoading(false)
  }

  useEffect(() => {
    runTests()
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'loading':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="success">成功</Badge>
      case 'error':
        return <Badge variant="destructive">失败</Badge>
      case 'loading':
        return <Badge variant="secondary">测试中</Badge>
      default:
        return <Badge variant="secondary">未知</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">API测试</h2>
          <p className="text-muted-foreground">
            测试后端API是否正常工作
          </p>
        </div>
        <Button onClick={runTests} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          重新测试
        </Button>
      </div>

      {/* 测试结果 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TestTube className="h-5 w-5" />
            API测试结果
          </CardTitle>
          <CardDescription>
            测试各个API端点是否正常响应
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="p-4 border border-red-200 rounded-lg bg-red-50">
              <p className="text-red-600">测试失败: {error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-2"
                onClick={runTests}
              >
                重试
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {testResults.map((result, index) => (
                <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    {getStatusIcon(result.status)}
                    <div>
                      <p className="font-medium">{result.name}</p>
                      <p className="text-sm text-muted-foreground">{result.message}</p>
                    </div>
                  </div>
                  {getStatusBadge(result.status)}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 数据源状态 */}
      {healthData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              数据源状态
            </CardTitle>
            <CardDescription>
              从健康检查API获取的数据源状态
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(healthData.sources || {}).map(([sourceName, sourceData]) => (
                <div key={sourceName} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className={`w-3 h-3 rounded-full ${
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
                      {sourceData.status === 'success' ? '正常' : 
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
          </CardContent>
        </Card>
      )}

      {/* 服务器信息 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            服务器信息
          </CardTitle>
          <CardDescription>
            前后端服务器连接状态
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium mb-2">前端服务器</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">地址</span>
                  <span className="font-mono">http://localhost:3000</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">状态</span>
                  <Badge variant="success">运行中</Badge>
                </div>
              </div>
            </div>
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium mb-2">后端服务器</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">地址</span>
                  <span className="font-mono">http://localhost:5000</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">状态</span>
                  <Badge variant="success">运行中</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">代理配置</span>
                  <span className="font-mono">/api → localhost:5000</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}