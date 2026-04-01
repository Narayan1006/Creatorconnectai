import { createContext, useContext, useState, type ReactNode } from 'react'

interface User {
  id: string
  email: string
  role: 'business' | 'creator'
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

function loadFromStorage(): { token: string | null; user: User | null } {
  try {
    const token = localStorage.getItem('cc_token')
    const userStr = localStorage.getItem('cc_user')
    const user = userStr ? JSON.parse(userStr) : null
    return { token, user }
  } catch {
    return { token: null, user: null }
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const saved = loadFromStorage()
  const [user, setUser] = useState<User | null>(saved.user)
  const [token, setToken] = useState<string | null>(saved.token)

  const login = (newToken: string, newUser: User) => {
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem('cc_token', newToken)
    localStorage.setItem('cc_user', JSON.stringify(newUser))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('cc_token')
    localStorage.removeItem('cc_user')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
