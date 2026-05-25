import { useState, useEffect } from 'react'
import { 
  Settings, 
  Save, 
  RefreshCw, 
  Plus, 
  Trash2, 
  Edit,
  Server,
  Clock,
  Globe,
  Shield,
  Bell,
  Database,
  Key,
  FileText
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
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

// 数据源采集频率映射
const sourceSchedules: Record<string, string> = {
  'oil-price': '0 9 * * *',
  'traffic-restrict': '0 8 * * 1',
  'policy': '0 10 * * *',
  'admin-division': '0 0 1 * *',
  'price-table': '0 12 * * *'
}

export default function AdminPage() {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('sources')

  const fetchData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getHealthCheck()
      setHealthData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取配置数据失败')
      console.error('获取配置数据失败:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSave = async () => {
    setIsSaving(true)
    // 模拟保存
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsSaving(false)
    setIsEditing(false)
  }

  const handleToggleSource = (sourceId: string) => {
    // 模拟切换状态
    console.log('Toggle source:', sourceId)
  }

  const handleDeleteSource = (sourceId: string) => {
    // 模拟删除
    console.log('Delete source:', sourceId)
  }

  // 转换配置数据
  const config = {
    sources: healthData?.sources ? Object.entries(healthData.sources).map(([sourceName, sourceData]) => ({
      id: sourceName,
      name: sourceNames[sourceName] || sourceName,
      url: `/api/v1/${sourceName}/latest.json`,
      schedule: sourceSchedules[sourceName] || '0 0 * * *',
      timeout: 30,
      retries: 3,
      enabled: sourceData.status !== 'error'
    })) : [],
    global: {
      quality_threshold: 0.8,
      max_history_days: 30,
      log_level: 'INFO',
      concurrent_collectors: 3
    }
  }

  const tabs = [
    { id: 'sources', label: '数据源配置', icon: Database },
    { id: 'global', label: '全局设置', icon: Settings },
    { id: 'notifications', label: '通知设置', icon: Bell },
    { id: 'security', label: '安全设置', icon: Shield }
  ]

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">管理后台</h2>
          <p className="text-muted-foreground">
            管理数据源配置、系统设置和通知规则
          </p>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                取消
              </Button>
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                保存配置
              </Button>
            </>
          ) : (
            <Button onClick={() => setIsEditing(true)}>
              <Edit className="mr-2 h-4 w-4" />
              编辑配置
            </Button>
          )}
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="flex gap-2 border-b">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "ghost"}
              onClick={() => setActiveTab(tab.id)}
              className="flex items-center gap-2"
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </Button>
          )
        })}
      </div>

      {/* 数据源配置 */}
      {activeTab === 'sources' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>数据源配置</CardTitle>
                <CardDescription>
                  管理数据源的采集URL、频率和重试策略
                </CardDescription>
              </div>
              {isEditing && (
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  添加数据源
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {config.sources.map((source) => (
                <div key={source.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${
                        source.enabled ? 'bg-green-500' : 'bg-gray-400'
                      }`} />
                      <div>
                        <h3 className="font-medium">{source.name}</h3>
                        <p className="text-sm text-muted-foreground">{source.id}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={source.enabled ? 'success' : 'secondary'}>
                        {source.enabled ? '启用' : '禁用'}
                      </Badge>
                      {isEditing && (
                        <div className="flex gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleSource(source.id)}
                          >
                            {source.enabled ? '禁用' : '启用'}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteSource(source.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">采集URL</p>
                      <p className="font-mono text-xs truncate">{source.url}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">采集频率</p>
                      <p className="font-mono">{source.schedule}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">超时时间</p>
                      <p>{source.timeout}秒</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">重试次数</p>
                      <p>{source.retries}次</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 全局设置 */}
      {activeTab === 'global' && (
        <Card>
          <CardHeader>
            <CardTitle>全局设置</CardTitle>
            <CardDescription>
              系统级别的配置参数
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">数据质量阈值</label>
                  <p className="text-sm text-muted-foreground">
                    低于此阈值的数据将不会被发布
                  </p>
                  <Input
                    type="number"
                    value={config.global.quality_threshold}
                    disabled={!isEditing}
                    min="0"
                    max="1"
                    step="0.1"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">历史数据保留天数</label>
                  <p className="text-sm text-muted-foreground">
                    超过此天数的历史数据将被清理
                  </p>
                  <Input
                    type="number"
                    value={config.global.max_history_days}
                    disabled={!isEditing}
                    min="1"
                    max="365"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">日志级别</label>
                  <p className="text-sm text-muted-foreground">
                    系统日志的详细程度
                  </p>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={config.global.log_level}
                    disabled={!isEditing}
                  >
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">并发采集数</label>
                  <p className="text-sm text-muted-foreground">
                    同时运行的采集器数量
                  </p>
                  <Input
                    type="number"
                    value={config.global.concurrent_collectors}
                    disabled={!isEditing}
                    min="1"
                    max="10"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 通知设置 */}
      {activeTab === 'notifications' && (
        <Card>
          <CardHeader>
            <CardTitle>通知设置</CardTitle>
            <CardDescription>
              配置采集失败时的通知方式
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4" />
                    <span className="font-medium">GitHub Issue</span>
                  </div>
                  <Badge variant="success">已启用</Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  采集失败时自动创建GitHub Issue
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    <span className="font-medium">邮件通知</span>
                  </div>
                  <Badge variant="secondary">未启用</Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  采集失败时发送邮件通知
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Key className="h-4 w-4" />
                    <span className="font-medium">Webhook</span>
                  </div>
                  <Badge variant="secondary">未启用</Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  采集失败时调用Webhook接口
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 安全设置 */}
      {activeTab === 'security' && (
        <Card>
          <CardHeader>
            <CardTitle>安全设置</CardTitle>
            <CardDescription>
              API访问控制和安全配置
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    <span className="font-medium">API密钥</span>
                  </div>
                  <Button variant="outline" size="sm">
                    生成新密钥
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  管理API访问密钥
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    <span className="font-medium">CORS设置</span>
                  </div>
                  <Badge variant="success">已启用</Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  配置跨域访问策略
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span className="font-medium">速率限制</span>
                  </div>
                  <Badge variant="success">已启用</Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  限制API请求频率，防止滥用
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 配置文件预览 */}
      <Card>
        <CardHeader>
          <CardTitle>配置文件预览</CardTitle>
          <CardDescription>
            当前配置的YAML格式预览
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="p-4 bg-muted rounded-lg overflow-x-auto text-sm">
            <code>{`# 数据源配置
sources:
${config.sources.map(source => `  ${source.id}:
    name: "${source.name}"
    url: "${source.url}"
    schedule: "${source.schedule}"
    timeout: ${source.timeout}
    retries: ${source.retries}
    enabled: ${source.enabled}`).join('\n')}

# 全局设置
settings:
  quality_threshold: ${config.global.quality_threshold}
  max_history_days: ${config.global.max_history_days}
  log_level: "${config.global.log_level}"
  concurrent_collectors: ${config.global.concurrent_collectors}`}</code>
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}