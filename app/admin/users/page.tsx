'use client';

import React, { useEffect, useState } from 'react';

interface User {
    id: number;
    email: string;
    role: string;
    dept: string;
    display_name: string;
    created_at: string;
    admin_level: string | null;
    is_admin: boolean;
}

export default function UserManagementPage() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [editingUserId, setEditingUserId] = useState<number | null>(null);
    const [editForm, setEditForm] = useState({ role: 'USER', admin_level: 'standard' });

    useEffect(() => {
        const fetchUsers = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) throw new Error('No auth token');

                const response = await fetch('/api/backend?endpoint=/api/v1/admin/users', {
                    headers: { 'Authorization': `Bearer ${token}` },
                });

                if (!response.ok) throw new Error('Failed to fetch users');
                const data = await response.json();
                setUsers(data.users || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchUsers();
    }, []);

    const handleUpdateUser = async (userId: number) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) throw new Error('No auth token');

            const response = await fetch(
                `/api/backend?endpoint=/api/v1/admin/users/${userId}`,
                {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        ...editForm,
                        email: users.find(u => u.id === userId)?.email || '',
                        is_active: true,
                    }),
                }
            );

            if (!response.ok) throw new Error('Failed to update user');

            // Refresh users list
            const res = await fetch('/api/backend?endpoint=/api/v1/admin/users', {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            const data = await res.json();
            setUsers(data.users || []);
            setEditingUserId(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        }
    };

    if (loading) return <div className="loading">Loading users...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    return (
        <div className="users-page">
            <h1>User Management</h1>

            <div className="users-table-container">
                <table className="users-table">
                    <thead>
                        <tr>
                            <th>Email</th>
                            <th>Display Name</th>
                            <th>Department</th>
                            <th>Role</th>
                            <th>Admin Level</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map((user) => (
                            <tr key={user.id} className={user.is_admin ? 'admin-row' : ''}>
                                <td>{user.email}</td>
                                <td>{user.display_name}</td>
                                <td>{user.dept}</td>
                                <td>
                                    {editingUserId === user.id ? (
                                        <select
                                            value={editForm.role}
                                            onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                                        >
                                            <option value="USER">USER</option>
                                            <option value="ADMIN">ADMIN</option>
                                        </select>
                                    ) : (
                                        user.role
                                    )}
                                </td>
                                <td>
                                    {editingUserId === user.id && user.role === 'ADMIN' ? (
                                        <select
                                            value={editForm.admin_level}
                                            onChange={(e) => setEditForm({ ...editForm, admin_level: e.target.value })}
                                        >
                                            <option value="standard">standard</option>
                                            <option value="super">super</option>
                                        </select>
                                    ) : (
                                        user.admin_level || '-'
                                    )}
                                </td>
                                <td>{new Date(user.created_at).toLocaleDateString()}</td>
                                <td>
                                    {editingUserId === user.id ? (
                                        <>
                                            <button
                                                onClick={() => handleUpdateUser(user.id)}
                                                className="btn-save"
                                            >
                                                Save
                                            </button>
                                            <button
                                                onClick={() => setEditingUserId(null)}
                                                className="btn-cancel"
                                            >
                                                Cancel
                                            </button>
                                        </>
                                    ) : (
                                        <button
                                            onClick={() => {
                                                setEditingUserId(user.id);
                                                setEditForm({
                                                    role: user.role,
                                                    admin_level: user.admin_level || 'standard',
                                                });
                                            }}
                                            className="btn-edit"
                                        >
                                            Edit
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
