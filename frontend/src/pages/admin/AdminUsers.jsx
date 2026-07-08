import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteAdminUser, getAdminUsers } from '../../api/adminClient'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { Input } from '../../components/ui/Input'
import { AdminCard } from '../../components/admin/AdminLayout'
import { AdminEmpty, AdminError } from '../../components/admin/AdminPageState'

export default function AdminUsers() {
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('username')
  const [sortDir, setSortDir] = useState('asc')
  const [page, setPage] = useState(0)
  const pageSize = 10

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getAdminUsers({ search: search || undefined, limit: 500 })
      setUsers(data.items || [])
      setTotal(data.total ?? (data.items || []).length)
    } catch (err) {
      setUsers([])
      setError(err.response?.data?.detail?.message || err.response?.data?.detail || 'Failed to load users.')
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => { load() }, [load])

  const filtered = useMemo(() => {
    let rows = [...users]
    rows.sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })
    return rows
  }, [users, sortKey, sortDir])

  const pageRows = filtered.slice(page * pageSize, (page + 1) * pageSize)
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('asc') }
  }

  const handleDelete = async (user) => {
    if (!window.confirm(`Delete user "${user.username}"?`)) return
    await deleteAdminUser(user.id)
    await load()
  }

  if (loading && !users.length) return <LoadingSpinner label="Loading users..." />
  if (error && !users.length) return <AdminError message={error} onRetry={load} />

  return (
    <div className="space-y-4">
      <AdminCard title="User Management" subtitle={`${total} registered users`}>
        <div className="mb-4 flex flex-wrap gap-3">
          <Input placeholder="Search users..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(0) }} className="max-w-xs bg-zinc-900 border-zinc-700 text-white" />
          <Button variant="secondary" onClick={load}>Search</Button>
        </div>
        {!filtered.length ? (
          <AdminEmpty message="No users found." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="admin-table w-full text-sm text-zinc-300">
                <thead>
                  <tr>
                    {[
                      ['username', 'Username'], ['email', 'Email'], ['role', 'Role'],
                      ['created_at', 'Created'], ['servers', 'Servers'], ['events', 'Events'],
                      ['status', 'Status'],
                    ].map(([key, label]) => (
                      <th key={key} className="cursor-pointer px-3 py-2 text-left" onClick={() => toggleSort(key)}>{label}</th>
                    ))}
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pageRows.map((user) => (
                    <tr key={user.id}>
                      <td className="px-3 py-3 font-medium text-white">{user.username}</td>
                      <td className="px-3 py-3">{user.email}</td>
                      <td className="px-3 py-3 uppercase text-xs">{user.role}</td>
                      <td className="px-3 py-3 text-xs">{user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</td>
                      <td className="px-3 py-3">{user.servers}</td>
                      <td className="px-3 py-3">{user.events}</td>
                      <td className="px-3 py-3">{user.status}</td>
                      <td className="px-3 py-3">
                        <div className="flex gap-2">
                          <Link to={`/admin/users/${user.id}`}><Button variant="secondary" size="sm">View</Button></Link>
                          <Button variant="danger" size="sm" onClick={() => handleDelete(user)}>Delete</Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 flex items-center justify-between text-xs text-zinc-500">
              <span>{filtered.length} users</span>
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" disabled={page <= 0} onClick={() => setPage((p) => p - 1)}>Prev</Button>
                <span className="self-center">Page {page + 1} / {totalPages}</span>
                <Button variant="secondary" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage((p) => p + 1)}>Next</Button>
              </div>
            </div>
          </>
        )}
      </AdminCard>
    </div>
  )
}
