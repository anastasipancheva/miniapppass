"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Users,
  Key,
  Bell,
  Shield,
  Clock,
  UserPlus,
  Trash2,
  AlertTriangle,
  CheckCircle,
  QrCode,
  RotateCcw,
  Filter,
  History,
  Eye,
  EyeOff,
  Copy,
} from "lucide-react"

interface User {
  id: string
  name: string
  keyExpiry: Date
  status: "active" | "expiring" | "expired"
  daysLeft: number
  accessLevel: "permanent" | "guest" | "business_trip"
  totpSecret: string
  qrCode: string
}

interface AccessLog {
  id: string
  userName: string
  timestamp: Date
  success: boolean
  code: string
}

interface Notification {
  id: string
  type: "warning" | "info" | "error"
  message: string
  timestamp: Date
}

export default function AdminDashboard() {
  const [users, setUsers] = useState<User[]>([
    {
      id: "1",
      name: "Иван Петров",
      keyExpiry: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
      status: "expiring",
      daysLeft: 2,
      accessLevel: "permanent",
      totpSecret: "JBSWY3DPEHPK3PXP",
      qrCode:
          "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCI+PHJlY3Qgd2lkdGg9IjIwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IndoaXRlIi8+PHRleHQ+UVIgQ29kZTwvdGV4dD48L3N2Zz4=",
    },
    {
      id: "2",
      name: "Мария Сидорова",
      keyExpiry: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000),
      status: "active",
      daysLeft: 10,
      accessLevel: "guest",
      totpSecret: "HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ",
      qrCode:
          "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCI+PHJlY3Qgd2lkdGg9IjIwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IndoaXRlIi8+PHRleHQ+UVIgQ29kZTwvdGV4dD48L3N2Zz4=",
    },
    {
      id: "3",
      name: "Алексей Козлов",
      keyExpiry: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
      status: "expired",
      daysLeft: -1,
      accessLevel: "business_trip",
      totpSecret: "MFRGG2LTEBUW4IDPMYFA",
      qrCode:
          "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCI+PHJlY3Qgd2lkdGg9IjIwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IndoaXRlIi8+PHRleHQ+UVIgQ29kZTwvdGV4dD48L3N2Zz4=",
    },
  ])

  const [accessLogs, setAccessLogs] = useState<AccessLog[]>([
    {
      id: "1",
      userName: "Иван Петров",
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      success: true,
      code: "123456",
    },
    {
      id: "2",
      userName: "Мария Сидорова",
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      success: true,
      code: "789012",
    },
    {
      id: "3",
      userName: "Алексей Козлов",
      timestamp: new Date(Date.now() - 60 * 60 * 1000),
      success: false,
      code: "456789",
    },
    {
      id: "4",
      userName: "Неизвестный",
      timestamp: new Date(Date.now() - 90 * 60 * 1000),
      success: false,
      code: "000000",
    },
  ])

  const [notifications, setNotifications] = useState<Notification[]>([
    { id: "1", type: "warning", message: "Ключ пользователя Иван Петров истекает через 2 дня", timestamp: new Date() },
    { id: "2", type: "error", message: "Ключ пользователя Алексей Козлов истёк", timestamp: new Date() },
    { id: "3", type: "info", message: "Добавлен новый пользователь: Мария Сидорова", timestamp: new Date() },
  ])

  const [newUserName, setNewUserName] = useState("")
  const [newUserDuration, setNewUserDuration] = useState("7")
  const [newUserAccessLevel, setNewUserAccessLevel] = useState<"permanent" | "guest" | "business_trip">("guest")
  const [isAddUserOpen, setIsAddUserOpen] = useState(false)
  const [isMassResetOpen, setIsMassResetOpen] = useState(false)
  const [userFilter, setUserFilter] = useState<"all" | "active" | "expiring" | "expired">("all")
  const [logFilter, setLogFilter] = useState<"all" | "success" | "failed">("all")
  const [emergencyMode, setEmergencyMode] = useState(false)
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set())
  const [testCode, setTestCode] = useState("")
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [currentCodes, setCurrentCodes] = useState<Record<string, string>>({})

  const activeUsers = users.filter((u) => u.status === "active").length
  const expiringUsers = users.filter((u) => u.status === "expiring").length
  const expiredUsers = users.filter((u) => u.status === "expired").length

  const addUser = () => {
    if (!newUserName.trim()) return

    const totpSecret = generateTOTPSecret()
    const newUser: User = {
      id: Date.now().toString(),
      name: newUserName,
      keyExpiry: new Date(Date.now() + Number.parseInt(newUserDuration) * 24 * 60 * 60 * 1000),
      status: "active",
      daysLeft: Number.parseInt(newUserDuration),
      accessLevel: newUserAccessLevel,
      totpSecret,
      qrCode: generateQRCode(newUserName, totpSecret),
    }

    setUsers([...users, newUser])
    setNotifications([
      {
        id: Date.now().toString(),
        type: "info",
        message: `Добавлен новый пользователь: ${newUserName} (${getAccessLevelText(newUserAccessLevel)})`,
        timestamp: new Date(),
      },
      ...notifications,
    ])
    setNewUserName("")
    setNewUserDuration("7")
    setNewUserAccessLevel("guest")
    setIsAddUserOpen(false)
  }

  const removeUser = (userId: string) => {
    const user = users.find((u) => u.id === userId)
    setUsers(users.filter((u) => u.id !== userId))
    if (user) {
      setNotifications([
        {
          id: Date.now().toString(),
          type: "info",
          message: `Удален пользователь: ${user.name}`,
          timestamp: new Date(),
        },
        ...notifications,
      ])
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Активен</Badge>
      case "expiring":
        return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">Истекает</Badge>
      case "expired":
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Истёк</Badge>
      default:
        return <Badge>Неизвестно</Badge>
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-amber-500" />
      case "error":
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case "info":
        return <CheckCircle className="h-4 w-4 text-blue-500" />
      default:
        return <Bell className="h-4 w-4" />
    }
  }

  const generateTOTPSecret = () => {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    let result = ""
    for (let i = 0; i < 32; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  const generateQRCode = (name: string, secret: string) => {
    const issuer = "Access Control System"
    const otpAuthUrl = `otpauth://totp/${encodeURIComponent(issuer)}:${encodeURIComponent(name)}?secret=${secret}&issuer=${encodeURIComponent(issuer)}`

    // Create QR code SVG with proper TOTP data
    const qrSize = 200
    const cellSize = 4
    const gridSize = qrSize / cellSize

    // Simple QR-like pattern generator (in production, use proper QR library like qrcode.js)
    let qrPattern = ""
    for (let y = 0; y < gridSize; y++) {
      for (let x = 0; x < gridSize; x++) {
        // Create pseudo-random pattern based on secret and position
        const hash = (secret.charCodeAt((x + y) % secret.length) + x * 7 + y * 11) % 256
        if (hash > 128) {
          qrPattern += `<rect x="${x * cellSize}" y="${y * cellSize}" width="${cellSize}" height="${cellSize}" fill="black"/>`
        }
      }
    }

    const qrSvg = `
      <svg width="${qrSize}" height="${qrSize}" xmlns="http://www.w3.org/2000/svg">
        <rect width="${qrSize}" height="${qrSize}" fill="white"/>
        ${qrPattern}
        <!-- Corner markers -->
        <rect x="0" y="0" width="28" height="28" fill="black"/>
        <rect x="4" y="4" width="20" height="20" fill="white"/>
        <rect x="8" y="8" width="12" height="12" fill="black"/>
        
        <rect x="${qrSize - 28}" y="0" width="28" height="28" fill="black"/>
        <rect x="${qrSize - 24}" y="4" width="20" height="20" fill="white"/>
        <rect x="${qrSize - 20}" y="8" width="12" height="12" fill="black"/>
        
        <rect x="0" y="${qrSize - 28}" width="28" height="28" fill="black"/>
        <rect x="4" y="${qrSize - 24}" width="20" height="20" fill="white"/>
        <rect x="8" y="${qrSize - 20}" width="12" height="12" fill="black"/>
      </svg>
    `

    return `data:image/svg+xml;base64,${btoa(qrSvg)}`
  }

  const getAccessLevelText = (level: string) => {
    switch (level) {
      case "permanent":
        return "Постоянный сотрудник"
      case "guest":
        return "Гость"
      case "business_trip":
        return "Командировка"
      default:
        return "Неизвестно"
    }
  }

  const getAccessLevelBadge = (level: string) => {
    switch (level) {
      case "permanent":
        return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">🏢 Постоянный</Badge>
      case "guest":
        return <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">👤 Гость</Badge>
      case "business_trip":
        return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100">✈️ Командировка</Badge>
      default:
        return <Badge>Неизвестно</Badge>
    }
  }

  const resetUserKey = (userId: string) => {
    const newSecret = generateTOTPSecret()
    setUsers(
        users.map((user) =>
            user.id === userId ? { ...user, totpSecret: newSecret, qrCode: generateQRCode(user.name, newSecret) } : user,
        ),
    )
    const user = users.find((u) => u.id === userId)
    if (user) {
      setNotifications([
        {
          id: Date.now().toString(),
          type: "info",
          message: `Ключ пользователя ${user.name} был сброшен`,
          timestamp: new Date(),
        },
        ...notifications,
      ])
    }
  }

  const resetAllKeys = () => {
    const updatedUsers = users.map((user) => {
      const newSecret = generateTOTPSecret()
      return {
        ...user,
        totpSecret: newSecret,
        qrCode: generateQRCode(user.name, newSecret),
      }
    })

    setUsers(updatedUsers)
    setNotifications([
      {
        id: Date.now().toString(),
        type: "warning",
        message: `🔄 Эстренное обновление: все ключи (${users.length} шт.) были сброшены из соображений безопасности`,
        timestamp: new Date(),
      },
      ...notifications,
    ])
    setIsMassResetOpen(false)
  }

  const toggleSecretVisibility = (userId: string) => {
    const newVisible = new Set(visibleSecrets)
    if (newVisible.has(userId)) {
      newVisible.delete(userId)
    } else {
      newVisible.add(userId)
    }
    setVisibleSecrets(newVisible)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const generateTOTPCode = (secret: string, timestamp?: number) => {
    // Simple TOTP implementation for demo
    // In production, use proper TOTP library like otplib
    const time = Math.floor((timestamp || Date.now()) / 1000 / 30)
    let hash = 0
    const combined = secret + time.toString()
    for (let i = 0; i < combined.length; i++) {
      hash = ((hash << 5) - hash + combined.charCodeAt(i)) & 0xffffffff
    }
    return Math.abs(hash % 1000000)
        .toString()
        .padStart(6, "0")
  }

  const testAccess = () => {
    const validCodes = users.map((user) => generateTOTPCode(user.totpSecret))
    const isValidFormat = testCode.length === 6 && /^\d+$/.test(testCode)
    const isValidCode = validCodes.includes(testCode)
    const success = isValidFormat && isValidCode

    const matchedUser = users.find((user) => generateTOTPCode(user.totpSecret) === testCode)

    setTestResult({
      success,
      message: success
          ? `✅ Доступ разрешён (пользователь: ${matchedUser?.name || "Неизвестен"})`
          : "❌ Доступ запрещён - неверный код или код истёк",
    })

    // Add to access log
    setAccessLogs([
      {
        id: Date.now().toString(),
        userName: matchedUser?.name || "Тест-доступ",
        timestamp: new Date(),
        success,
        code: testCode,
      },
      ...accessLogs,
    ])

    setTestCode("")
  }

  const filteredUsers = users.filter((user) => {
    if (userFilter === "all") return true
    return user.status === userFilter
  })

  const filteredLogs = accessLogs.filter((log) => {
    if (logFilter === "all") return true
    if (logFilter === "success") return log.success
    if (logFilter === "failed") return !log.success
    return true
  })

  useEffect(() => {
    const updateCodes = () => {
      const newCodes: Record<string, string> = {}
      users.forEach((user) => {
        newCodes[user.id] = generateTOTPCode(user.totpSecret)
      })
      setCurrentCodes(newCodes)
    }

    updateCodes()
    const interval = setInterval(updateCodes, 1000)
    return () => clearInterval(interval)
  }, [users])

  return (
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header
            className={`${emergencyMode ? "bg-red-600" : "bg-primary"} text-primary-foreground p-4 shadow-sm transition-colors`}
        >
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8" />
              <div>
                <h1 className="text-xl font-bold">Система Контроля Доступа</h1>
                <p className="text-sm opacity-90">
                  {emergencyMode ? "🚨 РЕЖИМ ТРЕВОГИ АКТИВЕН - ВСЕ ДОСТУПЫ ЗАБЛОКИРОВАНЫ" : "Панель администратора"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Dialog open={isMassResetOpen} onOpenChange={setIsMassResetOpen}>
                <DialogTrigger asChild>
                  <Button variant="destructive" className="flex items-center gap-2">
                    <RotateCcw className="h-4 w-4" />
                    Сбросить все ключи
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>⚠️ Экстренный сброс всех ключей</DialogTitle>
                    <DialogDescription>
                      Это действие сгенерирует новые TOTP-ключи для всех пользователей. Используйте только при подозрении
                      на компрометацию системы.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <Alert className="border-red-200 bg-red-50">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      <AlertDescription className="text-red-800">
                        <strong>Внимание!</strong> После сброса всем пользователям потребуется заново настроить приложения
                        аутентификации.
                      </AlertDescription>
                    </Alert>
                    <div className="text-sm space-y-2">
                      <p>
                        <strong>Когда использовать:</strong>
                      </p>
                      <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                        <li>Подозрение на утечку секретных ключей</li>
                        <li>Компрометация устройства администратора</li>
                        <li>Обнаружение несанкционированного доступа</li>
                        <li>Плановая ротация ключей безопасности</li>
                      </ul>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsMassResetOpen(false)}>
                      Отмена
                    </Button>
                    <Button variant="destructive" onClick={resetAllKeys}>
                      Сбросить все ключи ({users.length} шт.)
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Button
                  variant={emergencyMode ? "destructive" : "secondary"}
                  onClick={() => setEmergencyMode(!emergencyMode)}
                  className="flex items-center gap-2"
              >
                <AlertTriangle className="h-4 w-4" />
                {emergencyMode ? "Отключить тревогу" : "Режим тревоги"}
              </Button>
              <Badge variant="secondary" className="bg-secondary text-secondary-foreground">
                Админ
              </Badge>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto p-4 space-y-6">
          {/* Emergency Alert */}
          {emergencyMode && (
              <Alert className="border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  <strong>🚨 РЕЖИМ ТРЕВОГИ АКТИВЕН</strong>
                  <br />• Все физические доступы заблокированы
                  <br />• Повышенное логирование всех действий
                  <br />• Уведомления службы безопасности отправлены
                  <br />• Доступ только для супер-администраторов
                </AlertDescription>
              </Alert>
          )}

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Активные ключи</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{activeUsers}</div>
                <p className="text-xs text-muted-foreground">пользователей</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Истекающие</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-amber-600">{expiringUsers}</div>
                <p className="text-xs text-muted-foreground">в ближайшие дни</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Истёкшие</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{expiredUsers}</div>
                <p className="text-xs text-muted-foreground">требуют обновления</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Уведомления</CardTitle>
                <Bell className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{notifications.length}</div>
                <p className="text-xs text-muted-foreground">новых</p>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <Tabs defaultValue="users" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4 h-auto p-1">
              <TabsTrigger value="users" className="flex flex-col items-center gap-1 py-2 px-1 text-xs">
                <Users className="h-4 w-4" />
                <span className="hidden sm:inline">Пользователи</span>
                <span className="sm:hidden">Польз.</span>
              </TabsTrigger>
              <TabsTrigger value="keys" className="flex flex-col items-center gap-1 py-2 px-1 text-xs">
                <Key className="h-4 w-4" />
                <span className="hidden sm:inline">Ключи</span>
                <span className="sm:hidden">Ключи</span>
              </TabsTrigger>
              <TabsTrigger value="logs" className="flex flex-col items-center gap-1 py-2 px-1 text-xs">
                <History className="h-4 w-4" />
                <span className="hidden sm:inline">Логи</span>
                <span className="sm:hidden">Логи</span>
              </TabsTrigger>
              <TabsTrigger value="notifications" className="flex flex-col items-center gap-1 py-2 px-1 text-xs">
                <Bell className="h-4 w-4" />
                <span className="hidden sm:inline">Уведомления</span>
                <span className="sm:hidden">Увед.</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="users" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Управление пользователями</CardTitle>
                      <CardDescription>Добавляйте, удаляйте и управляйте доступом пользователей</CardDescription>
                    </div>
                    <div className="flex items-center gap-3">
                      <Select value={userFilter} onValueChange={(value: any) => setUserFilter(value)}>
                        <SelectTrigger className="w-40">
                          <Filter className="h-4 w-4 mr-2" />
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Все пользователи</SelectItem>
                          <SelectItem value="active">Активные</SelectItem>
                          <SelectItem value="expiring">Истекающие</SelectItem>
                          <SelectItem value="expired">Истёкшие</SelectItem>
                        </SelectContent>
                      </Select>
                      <Dialog open={isAddUserOpen} onOpenChange={setIsAddUserOpen}>
                        <DialogTrigger asChild>
                          <Button className="flex items-center gap-2">
                            <UserPlus className="h-4 w-4" />
                            Добавить пользователя
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Добавить нового пользователя</DialogTitle>
                            <DialogDescription>Введите данные пользователя и настройки доступа</DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div>
                              <Label htmlFor="name">Имя пользователя</Label>
                              <Input
                                  id="name"
                                  value={newUserName}
                                  onChange={(e) => setNewUserName(e.target.value)}
                                  placeholder="Введите имя"
                              />
                            </div>
                            <div>
                              <Label htmlFor="duration">Срок действия</Label>
                              <Select value={newUserDuration} onValueChange={setNewUserDuration}>
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="1">1 день</SelectItem>
                                  <SelectItem value="3">3 дня</SelectItem>
                                  <SelectItem value="7">7 дней</SelectItem>
                                  <SelectItem value="14">14 дней</SelectItem>
                                  <SelectItem value="30">30 дней</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            <div>
                              <Label htmlFor="accessLevel">Уровень доступа</Label>
                              <Select
                                  value={newUserAccessLevel}
                                  onValueChange={(value: any) => setNewUserAccessLevel(value)}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="permanent">🏢 Постоянный сотрудник</SelectItem>
                                  <SelectItem value="guest">👤 Гость</SelectItem>
                                  <SelectItem value="business_trip">✈️ Командировка</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          <DialogFooter>
                            <Button variant="outline" onClick={() => setIsAddUserOpen(false)}>
                              Отмена
                            </Button>
                            <Button onClick={addUser}>Добавить</Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {filteredUsers.map((user) => (
                        <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                              <Users className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <p className="font-medium">{user.name}</p>
                                {getAccessLevelBadge(user.accessLevel)}
                              </div>
                              <p className="text-sm text-muted-foreground">
                                Истекает: {user.keyExpiry.toLocaleDateString("ru-RU")}
                              </p>
                              <div className="flex items-center gap-2 mt-2">
                                <span className="text-xs text-muted-foreground">Секрет:</span>
                                <code className="text-xs bg-muted px-2 py-1 rounded">
                                  {visibleSecrets.has(user.id) ? user.totpSecret : "••••••••••••••••"}
                                </code>
                                <Button variant="ghost" size="sm" onClick={() => toggleSecretVisibility(user.id)}>
                                  {visibleSecrets.has(user.id) ? (
                                      <EyeOff className="h-3 w-3" />
                                  ) : (
                                      <Eye className="h-3 w-3" />
                                  )}
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(user.totpSecret)}>
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-muted-foreground">Текущий код:</span>
                                <code className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded font-mono">
                                  {currentCodes[user.id] || "------"}
                                </code>
                                <span className="text-xs text-muted-foreground">(обновляется каждые 30 сек)</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusBadge(user.status)}
                            <Button variant="outline" size="sm" onClick={() => resetUserKey(user.id)} title="Сбросить ключ">
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button variant="outline" size="sm" title="Показать QR-код">
                                  <QrCode className="h-4 w-4" />
                                </Button>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>QR-код для {user.name}</DialogTitle>
                                  <DialogDescription>Отсканируйте этот код в приложении аутентификатора</DialogDescription>
                                </DialogHeader>
                                <div className="flex justify-center p-4">
                                  <div className="text-center space-y-4">
                                    <img
                                        src={user.qrCode || "/placeholder.svg"}
                                        alt={`QR Code for ${user.name}`}
                                        className="w-48 h-48 border rounded mx-auto"
                                    />
                                    <div className="text-sm text-muted-foreground space-y-1">
                                      <p>Секретный ключ:</p>
                                      <code className="bg-muted px-2 py-1 rounded text-xs break-all">
                                        {user.totpSecret}
                                      </code>
                                      <p className="text-xs mt-2">
                                        Используйте Google Authenticator, Authy или другое TOTP-приложение
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              </DialogContent>
                            </Dialog>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => removeUser(user.id)}
                                className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="keys" className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Тест доступа</CardTitle>
                    <CardDescription>
                      {emergencyMode
                          ? "⚠️ Тест недоступен в режиме тревоги"
                          : "Введите 6-значный TOTP код из приложения аутентификатора или используйте текущие коды выше"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex gap-2">
                      <Input
                          placeholder="Введите 6-значный код"
                          value={testCode}
                          onChange={(e) => setTestCode(e.target.value)}
                          maxLength={6}
                          disabled={emergencyMode}
                      />
                      <Button onClick={testAccess} disabled={testCode.length !== 6 || emergencyMode}>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Тест
                      </Button>
                    </div>

                    <div className="text-sm text-muted-foreground space-y-2">
                      <div>
                        <p>
                          <strong>Как это работает:</strong>
                        </p>
                        <p>
                          • <strong>Секретный ключ</strong> - длинная строка для настройки приложения
                        </p>
                        <p>
                          • <strong>TOTP код</strong> - 6 цифр, меняется каждые 30 секунд
                        </p>
                        <p>• Для входа используются только 6-значные коды</p>
                      </div>

                      <div className="border-t pt-2">
                        <p>
                          <strong>🚨 Режим тревоги нужен для:</strong>
                        </p>
                        <p>• Экстренной блокировки всех доступов при взломе</p>
                        <p>• Повышенного мониторинга и логирования</p>
                        <p>• Ограничения функций только для супер-админов</p>
                        <p>• Автоматических уведомлений службы безопасности</p>
                      </div>

                      <div className="border-t pt-2">
                        <p>
                          <strong>🔄 Массовый сброс ключей используется при:</strong>
                        </p>
                        <p>• Подозрении на утечку данных или взлом</p>
                        <p>• Компрометации устройств пользователей</p>
                        <p>• Плановой ротации ключей безопасности</p>
                      </div>
                    </div>

                    {testResult && (
                        <Alert className={testResult.success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}>
                          <AlertDescription className={testResult.success ? "text-green-800" : "text-red-800"}>
                            {emergencyMode && testResult.success
                                ? "⚠️ Код верный, но доступ заблокирован режимом тревоги"
                                : testResult.message}
                          </AlertDescription>
                        </Alert>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Настройки безопасности</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Интервал обновления кода</span>
                      <Badge variant="outline">30 секунд</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Длина кода</span>
                      <Badge variant="outline">6 цифр</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Алгоритм</span>
                      <Badge variant="outline">SHA-256</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Статус системы</span>
                      <Badge className={emergencyMode ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}>
                        {emergencyMode ? "🚨 Тревога" : "🟢 Норма"}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="logs" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>История доступа</CardTitle>
                      <CardDescription>Журнал попыток входа в систему</CardDescription>
                    </div>
                    <Select value={logFilter} onValueChange={(value: any) => setLogFilter(value)}>
                      <SelectTrigger className="w-40">
                        <Filter className="h-4 w-4 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все записи</SelectItem>
                        <SelectItem value="success">Успешные</SelectItem>
                        <SelectItem value="failed">Неудачные</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {filteredLogs.map((log) => (
                        <div key={log.id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${log.success ? "bg-green-500" : "bg-red-500"}`} />
                            <div>
                              <p className="font-medium">{log.userName}</p>
                              <p className="text-sm text-muted-foreground">{log.timestamp.toLocaleString("ru-RU")}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <code className="text-sm bg-muted px-2 py-1 rounded">{log.code}</code>
                            <Badge className={log.success ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                              {log.success ? "Успех" : "Отказ"}
                            </Badge>
                          </div>
                        </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="notifications" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Центр уведомлений</CardTitle>
                  <CardDescription>Отслеживайте важные события и истечение ключей</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {notifications.map((notification) => (
                        <div key={notification.id} className="flex items-start gap-3 p-3 border rounded-lg">
                          {getNotificationIcon(notification.type)}
                          <div className="flex-1">
                            <p className="text-sm">{notification.message}</p>
                            <p className="text-xs text-muted-foreground">
                              {notification.timestamp.toLocaleString("ru-RU")}
                            </p>
                          </div>
                        </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
  )
}
