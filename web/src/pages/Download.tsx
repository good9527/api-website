import { useState, useEffect } from 'react'
import { 
  Download as DownloadIcon, 
  FileJson, 
  FileText, 
  Archive,
  Search,
  Filter,
  Calendar,
  Clock,
  Database,
  HardDrive
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { getHealthCheck, HealthCheckResponse } from '@/services/api'

// 数据源描述映射
const sourceDescriptions: Record<string, string> = {
  'oil-price': '国内成品油价格数据',
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

export default function DownloadPage() {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFormat, setSelectedFormat] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getHealthCheck()
      setHealthData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取数据源信息失败')
      console.error('获取数据源信息失败:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // 转换数据源信息
  const dataSources = healthData?.sources ? Object.entries(healthData.sources).map(([sourceName, sourceData]) => ({
    id: sourceName,
    name: sourceNames[sourceName] || sourceName,
    description: sourceDescriptions[sourceName] || '数据源',
    lastUpdate: sourceData.last_updated ? new Date(sourceData.last_updated).toLocaleString('zh-CN') : '未知',
    records: sourceData.records_count || 0,
    size: '未知', // API没有返回文件大小
    format: 'JSON',
    status: sourceData.status
  })) : []

  const filteredSources = dataSources.filter(source => {
    const matchesSearch = source.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         source.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFormat = !selectedFormat || source.format === selectedFormat
    return matchesSearch && matchesFormat
  })

  const handleDownload = (sourceId: string, format: string) => {
    // 实际下载
    const url = `/api/v1/${sourceId}/latest.json`
    window.open(url, '_blank')
  }

  const handleBatchDownload = () => {
    // 批量下载
    dataSources.forEach(source => {
      if (source.status === 'success') {
        handleDownload(source.id, 'JSON')
      }
    })
  }

  const formats = ['JSON', 'CSV', 'XML']

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">数据下载中心</h2>
        <p className="text-muted-foreground">
          下载各类数据源的最新或历史数据
        </p>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="搜索数据源..."
            className="pl-8"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={selectedFormat === null ? "default" : "outline"}
            onClick={() => setSelectedFormat(null)}
          >
            全部格式
          </Button>
          {formats.map(format => (
            <Button
              key={format}
              variant={selectedFormat === format ? "default" : "outline"}
              onClick={() => setSelectedFormat(format)}
            >
              {format}
            </Button>
          ))}
        </div>
      </div>

      {/* 批量操作 */}
      <div className="flex gap-2">
        <Button onClick={handleBatchDownload}>
          <Archive className="mr-2 h-4 w-4" />
          批量下载 (ZIP)
        </Button>
        <Button variant="outline">
          <DownloadIcon className="mr-2 h-4 w-4" />
          下载全部数据
        </Button>
      </div>

      {/* 数据源卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredSources.map((source) => (
          <Card key={source.id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{source.name}</CardTitle>
                <Badge variant={source.status === 'success' ? 'success' : 
                               source.status === 'warning' ? 'warning' : 'destructive'}>
                  {source.status === 'success' ? '正常' : 
                   source.status === 'warning' ? '警告' : '异常'}
                </Badge>
              </div>
              <CardDescription>{source.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">最后更新</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {source.lastUpdate}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">记录数量</span>
                  <span className="flex items-center gap-1">
                    <Database className="h-3 w-3" />
                    {source.records} 条
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">文件大小</span>
                  <span className="flex items-center gap-1">
                    <HardDrive className="h-3 w-3" />
                    {source.size}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">数据格式</span>
                  <Badge variant="outline">{source.format}</Badge>
                </div>
              </div>

              <Separator className="my-4" />

              <div className="space-y-2">
                <p className="text-sm font-medium">下载选项</p>
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(source.id, 'JSON')}
                    disabled={source.status === 'error'}
                  >
                    <FileJson className="mr-1 h-3 w-3" />
                    JSON
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(source.id, 'CSV')}
                    disabled={source.status === 'error'}
                  >
                    <FileText className="mr-1 h-3 w-3" />
                    CSV
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(source.id, 'XML')}
                    disabled={source.status === 'error'}
                  >
                    <FileText className="mr-1 h-3 w-3" />
                    XML
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 下载说明 */}
      <Card>
        <CardHeader>
          <CardTitle>下载说明</CardTitle>
          <CardDescription>
            关于数据下载的详细说明
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">数据格式</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• <strong>JSON</strong> - 标准JSON格式，包含完整元数据</li>
                <li>• <strong>CSV</strong> - 逗号分隔值，适合Excel等工具</li>
                <li>• <strong>XML</strong> - 可扩展标记语言，适合系统集成</li>
              </ul>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">数据更新</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• 数据按预定计划自动更新</li>
                <li>• 更新频率因数据源而异（每日/每周/每月）</li>
                <li>• 可在"状态监控"页面查看更新计划</li>
              </ul>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">使用条款</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• 数据仅供学习和研究使用</li>
                <li>• 商业用途请联系数据提供方</li>
                <li>• 下载数据需遵守相关法律法规</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}