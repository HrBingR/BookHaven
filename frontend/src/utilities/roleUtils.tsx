export type UserRole = 'admin' | 'editor' | 'user';

export const hasPermission = (userRole: UserRole, requiredRole: UserRole): boolean => {
  const roleHierarchy: Record<UserRole, number> = {
    'user': 0,
    'editor': 1,
    'admin': 2
  };

  return roleHierarchy[userRole] >= roleHierarchy[requiredRole];
};

export const canUpload = (userRole: UserRole): boolean => {
  return hasPermission(userRole, 'editor');
};

export const canEditMetadata = (userRole: UserRole): boolean => {
  return hasPermission(userRole, 'editor');
};

export const canAccessAdmin = (userRole: UserRole): boolean => {
  return hasPermission(userRole, 'admin');
};