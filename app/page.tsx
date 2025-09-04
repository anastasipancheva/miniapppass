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
  qrShown: boolean // Added flag to track if QR was shown
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
      qrShown: true, // Existing users already have QR shown
      qrCode: "",
    },
    {
      id: "2",
      name: "Мария Сидорова",
      keyExpiry: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000),
      status: "active",
      daysLeft: 10,
      accessLevel: "guest",
      totpSecret: "HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ",
      qrShown: true, // Existing users already have QR shown
      qrCode: "",
    },
    {
      id: "3",
      name: "Алексей Козлов",
      keyExpiry: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
      status: "expired",
      daysLeft: -1,
      accessLevel: "business_trip",
      totpSecret: "MFRGG2LTEBUW4IDPMYFA",
      qrShown: true, // Existing users already have QR shown
      qrCode: "",
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

  const [newUserQrCode, setNewUserQrCode] = useState<string>("") // Added state for new user QR code
  const [showNewUserQr, setShowNewUserQr] = useState(false) // Added state to control QR display
  const [newUserCreated, setNewUserCreated] = useState<User | null>(null) // Added state for newly created user

  const activeUsers = users.filter((u) => u.status === "active").length
  const expiringUsers = users.filter((u) => u.status === "expiring").length
  const expiredUsers = users.filter((u) => u.status === "expired").length

  const addUser = () => {
    if (!newUserName.trim()) return

    const totpSecret = generateTOTPSecret()
    const qrCode = generateQRCode(newUserName, totpSecret)

    const newUser: User = {
      id: Date.now().toString(),
      name: newUserName,
      keyExpiry: new Date(Date.now() + Number.parseInt(newUserDuration) * 24 * 60 * 60 * 1000),
      status: "active",
      daysLeft: Number.parseInt(newUserDuration),
      accessLevel: newUserAccessLevel,
      totpSecret,
      qrShown: false, // New users start with QR not shown
      qrCode,
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

    setNewUserCreated(newUser)
    setNewUserQrCode(qrCode)
    setShowNewUserQr(true)

    setNewUserName("")
    setNewUserDuration("7")
    setNewUserAccessLevel("guest")
    setIsAddUserOpen(false)
  }

  const handleQrConfirmed = () => {
    if (newUserCreated) {
      setUsers(users.map((user) => (user.id === newUserCreated.id ? { ...user, qrShown: true } : user)))
    }
    setShowNewUserQr(false)
    setNewUserQrCode("")
    setNewUserCreated(null)
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
    const qrSize = 200
    const cellSize = 4
    const gridSize = qrSize / cellSize

    let qrPattern = ""
    for (let y = 0; y < gridSize; y++) {
      for (let x = 0; x < gridSize; x++) {
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
    const qrCode = generateQRCode(users.find((u) => u.id === userId)?.name || "", newSecret)

    setUsers(
        users.map((user) =>
            user.id === userId
                ? {
                  ...user,
                  totpSecret: newSecret,
                  qrShown: false, // Reset QR shown flag when key is reset
                  qrCode,
                }
                : user,
        ),
    )

    const user = users.find((u) => u.id === userId)
    if (user) {
      setNotifications([
        {
          id: Date.now().toString(),
          type: "warning",
          message: `🔄 Ключ пользователя ${user.name} был сброшен. Требуется новая настройка аутентификатора!`,
          timestamp: new Date(),
        },
        ...notifications,
      ])

      setNewUserCreated({ ...user, totpSecret: newSecret, qrShown: false, qrCode })
      setNewUserQrCode(qrCode)
      setShowNewUserQr(true)
    }
  }

  const resetAllKeys = () => {
    const updatedUsers = users.map((user) => {
      const newSecret = generateTOTPSecret()
      return {
        ...user,
        totpSecret: newSecret,
        qrShown: false, // Reset QR shown flag for all users
        qrCode: generateQRCode(user.name, newSecret),
      }
    })

    setUsers(updatedUsers)
    setNotifications([
      {
        id: Date.now().toString(),
        type: "warning",
        message: `🔄 Эстренное обновление: все ключи (${users.length} шт.) были сброшены из соображений безопасности. Всем пользователям требуется новая настройка!`,
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

  useEffect(() => {
    setUsers((prevUsers) =>
        prevUsers.map((user) => ({
          ...user,
          qrCode: user.qrCode || generateQRCode(user.name, user.totpSecret),
        })),
    )
  }, [])

  return (
      <div className="min-h-screen bg-background">
        <header
            className={`${emergencyMode ? "bg-red-600" : "bg-primary"} text-primary-foreground shadow-lg transition-colors`}
        >
          <div className="px-4 py-6 max-w-7xl mx-auto">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-xl">
                  <Shield className="h-8 w-8" />
                </div>
                <div>
                  <h1 className="text-xl sm:text-2xl font-bold">Система Контроля Доступа</h1>
                  <p className="text-sm opacity-90 mt-1">
                    {emergencyMode ? "🚨 РЕЖИМ ТРЕВОГИ АКТИВЕН" : "Панель администратора"}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                <Dialog open={isMassResetOpen} onOpenChange={setIsMassResetOpen}>
                  <DialogTrigger asChild>
                    <Button variant="destructive" size="sm" className="flex items-center gap-2 text-xs">
                      <RotateCcw className="h-3 w-3" />
                      <span className="hidden sm:inline">Сбросить все ключи</span>
                      <span className="sm:hidden">Сброс</span>
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>⚠️ Экстренный сброс всех ключей</DialogTitle>
                      <DialogDescription>
                        Это действие сгенерирует новые TOTP-ключи для всех пользователей. Используйте только при
                        подозрении на компрометацию системы.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Alert className="border-red-200 bg-red-50">
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                        <AlertDescription className="text-red-800">
                          <strong>Внимание!</strong> После сброса всем пользователям потребуется заново настроить
                          приложения аутентификации.
                        </AlertDescription>
                      </Alert>
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
                    size="sm"
                    onClick={() => setEmergencyMode(!emergencyMode)}
                    className="flex items-center gap-2 text-xs"
                >
                  <AlertTriangle className="h-3 w-3" />
                  <span className="hidden sm:inline">{emergencyMode ? "Отключить тревогу" : "Режим тревоги"}</span>
                  <span className="sm:hidden">{emergencyMode ? "Откл" : "Тревога"}</span>
                </Button>
                <Badge variant="secondary" className="bg-secondary text-secondary-foreground text-xs">
                  Админ
                </Badge>
              </div>
            </div>
          </div>
        </header>

        <div className="px-4 py-6 max-w-7xl mx-auto space-y-6">
          {emergencyMode && (
              <Alert className="border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  <strong>🚨 РЕЖИМ ТРЕВОГИ АКТИВЕН</strong>
                  <br />• Все физические доступы заблокированы
                  <br />• Повышенное логирование всех действий
                  <br />• Уведомления службы безопасности отправлены
                </AlertDescription>
              </Alert>
          )}

          <Dialog open={showNewUserQr} onOpenChange={() => {}}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle className="text-center">🔐 Настройка аутентификатора</DialogTitle>
                <DialogDescription className="text-center">
                  Для пользователя: <strong>{newUserCreated?.name}</strong>
                </DialogDescription>
              </DialogHeader>

              <Alert className="border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800 text-sm">
                  <strong>⚠️ ВНИМАНИЕ!</strong> QR-код показывается только ОДИН раз из соображений безопасности. Сохраните
                  его сейчас или запишите секретный ключ.
                </AlertDescription>
              </Alert>

              <div className="flex justify-center p-4">
                <div className="text-center space-y-4">
                  <img
                      src={newUserQrCode || "/placeholder.svg"}
                      alt="QR Code for TOTP setup"
                      className="w-48 h-48 border rounded mx-auto"
                  />
                  <div className="text-sm text-muted-foreground space-y-2">
                    <p className="font-medium">Секретный ключ:</p>
                    <code className="bg-muted px-2 py-1 rounded text-xs break-all block">
                      {newUserCreated?.totpSecret}
                    </code>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(newUserCreated?.totpSecret || "")}
                        className="mt-2"
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      Скопировать ключ
                    </Button>
                  </div>
                </div>
              </div>

              <Alert className="border-blue-200 bg-blue-50">
                <AlertDescription className="text-blue-800 text-sm">
                  <strong>Инструкция:</strong>
                  <br />
                  1. Откройте Google Authenticator или Authy
                  <br />
                  2. Отсканируйте QR-код или введите ключ вручную
                  <br />
                  3. Проверьте, что код генерируется корректно
                </AlertDescription>
              </Alert>

              <DialogFooter>
                <Button onClick={handleQrConfirmed} className="w-full">
                  ✅ Настройка завершена
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <Card className="shadow-sm hover:shadow-md transition-shadow border-0 bg-gradient-to-br from-card to-card/50">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Активные</CardTitle>
                <div className="p-2 bg-green-100 rounded-lg">
                  <Users className="h-4 w-4 text-green-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{activeUsers}</div>
                <p className="text-xs text-muted-foreground">пользователей</p>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-md transition-shadow border-0 bg-gradient-to-br from-card to-card/50">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Истекающие</CardTitle>
                <div className="p-2 bg-amber-100 rounded-lg">
                  <Clock className="h-4 w-4 text-amber-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-amber-600">{expiringUsers}</div>
                <p className="text-xs text-muted-foreground">скоро</p>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-md transition-shadow border-0 bg-gradient-to-br from-card to-card/50">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Истёкшие</CardTitle>
                <div className="p-2 bg-red-100 rounded-lg">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{expiredUsers}</div>
                <p className="text-xs text-muted-foreground">обновить</p>
              </CardContent>
            </Card>

            <Card className="shadow-sm hover:shadow-md transition-shadow border-0 bg-gradient-to-br from-card to-card/50">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Уведомления</CardTitle>
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Bell className="h-4 w-4 text-blue-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{notifications.length}</div>
                <p className="text-xs text-muted-foreground">новых</p>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="users" className="space-y-6">
            <div className="sticky top-0 bg-background/95 backdrop-blur-sm z-10 pb-4">
              <TabsList className="grid w-full grid-cols-4 h-auto p-1 bg-card shadow-sm">
                <TabsTrigger
                    value="users"
                    className="flex flex-col items-center gap-2 py-3 px-2 text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all"
                >
                  <Users className="h-5 w-5" />
                  <span className="font-medium">Пользователи</span>
                </TabsTrigger>
                <TabsTrigger
                    value="keys"
                    className="flex flex-col items-center gap-2 py-3 px-2 text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all"
                >
                  <Key className="h-5 w-5" />
                  <span className="font-medium">Ключи</span>
                </TabsTrigger>
                <TabsTrigger
                    value="logs"
                    className="flex flex-col items-center gap-2 py-3 px-2 text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all"
                >
                  <History className="h-5 w-5" />
                  <span className="font-medium">Логи</span>
                </TabsTrigger>
                <TabsTrigger
                    value="notifications"
                    className="flex flex-col items-center gap-2 py-3 px-2 text-xs data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all"
                >
                  <Bell className="h-5 w-5" />
                  <span className="font-medium">Уведомления</span>
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="users" className="space-y-4">
              <Card className="shadow-sm border-0 bg-gradient-to-br from-card to-card/50">
                <CardHeader className="pb-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <CardTitle className="text-lg">Управление пользователями</CardTitle>
                      <CardDescription className="mt-1">Добавляйте и управляйте доступом пользователей</CardDescription>
                    </div>
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto">
                      <Select value={userFilter} onValueChange={(value: any) => setUserFilter(value)}>
                        <SelectTrigger className="w-full sm:w-40">
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
                          <Button className="flex items-center gap-2 w-full sm:w-auto">
                            <UserPlus className="h-4 w-4" />
                            <span className="sm:hidden">Добавить</span>
                            <span className="hidden sm:inline">Добавить пользователя</span>
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
                <CardContent className="pt-0">
                  <div className="space-y-3">
                    {filteredUsers.map((user) => (
                        <Card
                            key={user.id}
                            className="p-4 shadow-sm border-0 bg-background/50 hover:bg-background/80 transition-colors"
                        >
                          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <div className="flex items-start gap-4 flex-1">
                              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                                <Users className="h-6 w-6 text-primary" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                  <p className="font-semibold text-base">{user.name}</p>
                                  {getAccessLevelBadge(user.accessLevel)}
                                  {!user.qrShown && (
                                      <Badge className="bg-red-100 text-red-800 hover:bg-red-100">🔐 Требует настройки</Badge>
                                  )}
                                </div>
                                <p className="text-sm text-muted-foreground mb-3">
                                  Истекает: {user.keyExpiry.toLocaleDateString("ru-RU")}
                                </p>

                                <div className="space-y-2">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-xs text-muted-foreground">Секрет:</span>
                                    <code className="text-xs bg-muted px-2 py-1 rounded font-mono break-all">
                                      {visibleSecrets.has(user.id) ? user.totpSecret : "••••••••••••••••"}
                                    </code>
                                    <div className="flex gap-1">
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
                                  </div>
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-xs text-muted-foreground">Текущий код:</span>
                                    <code className="text-sm bg-green-100 text-green-800 px-3 py-1 rounded-lg font-mono font-bold">
                                      {currentCodes[user.id] || "------"}
                                    </code>
                                    <span className="text-xs text-muted-foreground">(обновляется каждые 30 сек)</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                              {getStatusBadge(user.status)}
                              <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => resetUserKey(user.id)}
                                  title="Сбросить ключ"
                              >
                                <RotateCcw className="h-4 w-4" />
                              </Button>
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
                        </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="keys" className="space-y-4">
              <Card className="shadow-sm border-0 bg-gradient-to-br from-card to-card/50">
                <CardHeader>
                  <CardTitle className="text-lg">Тест доступа</CardTitle>
                  <CardDescription>Проверьте TOTP-код для тестирования системы</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {emergencyMode ? (
                      <Alert className="border-red-200 bg-red-50">
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                        <AlertDescription className="text-red-800">
                          <strong>🚨 Тест-доступ заблокирован</strong> - система находится в режиме тревоги
                        </AlertDescription>
                      </Alert>
                  ) : (
                      <>
                        <div className="flex gap-2">
                          <Input
                              placeholder="Введите 6-значный код"
                              value={testCode}
                              onChange={(e) => setTestCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                              maxLength={6}
                              className="font-mono text-center text-lg"
                          />
                          <Button onClick={testAccess} disabled={testCode.length !== 6}>
                            Проверить
                          </Button>
                        </div>
                        {testResult && (
                            <Alert
                                className={testResult.success ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}
                            >
                              <AlertDescription className={testResult.success ? "text-green-800" : "text-red-800"}>
                                {testResult.message}
                              </AlertDescription>
                            </Alert>
                        )}
                      </>
                  )}
                </CardContent>
              </Card>

              <Card className="shadow-sm border-0 bg-gradient-to-br from-card to-card/50">
                <CardHeader>
                  <CardTitle className="text-lg">Активные TOTP-ключи</CardTitle>
                  <CardDescription>Текущие коды обновляются каждые 30 секунд</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {users.map((user) => (
                        <div
                            key={user.id}
                            className="flex items-center justify-between p-3 bg-background/50 rounded-lg border"
                        >
                          <div>
                            <p className="font-medium">{user.name}</p>
                            <p className="text-sm text-muted-foreground">{getAccessLevelText(user.accessLevel)}</p>
                          </div>
                          <div className="text-right">
                            <code className="text-lg font-mono font-bold bg-primary/10 px-3 py-1 rounded">
                              {currentCodes[user.id] || "------"}
                            </code>
                            <p className="text-xs text-muted-foreground mt-1">{getStatusBadge(user.status)}</p>
                          </div>
                        </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="logs" className="space-y-4">
              <Card className="shadow-sm border-0 bg-gradient-to-br from-card to-card/50">
                <CardHeader>
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <CardTitle className="text-lg">История доступа</CardTitle>
                      <CardDescription>Логи всех попыток входа в систему</CardDescription>
                    </div>
                    <Select value={logFilter} onValueChange={(value: any) => setLogFilter(value)}>
                      <SelectTrigger className="w-full sm:w-40">
                        <Filter className="h-4 w-4 mr-2" />
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все попытки</SelectItem>
                        <SelectItem value="success">Успешные</SelectItem>
                        <SelectItem value="failed">Неудачные</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {filteredLogs.map((log) => (
                        <div
                            key={log.id}
                            className={`flex items-center justify-between p-3 rounded-lg border ${
                                log.success ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
                            }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${log.success ? "bg-green-500" : "bg-red-500"}`} />
                            <div>
                              <p className="font-medium">{log.userName}</p>
                              <p className="text-sm text-muted-foreground">{log.timestamp.toLocaleString("ru-RU")}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <code className="text-sm bg-background px-2 py-1 rounded">{log.code}</code>
                            <p className={`text-xs mt-1 ${log.success ? "text-green-600" : "text-red-600"}`}>
                              {log.success ? "✅ Успешно" : "❌ Отклонено"}
                            </p>
                          </div>
                        </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="notifications" className="space-y-4">
              <Card className="shadow-sm border-0 bg-gradient-to-br from-card to-card/50">
                <CardHeader>
                  <CardTitle className="text-lg">Системные уведомления</CardTitle>
                  <CardDescription>Важные события и предупреждения системы</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {notifications.map((notification) => (
                        <div
                            key={notification.id}
                            className="flex items-start gap-3 p-4 bg-background/50 rounded-lg border"
                        >
                          {getNotificationIcon(notification.type)}
                          <div className="flex-1">
                            <p className="text-sm">{notification.message}</p>
                            <p className="text-xs text-muted-foreground mt-1">
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
