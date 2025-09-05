"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  AlertTriangle,
  Users,
  Key,
  Bell,
  Trash2,
  RotateCcw,
  Shield,
  Copy,
  CheckCircle,
  Clock,
  Plus,
} from "lucide-react"
import { Filter } from "lucide-react"

const generateQRCodeDataURL = async (text: string): Promise<string> => {
  // Import qrcode dynamically for client-side usage
  const QRCode = (await import("qrcode")).default

  try {
    const qrCodeDataURL = await QRCode.toDataURL(text, {
      width: 200,
      margin: 2,
      color: {
        dark: "#000000",
        light: "#FFFFFF",
      },
    })
    return qrCodeDataURL
  } catch (error) {
    console.error("Error generating QR code:", error)
    // Fallback to a simple placeholder
    return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y5ZjlmOSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjE0cHgiIGZpbGw9IiM5OTk5OTkiPkVycm9yPC90ZXh0Pjwvc3ZnPg=="
  }
}

interface User {
  id: string
  name: string
  accessLevel: "permanent" | "guest" | "business_trip"
  expiresAt: Date
  totpSecret: string
  qrShown: boolean
  isActive: boolean
}

interface AccessLog {
  id: string
  userId: string
  userName: string
  timestamp: Date
  success: boolean
  code: string
}

interface Notification {
  id: string
  type: "info" | "warning" | "error" | "success"
  message: string
  timestamp: Date
}

const generateTOTPSecret = () => {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
  let result = ""
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

const removeUser = (userId: string) => {
  // Placeholder for removeUser function
}

export default function AccessControlAdmin() {
  const [users, setUsers] = useState<User[]>([
    {
      id: "1",
      name: "Мария Сидорова",
      accessLevel: "permanent",
      expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000),
      totpSecret: "",
      qrShown: true, // Already shown
      isActive: true,
    },
    {
      id: "2",
      name: "Алексей Петров",
      accessLevel: "guest",
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      totpSecret: "",
      qrShown: true, // Already shown
      isActive: true,
    },
    {
      id: "3",
      name: "Елена Козлова",
      accessLevel: "business_trip",
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      totpSecret: "",
      qrShown: true, // Already shown
      isActive: false,
    },
  ])

  const [accessLogs, setAccessLogs] = useState<AccessLog[]>([
    {
      id: "1",
      userId: "1",
      userName: "Иван Петров",
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      success: true,
      code: "123456",
    },
    {
      id: "2",
      userId: "2",
      userName: "Мария Сидорова",
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      success: true,
      code: "789012",
    },
    {
      id: "3",
      userId: "3",
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
  const [newUserDuration, setNewUserDuration] = useState("7") // (пока не используется)
  const [newUserAccessLevel, setNewUserAccessLevel] = useState<string>("")
  const [isAddUserOpen, setShowAddUserDialog] = useState(false)
  const [isMassResetOpen, setShowMassResetDialog] = useState(false)
  const [userFilter, setUserFilter] = useState<"all" | "active" | "expiring" | "expired">("all")
  const [logFilter, setLogFilter] = useState<"all" | "success" | "failed">("all")
  const [emergencyMode, setAlarmMode] = useState(false)
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set())

  const [newUserQrCode, setNewUserQrCode] = useState<string>("")
  const [showNewUserQr, setShowNewUserQr] = useState(false)
  const [newUserCreated, setNewUserCreated] = useState<User | null>(null)
  const [activeTab, setActiveTab] = useState<"users" | "keys" | "logs" | "notifications">("users")

  const activeUsers = users.filter((u) => u.isActive).length
  const expiringUsers = users.filter(
      (u) => u.expiresAt.getTime() > Date.now() && u.expiresAt.getTime() < Date.now() + 30 * 24 * 60 * 60 * 1000,
  ).length
  const inactiveUsers = users.filter((u) => !u.isActive).length

  const generateQRCode = async (name: string, secret: string) => {
    const issuer = "Access Control System"
    const otpauthUrl = `otpauth://totp/${encodeURIComponent(issuer)}:${encodeURIComponent(name)}?secret=${secret}&issuer=${encodeURIComponent(issuer)}`
    return await generateQRCodeDataURL(otpauthUrl)
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

  const getStatusBadge = (user: User) => {
    if (!user.isActive) {
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Не активен</Badge>
    }
    if (user.expiresAt.getTime() < Date.now()) {
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Истёк</Badge>
    }
    if (user.expiresAt.getTime() < Date.now() + 30 * 24 * 60 * 60 * 1000) {
      return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">Истекает</Badge>
    }
    return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Активен</Badge>
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

  const resetUserKey = async (userId: string) => {
    const newSecret = generateTOTPSecret()
    const user = users.find((u) => u.id === userId)

    if (user) {
      const qrCode = await generateQRCode(user.name, newSecret)

      setUsers(
          users.map((u) =>
              u.id === userId
                  ? {
                    ...u,
                    totpSecret: newSecret,
                    qrShown: false, // Reset QR shown flag when key is reset
                  }
                  : u,
          ),
      )

      setNotifications([
        {
          id: Date.now().toString(),
          type: "warning",
          message: `🔄 Ключ пользователя ${user.name} был сброшен. Требуется новая настройка аутентификатора!`,
          timestamp: new Date(),
        },
        ...notifications,
      ])

      setNewUserCreated({ ...user, totpSecret: newSecret, qrShown: false })
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
    setShowMassResetDialog(false)
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

  const addUser = async () => {
    if (newUserName && newUserAccessLevel) {
      const expirationDays = newUserAccessLevel === "permanent" ? 365 : newUserAccessLevel === "guest" ? 7 : 30
      const newSecret = generateTOTPSecret()
      const qrCode = await generateQRCode(newUserName, newSecret)

      const user: User = {
        id: Date.now().toString(),
        name: newUserName,
        accessLevel: newUserAccessLevel as "permanent" | "guest" | "business_trip",
        expiresAt: new Date(Date.now() + expirationDays * 24 * 60 * 60 * 1000),
        totpSecret: newSecret,
        qrShown: false, // QR not shown yet
        isActive: true,
      }

      try {
        const response = await fetch("https://iag9aq-5-77-6-147.ru.tuna.am/api/users", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: newUserName,
            accessLevel: newUserAccessLevel,
            expiresAt: user.expiresAt.toISOString(),
            totpSecret: newSecret,
            isActive: true,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const controllerResult = await response.json()
        console.log("[v0] User created in controller:", controllerResult)

        // Update local state only if controller creation was successful
        setUsers([...users, user])
        setNotifications([
          {
            id: Date.now().toString(),
            type: "success",
            message: `✅ Пользователь ${newUserName} добавлен локально и в контроллере с уровнем доступа "${getAccessLevelText(newUserAccessLevel as any)}"`,
            timestamp: new Date(),
          },
          ...notifications,
        ])
      } catch (error) {
        console.error("[v0] Error creating user in controller:", error)

        // Still add user locally but show warning
        setUsers([...users, user])
        setNotifications([
          {
            id: Date.now().toString(),
            type: "warning",
            message: `⚠️ Пользователь ${newUserName} добавлен локально, но не удалось синхронизировать с контроллером. Проверьте подключение.`,
            timestamp: new Date(),
          },
          ...notifications,
        ])
      }

      setNewUserCreated(user)
      setNewUserQrCode(qrCode)
      setShowNewUserQr(true)

      setNewUserName("")
      setNewUserAccessLevel("")
      setShowAddUserDialog(false)
    }
  }

  useEffect(() => {
    setUsers((prevUsers) =>
        prevUsers.map((user) => ({
          ...user,
          totpSecret: user.totpSecret || generateTOTPSecret(),
        })),
    )
  }, [])

  const filteredUsers = users.filter((user) => {
    if (userFilter === "all") return true
    // return user.status === userFilter
    return true
  })

  const filteredLogs = accessLogs.filter((log) => {
    if (logFilter === "all") return true
    if (logFilter === "success") return log.success
    if (logFilter === "failed") return !log.success
    return true
  })

  return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
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
                <Dialog open={isAddUserOpen} onOpenChange={setShowAddUserDialog}>
                  <DialogTrigger asChild>
                    <Button variant="secondary" size="sm" className="flex items-center gap-2 text-xs">
                      <Plus className="h-3 w-3" />
                      <span className="hidden sm:inline">Добавить пользователя</span>
                      <span className="sm:hidden">Добавить</span>
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Добавить нового пользователя</DialogTitle>
                      <DialogDescription>Создание нового пользователя с TOTP-ключом для доступа</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="user-name">Имя пользователя</Label>
                        <Input
                            id="user-name"
                            value={newUserName}
                            onChange={(e) => setNewUserName(e.target.value)}
                            placeholder="Введите имя"
                        />
                      </div>
                      <div>
                        <Label htmlFor="access-level">Уровень доступа</Label>
                        <Select value={newUserAccessLevel} onValueChange={setNewUserAccessLevel}>
                          <SelectTrigger>
                            <SelectValue placeholder="Выберите уровень доступа" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="permanent">🏢 Постоянный сотрудник (1 год)</SelectItem>
                            <SelectItem value="guest">👤 Гость (7 дней)</SelectItem>
                            <SelectItem value="business_trip">✈️ Командировка (30 дней)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" onClick={() => setShowAddUserDialog(false)}>
                          Отмена
                        </Button>
                        <Button onClick={addUser} className="bg-orange-600 hover:bg-orange-700">
                          Создать пользователя
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>

                <Dialog open={isMassResetOpen} onOpenChange={setShowMassResetDialog}>
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
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-red-700">
                          <AlertTriangle className="h-4 w-4" />
                          <span className="font-medium">Внимание!</span>
                        </div>
                        <p className="text-red-800 text-sm mt-1">
                          После сброса всем пользователям потребуется заново настроить приложения аутентификации.
                        </p>
                      </div>
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" onClick={() => setShowMassResetDialog(false)}>
                          Отмена
                        </Button>
                        <Button variant="destructive" onClick={resetAllKeys}>
                          Сбросить все ключи ({users.length} шт.)
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>

                <Button
                    variant={emergencyMode ? "destructive" : "secondary"}
                    size="sm"
                    onClick={() => setAlarmMode(!emergencyMode)}
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
              <div className="border-red-200 bg-red-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-red-700">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="font-medium">🚨 РЕЖИМ ТРЕВОГИ АКТИВЕН</span>
                </div>
                <ul className="mt-4 list-disc list-inside space-y-2 text-sm text-red-800">
                  <li>Все физические доступы заблокированы</li>
                  <li>Повышенное логирование всех действий</li>
                  <li>Уведомления службы безопасности отправлены</li>
                </ul>
              </div>
          )}

          {/* QR Code Display Dialog */}
          <Dialog open={showNewUserQr} onOpenChange={setShowNewUserQr}>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5 text-orange-600" />
                  QR-код для {newUserCreated?.name}
                </DialogTitle>
                <DialogDescription>
                  <div className="space-y-2 text-sm">
                    <p className="text-red-600 font-medium">⚠️ ВНИМАНИЕ: Этот QR-код показывается только ОДИН раз!</p>
                    <p>Отсканируйте код в приложении аутентификатора (Google Authenticator, Authy и т.д.)</p>
                  </div>
                </DialogDescription>
              </DialogHeader>

              <div className="flex justify-center p-4">
                <div className="text-center space-y-4">
                  <img
                      src={newUserQrCode || "/placeholder.svg"}
                      alt="QR Code for TOTP setup"
                      className="w-48 h-48 border rounded mx-auto bg-white"
                  />
                  <div className="text-sm text-muted-foreground space-y-2">
                    <p className="font-medium">Секретный ключ (для ручного ввода):</p>
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
                  <div className="text-xs text-muted-foreground bg-yellow-50 p-3 rounded border">
                    <p className="font-medium mb-1">Инструкция:</p>
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Откройте приложение аутентификатора</li>
                      <li>Нажмите "Добавить аккаунт" или "+"</li>
                      <li>Отсканируйте QR-код или введите ключ вручную</li>
                      <li>Сохраните настройки</li>
                    </ol>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button
                    onClick={() => {
                      if (newUserCreated) {
                        setUsers(users.map((u) => (u.id === newUserCreated.id ? { ...u, qrShown: true } : u)))
                      }
                      setShowNewUserQr(false)
                      setNewUserCreated(null)
                      setNewUserQrCode("")
                    }}
                    className="bg-orange-600 hover:bg-orange-700"
                >
                  Готово, код настроен
                </Button>
              </div>
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
                <CardTitle className="text-sm font-medium">Неактивные</CardTitle>
                <div className="p-2 bg-red-100 rounded-lg">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{inactiveUsers}</div>
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

          <div className="grid gap-4">
            {users.map((user) => (
                <Card key={user.id} className="bg-white/80 backdrop-blur border-orange-200">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{user.name}</h3>
                          {getAccessLevelBadge(user.accessLevel)}
                          {getStatusBadge(user)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          <p>Ключ настроен: {user.qrShown ? "✅ Да" : "❌ Требуется настройка"}</p>
                          <p>Истекает: {user.expiresAt.toLocaleDateString("ru-RU")}</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => resetUserKey(user.id)}
                            className="text-orange-600 border-orange-200 hover:bg-orange-50"
                        >
                          <RotateCcw className="h-3 w-3 mr-1" />
                          Сбросить ключ
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
                  </CardContent>
                </Card>
            ))}
          </div>

          {/* Logs Section */}
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

          {/* Notifications Section */}
          <Card className="shadow-sm border-0 bg-gradient-to-br from-card to-card/50">
            <CardHeader>
              <CardTitle className="text-lg">Системные уведомления</CardTitle>
              <CardDescription>Важные события и предупреждения системы</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {notifications.map((notification) => (
                    <div key={notification.id} className="flex items-start gap-3 p-4 bg-background/50 rounded-lg border">
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
        </div>
      </div>
  )
}
