/**
 * API服务层
 * 封装与后端API的通信
 */

const API_BASE_URL = '/api'

export interface ApiResponse<T = any> {
  status: 'success' | 'error'
  timestamp?: string
  data?: T
  error?: string
  sources?: Record<string, any>
}

export interface HealthCheckResponse {
  status: 'success' | 'error'
  timestamp: string
  sources: Record<string, {
    status: string
    last_updated?: string
    records_count?: number
    error?: string
    message?: string
  }>
}

export interface SourceMetadata {
  name: string
  path: string
  has_data: boolean
  metadata?: {
    name: string
    description: string
    source: string
    update_frequency: string
    last_updated: string
    fields: string[]
    quality_score: number
    tags: string[]
  }
}

export interface SourcesResponse {
  status: 'success' | 'error'
  timestamp: string
  sources: SourceMetadata[]
}

export interface OilPriceData {
  status: string
  data: {
    update_time: string
    prices: Array<{
      region: string
      gasoline_92: number
      gasoline_95: number
      gasoline_98: number
      diesel_0: number
    }>
    source: string
    next_update: string
  }
}

export interface TrafficRestrictData {
  status: string
  data: {
    update_time: string
    restrictions: Array<{
      city: string
      rules: Array<{
        date: string
        restricted_numbers: string[]
        time_range: string
        area: string
        exceptions: string[]
      }>
    }>
    source: string
    next_update: string
  }
}

export interface PolicyData {
  status: string
  data: {
    update_time: string
    policies: Array<{
      id: string
      title: string
      publish_date: string
      effective_date: string
      source: string
      category: string
      summary: string
      url: string
      tags: string[]
    }>
    source: string
    next_update: string
  }
}

export interface AdminDivisionData {
  status: string
  data: {
    update_time: string
    divisions: Array<{
      code: string
      name: string
      level: string
      parent_code: string | null
      children: Array<{
        code: string
        name: string
        level: string
      }>
    }>
    source: string
    next_update: string
  }
}

export interface PriceTableData {
  status: string
  data: {
    update_time: string
    categories: Array<{
      name: string
      items: Array<{
        name: string
        price: number
        unit: string
        trend: string
        change_percent: number
      }>
    }>
    source: string
    next_update: string
  }
}

/**
 * 通用API请求函数
 */
async function fetchApi<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`)
  
  if (!response.ok) {
    throw new Error(`API请求失败: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  return data as T
}

/**
 * 健康检查
 */
export async function getHealthCheck(): Promise<HealthCheckResponse> {
  return fetchApi<HealthCheckResponse>('/health.json')
}

/**
 * 获取数据源元数据
 */
export async function getSourcesMetadata(): Promise<SourcesResponse> {
  return fetchApi<SourcesResponse>('/metadata/sources.json')
}

/**
 * 获取油价数据
 */
export async function getOilPriceData(): Promise<OilPriceData> {
  return fetchApi<OilPriceData>('/v1/oil-price/latest.json')
}

/**
 * 获取限行信息
 */
export async function getTrafficRestrictData(): Promise<TrafficRestrictData> {
  return fetchApi<TrafficRestrictData>('/v1/traffic-restrict/latest.json')
}

/**
 * 获取政策信息
 */
export async function getPolicyData(): Promise<PolicyData> {
  return fetchApi<PolicyData>('/v1/policy/latest.json')
}

/**
 * 获取行政区划数据
 */
export async function getAdminDivisionData(): Promise<AdminDivisionData> {
  return fetchApi<AdminDivisionData>('/v1/admin-division/latest.json')
}

/**
 * 获取价格表数据
 */
export async function getPriceTableData(): Promise<PriceTableData> {
  return fetchApi<PriceTableData>('/v1/price-table/latest.json')
}

/**
 * 获取指定数据源的历史数据
 */
export async function getSourceHistory(source: string, filename: string): Promise<any> {
  return fetchApi<any>(`/v1/${source}/${filename}`)
}

/**
 * 触发数据采集（开发测试用）
 */
export async function triggerCollection(): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE_URL}/collect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  
  if (!response.ok) {
    throw new Error(`触发采集失败: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * 触发油价数据采集
 */
export async function triggerOilPriceCollection(): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/oil-price/collect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  
  if (!response.ok) {
    throw new Error(`触发油价采集失败: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * 获取数据源信息（根据名称）
 */
export async function getSourceData(sourceName: string): Promise<any> {
  const endpointMap: Record<string, () => Promise<any>> = {
    'oil-price': getOilPriceData,
    'traffic-restrict': getTrafficRestrictData,
    'policy': getPolicyData,
    'admin-division': getAdminDivisionData,
    'price-table': getPriceTableData
  }
  
  const fetcher = endpointMap[sourceName]
  if (!fetcher) {
    throw new Error(`未知的数据源: ${sourceName}`)
  }
  
  return fetcher()
}

/**
 * 批量获取所有数据源的健康状态
 */
export async function getAllSourcesHealth(): Promise<Record<string, any>> {
  const health = await getHealthCheck()
  return health.sources || {}
}

/**
 * 获取系统状态摘要
 */
export async function getSystemStatus(): Promise<{
  totalSources: number
  healthySources: number
  warningSources: number
  errorSources: number
  lastUpdate: string | null
}> {
  const health = await getHealthCheck()
  const sources = health.sources || {}
  
  const sourceStatuses = Object.values(sources)
  const totalSources = sourceStatuses.length
  const healthySources = sourceStatuses.filter(s => s.status === 'success').length
  const warningSources = sourceStatuses.filter(s => s.status === 'warning').length
  const errorSources = sourceStatuses.filter(s => s.status === 'error').length
  
  // 获取最新的更新时间
  const lastUpdateTimes = sourceStatuses
    .filter(s => s.last_updated)
    .map(s => new Date(s.last_updated!).getTime())
  
  const lastUpdate = lastUpdateTimes.length > 0
    ? new Date(Math.max(...lastUpdateTimes)).toISOString()
    : null
  
  return {
    totalSources,
    healthySources,
    warningSources,
    errorSources,
    lastUpdate
  }
}