import { useState } from 'react'
import { 
  FileText, 
  Search, 
  Copy, 
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Code,
  BookOpen,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'

// API端点数据
const apiEndpoints = [
  {
    category: '油价数据',
    endpoints: [
      {
        method: 'GET',
        path: '/api/v1/oil-price/latest.json',
        description: '获取最新油价数据',
        response: {
          status: 'success',
          data: {
            update_time: '2026-05-24T14:30:00Z',
            prices: [
              { fuel_type: '92号汽油', price: 7.85, unit: '元/升' },
              { fuel_type: '95号汽油', price: 8.35, unit: '元/升' },
              { fuel_type: '98号汽油', price: 9.33, unit: '元/升' },
              { fuel_type: '0号柴油', price: 7.55, unit: '元/升' }
            ]
          },
          metadata: {
            source: 'oil-price',
            collected_at: '2026-05-24T14:30:00Z',
            version: '20260524-143000',
            quality_score: 0.98
          }
        }
      },
      {
        method: 'GET',
        path: '/api/v1/oil-price/{date}.json',
        description: '获取历史油价数据',
        response: {
          status: 'success',
          data: {
            update_time: '2026-05-23T09:00:00Z',
            prices: [
              { fuel_type: '92号汽油', price: 7.73, unit: '元/升' },
              { fuel_type: '95号汽油', price: 8.22, unit: '元/升' }
            ]
          }
        }
      }
    ]
  },
  {
    category: '限行信息',
    endpoints: [
      {
        method: 'GET',
        path: '/api/v1/traffic-restrict/latest.json',
        description: '获取最新限行信息',
        response: {
          status: 'success',
          data: {
            update_time: '2026-05-24T08:00:00Z',
            restrictions: [
              {
                city: '北京',
                rule: '工作日早晚高峰时段限行',
                time_range: '工作日7:00-9:00，17:00-20:00'
              }
            ]
          }
        }
      }
    ]
  },
  {
    category: '系统状态',
    endpoints: [
      {
        method: 'GET',
        path: '/api/health.json',
        description: 'API健康状态检查',
        response: {
          status: 'success',
          timestamp: '2026-05-24T15:00:00Z',
          sources: {
            'oil-price': { status: 'healthy', last_updated: '2026-05-24T14:30:00Z' },
            'traffic-restrict': { status: 'healthy', last_updated: '2026-05-24T08:00:00Z' }
          }
        }
      },
      {
        method: 'GET',
        path: '/api/metadata/sources.json',
        description: '获取所有数据源状态',
        response: {
          sources: [
            { name: 'oil-price', status: 'healthy', quality_score: 0.98 },
            { name: 'traffic-restrict', status: 'healthy', quality_score: 0.95 }
          ]
        }
      }
    ]
  }
]

export default function ApiDocs() {
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedEndpoints, setExpandedEndpoints] = useState<string[]>([])

  const toggleEndpoint = (path: string) => {
    setExpandedEndpoints(prev => 
      prev.includes(path) 
        ? prev.filter(p => p !== path)
        : [...prev, path]
    )
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const filteredEndpoints = apiEndpoints.map(category => ({
    ...category,
    endpoints: category.endpoints.filter(endpoint =>
      endpoint.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.endpoints.length > 0)

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">API文档</h2>
        <p className="text-muted-foreground">
          查看所有API端点、请求参数和响应格式
        </p>
      </div>

      {/* 搜索 */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          type="search"
          placeholder="搜索API端点..."
          className="pl-8"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* 快速开始 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            快速开始
          </CardTitle>
          <CardDescription>
            使用以下示例快速开始调用API
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">获取最新油价</p>
              <code className="text-sm bg-background p-2 rounded block">
                curl -X GET "https://api.example.com/api/v1/oil-price/latest.json"
              </code>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">检查API状态</p>
              <code className="text-sm bg-background p-2 rounded block">
                curl -X GET "https://api.example.com/api/health.json"
              </code>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API端点列表 */}
      <div className="space-y-6">
        {filteredEndpoints.map((category) => (
          <Card key={category.category}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                {category.category}
              </CardTitle>
              <CardDescription>
                {category.endpoints.length} 个端点
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {category.endpoints.map((endpoint) => (
                  <div key={endpoint.path} className="border rounded-lg">
                    {/* 端点头部 */}
                    <div 
                      className="flex items-center justify-between p-4 cursor-pointer"
                      onClick={() => toggleEndpoint(endpoint.path)}
                    >
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="font-mono">
                          {endpoint.method}
                        </Badge>
                        <code className="text-sm font-medium">{endpoint.path}</code>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">
                          {endpoint.description}
                        </span>
                        {expandedEndpoints.includes(endpoint.path) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </div>
                    </div>

                    {/* 端点详情 */}
                    {expandedEndpoints.includes(endpoint.path) && (
                      <div className="border-t p-4">
                        <div className="space-y-4">
                          {/* 描述 */}
                          <div>
                            <h4 className="text-sm font-medium mb-2">描述</h4>
                            <p className="text-sm text-muted-foreground">
                              {endpoint.description}
                            </p>
                          </div>

                          <Separator />

                          {/* 响应示例 */}
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="text-sm font-medium">响应示例</h4>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyToClipboard(JSON.stringify(endpoint.response, null, 2))}
                              >
                                <Copy className="h-4 w-4 mr-1" />
                                复制
                              </Button>
                            </div>
                            <pre className="p-4 bg-muted rounded-lg overflow-x-auto text-sm">
                              <code>{JSON.stringify(endpoint.response, null, 2)}</code>
                            </pre>
                          </div>

                          {/* 使用示例 */}
                          <div>
                            <h4 className="text-sm font-medium mb-2">使用示例</h4>
                            <div className="space-y-2">
                              <div className="p-3 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground mb-1">JavaScript (fetch)</p>
                                <code className="text-sm">
{`fetch('${endpoint.path}')
  .then(response => response.json())
  .then(data => console.log(data))`}
                                </code>
                              </div>
                              <div className="p-3 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground mb-1">Python (requests)</p>
                                <code className="text-sm">
{`import requests
response = requests.get('https://api.example.com${endpoint.path}')
data = response.json()`}
                                </code>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 错误码说明 */}
      <Card>
        <CardHeader>
          <CardTitle>错误码说明</CardTitle>
          <CardDescription>
            API可能返回的错误码及说明
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div>
                <code className="font-mono">200</code>
                <span className="ml-2 text-sm">成功</span>
              </div>
              <Badge variant="success">正常</Badge>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div>
                <code className="font-mono">404</code>
                <span className="ml-2 text-sm">数据不存在</span>
              </div>
              <Badge variant="warning">警告</Badge>
            </div>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div>
                <code className="font-mono">500</code>
                <span className="ml-2 text-sm">服务器错误</span>
              </div>
              <Badge variant="destructive">错误</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}