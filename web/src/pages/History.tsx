import { useState, useEffect } from 'react'
import { 
  History as HistoryIcon, 
  Calendar, 
  Search, 
  Download,
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  Clock,
  Database
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { getHealthCheck, HealthCheckResponse } from '@/services/api'

// 数据源中文名称映射
const sourceNames: Record<string, string> = {
  'oil-price': '油价数据',
  'traffic-restrict': '限行信息',
  'policy': '政策信息',
  'admin-division': '行政区划',
  'price-table': '价格表'
}

export default function HistoryPage() {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 5

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getHealthCheck()
      setHealthData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取历史数据失败')
      console.error('获取历史数据失败:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // 转换历史数据
  const history = healthData?.sources ? Object.entries(healthData.sources).map(([sourceName, sourceData]) => ({
    id: sourceData.last_updated || 'unknown',
    timestamp: sourceData.last_updated ? new Date(sourceData.last_updated).toLocaleString('zh-CN') : '未知',
    source: sourceNames[sourceName] || sourceName,
    status: sourceData.status,
    records: sourceData.records_count || 0,
    qualityScore: sourceData.status === 'success' ? 95 : 0,
    size: '未知'
  })) : []

  const filteredHistory = history.filter(item => {
    const matchesSearch = item.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.id.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesSource = !selectedSource || item.source === selectedSource
    return matchesSearch && matchesSource
  })

  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage)
  const paginatedHistory = filteredHistory.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const sources = [...new Set(history.map(item => item.source))]

  const handleDownload = (id: string) => {
    // 模拟下载
    console.log(`Downloading ${id}`)
  }

  const handleCompare = () => {
    // 模拟对比功能
    console.log('Comparing versions')
  }

  const handleRefresh = () => {
    fetchData()
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">历史数据查询</h2>
        <p className="text-muted-foreground">
          浏览和查询历史数据版本，支持版本对比
        </p>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="搜索数据源或版本ID..."
            className="pl-8"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={selectedSource === null ? "default" : "outline"}
            onClick={() => setSelectedSource(null)}
          >
            全部
          </Button>
          {sources.map(source => (
            <Button
              key={source}
              variant={selectedSource === source ? "default" : "outline"}
              onClick={() => setSelectedSource(source)}
            >
              {source}
            </Button>
          ))}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <Button onClick={handleCompare}>
          <HistoryIcon className="mr-2 h-4 w-4" />
          版本对比
        </Button>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          批量下载
        </Button>
      </div>

      {/* 历史列表 */}
      <Card>
        <CardHeader>
          <CardTitle>历史版本</CardTitle>
          <CardDescription>
            共 {filteredHistory.length} 个版本
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {paginatedHistory.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className={`w-2 h-2 rounded-full ${
                    item.status === 'success' ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{item.source}</p>
                      <Badge variant="outline" className="font-mono">
                        {item.id}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {item.timestamp}
                      </span>
                      <span className="flex items-center gap-1">
                        <Database className="h-3 w-3" />
                        {item.records} 条记录
                      </span>
                      <span>{item.size}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm font-medium">质量评分</p>
                    <p className={`text-sm ${
                      item.qualityScore >= 90 ? 'text-green-500' : 
                      item.qualityScore >= 80 ? 'text-yellow-500' : 'text-red-500'
                    }`}>
                      {item.qualityScore}%
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(item.id)}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-muted-foreground">
                显示 {(currentPage - 1) * itemsPerPage + 1} 到{' '}
                {Math.min(currentPage * itemsPerPage, filteredHistory.length)} 条，
                共 {filteredHistory.length} 条
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 版本对比预览 */}
      <Card>
        <CardHeader>
          <CardTitle>版本对比</CardTitle>
          <CardDescription>
            选择两个版本进行数据对比
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium mb-2">版本 A</h4>
              <p className="text-sm text-muted-foreground">
                选择一个历史版本进行对比
              </p>
              <Button variant="outline" className="mt-2">
                选择版本
              </Button>
            </div>
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium mb-2">版本 B</h4>
              <p className="text-sm text-muted-foreground">
                选择另一个历史版本进行对比
              </p>
              <Button variant="outline" className="mt-2">
                选择版本
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}