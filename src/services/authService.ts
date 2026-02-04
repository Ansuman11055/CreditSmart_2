// Phase 4D+ Local Auth - Password-based authentication service

/**
 * Local authentication service with password hashing.
 * 
 * SECURITY NOTES:
 * - Passwords are hashed using SHA-256 (Web Crypto API)
 * - Plain-text passwords are NEVER stored
 * - Hashes are stored in localStorage
 * - Sessions persist based on "remember me" preference
 * 
 * UPGRADE PATH:
 * This implementation is designed to be replaced with backend auth
 * without breaking changes to the AuthContext interface.
 */

// Phase 4D+ Local Auth - Storage keys
const USERS_STORAGE_KEY = 'creditsmart_users';
const SESSION_STORAGE_KEY = 'creditsmart_session';

// Phase 4D+ Local Auth - User data structure
interface StoredUser {
  email: string;
  name: string;
  passwordHash: string;
  createdAt: string;
  currency?: string;
}

// Phase 4D+ Local Auth - Session data structure
interface Session {
  userId: string;
  email: string;
  name: string;
  currency: string;
  createdAt: string;
  rememberMe: boolean;
}

// Phase 4D+ Local Auth - Users database (localStorage)
interface UsersDatabase {
  [email: string]: StoredUser;
}

/**
 * Phase 4D+ Local Auth - Hash password using SHA-256
 * 
 * Uses Web Crypto API for secure hashing. Never logs input password.
 * 
 * @param password - Plain-text password (never stored)
 * @returns Hex string of SHA-256 hash
 */
export async function hashPassword(password: string): Promise<string> {
  try {
    // Convert password to bytes
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    
    // Hash using SHA-256
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    
    // Convert to hex string
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    return hashHex;
  } catch (error) {
    console.error('Password hashing failed:', error);
    throw new Error('Failed to hash password');
  }
}

/**
 * Phase 4D+ Local Auth - Load users database from localStorage
 */
function loadUsersDatabase(): UsersDatabase {
  try {
    const stored = localStorage.getItem(USERS_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Failed to load users database:', error);
    return {};
  }
}

/**
 * Phase 4D+ Local Auth - Save users database to localStorage
 */
function saveUsersDatabase(database: UsersDatabase): void {
  try {
    localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(database));
  } catch (error) {
    console.error('Failed to save users database:', error);
    throw new Error('Failed to save user data');
  }
}

/**
 * Phase 4D+ Local Auth - Generate deterministic user ID from email
 */
export function generateUserId(email: string): string {
  // Simple hash for user ID (not security-critical)
  let hash = 0;
  for (let i = 0; i < email.length; i++) {
    const char = email.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return `user_${Math.abs(hash).toString(36)}`;
}

/**
 * Phase 4D+ Local Auth - Sign up new user
 * 
 * @param name - User's full name
 * @param email - User's email (used as unique identifier)
 * @param password - Plain-text password (will be hashed)
 * @returns Success boolean
 * @throws Error if user already exists or validation fails
 */
export async function signUp(
  name: string,
  email: string,
  password: string
): Promise<{ success: boolean; error?: string }> {
  // Phase 4D+ Local Auth - Validate inputs
  if (!name || name.trim().length === 0) {
    return { success: false, error: 'Name is required' };
  }
  
  if (!email || !email.includes('@')) {
    return { success: false, error: 'Valid email is required' };
  }
  
  if (!password || password.length < 6) {
    return { success: false, error: 'Password must be at least 6 characters' };
  }
  
  // Phase 4D+ Local Auth - Check for existing user
  const database = loadUsersDatabase();
  const normalizedEmail = email.toLowerCase().trim();
  
  if (database[normalizedEmail]) {
    return { success: false, error: 'User already exists. Please sign in.' };
  }
  
  try {
    // Phase 4D+ Local Auth - Hash password (NEVER store plain-text)
    const passwordHash = await hashPassword(password);
    
    // Phase 4D+ Local Auth - Create user record
    const newUser: StoredUser = {
      email: normalizedEmail,
      name: name.trim(),
      passwordHash,
      createdAt: new Date().toISOString(),
      currency: 'USD'
    };
    
    // Phase 4D+ Local Auth - Save to database
    database[normalizedEmail] = newUser;
    saveUsersDatabase(database);
    
    console.log('User registered successfully:', normalizedEmail);
    return { success: true };
    
  } catch (error) {
    console.error('Sign up failed:', error);
    return { success: false, error: 'Registration failed. Please try again.' };
  }
}

/**
 * Phase 4D+ Local Auth - Sign in existing user
 * 
 * @param email - User's email
 * @param password - Plain-text password (will be hashed and compared)
 * @param rememberMe - Whether to persist session across browser restarts
 * @returns User data if successful, error message if failed
 */
export async function signIn(
  email: string,
  password: string,
  rememberMe: boolean = false
): Promise<{ success: boolean; user?: Session; error?: string }> {
  // Phase 4D+ Local Auth - Validate inputs
  if (!email || !password) {
    return { success: false, error: 'Email and password are required' };
  }
  
  const normalizedEmail = email.toLowerCase().trim();
  
  // Phase 4D+ Local Auth - Load user database
  const database = loadUsersDatabase();
  const storedUser = database[normalizedEmail];
  
  if (!storedUser) {
    return { success: false, error: 'User not found' };
  }
  
  try {
    // Phase 4D+ Local Auth - Hash input password
    const inputHash = await hashPassword(password);
    
    // Phase 4D+ Local Auth - Compare hashes (constant-time comparison would be ideal)
    if (inputHash !== storedUser.passwordHash) {
      return { success: false, error: 'Invalid password' };
    }
    
    // Phase 4D+ Local Auth - Create session
    const session: Session = {
      userId: generateUserId(normalizedEmail),
      email: storedUser.email,
      name: storedUser.name,
      currency: storedUser.currency || 'USD',
      createdAt: new Date().toISOString(),
      rememberMe
    };
    
    // Phase 4D+ Local Auth - Persist session based on remember me preference
    if (rememberMe) {
      // Persistent session (survives browser restart)
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    } else {
      // Temporary session (cleared on browser close)
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    }
    
    console.log('User signed in successfully:', normalizedEmail);
    return { success: true, user: session };
    
  } catch (error) {
    console.error('Sign in failed:', error);
    return { success: false, error: 'Authentication failed. Please try again.' };
  }
}

/**
 * Phase 4D+ Local Auth - Restore session on app load
 * 
 * Checks both localStorage (persistent) and sessionStorage (temporary)
 * for existing session data.
 * 
 * @returns Session data if found, null otherwise
 */
export function restoreSession(): Session | null {
  try {
    // Phase 4D+ Local Auth - Check localStorage first (remember me)
    const persistentSession = localStorage.getItem(SESSION_STORAGE_KEY);
    if (persistentSession) {
      return JSON.parse(persistentSession);
    }
    
    // Phase 4D+ Local Auth - Check sessionStorage (current session)
    const temporarySession = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (temporarySession) {
      return JSON.parse(temporarySession);
    }
    
    return null;
  } catch (error) {
    console.error('Failed to restore session:', error);
    return null;
  }
}

/**
 * Phase 4D+ Local Auth - Sign out current user
 * 
 * Clears session from both localStorage and sessionStorage.
 * Does NOT delete user account data.
 */
export function signOut(): void {
  try {
    // Phase 4D+ Local Auth - Clear session only (not user data)
    localStorage.removeItem(SESSION_STORAGE_KEY);
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    
    console.log('User signed out successfully');
  } catch (error) {
    console.error('Sign out failed:', error);
  }
}

/**
 * Phase 4D+ Local Auth - Check if user account exists
 * 
 * Used to determine whether to show sign-up or sign-in form.
 * 
 * @param email - Email to check
 * @returns True if user exists
 */
export function userExists(email: string): boolean {
  const database = loadUsersDatabase();
  const normalizedEmail = email.toLowerCase().trim();
  return normalizedEmail in database;
}

/**
 * Phase 4D+ Local Auth - Update user currency preference
 * 
 * @param email - User's email
 * @param currency - New currency code
 */
export function updateUserCurrency(email: string, currency: string): void {
  try {
    const database = loadUsersDatabase();
    const normalizedEmail = email.toLowerCase().trim();
    
    if (database[normalizedEmail]) {
      database[normalizedEmail].currency = currency;
      saveUsersDatabase(database);
      
      // Phase 4D+ Local Auth - Update active session if exists
      const persistentSession = localStorage.getItem(SESSION_STORAGE_KEY);
      const temporarySession = sessionStorage.getItem(SESSION_STORAGE_KEY);
      
      if (persistentSession) {
        const session = JSON.parse(persistentSession);
        session.currency = currency;
        localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
      }
      
      if (temporarySession) {
        const session = JSON.parse(temporarySession);
        session.currency = currency;
        sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
      }
    }
  } catch (error) {
    console.error('Failed to update currency:', error);
  }
}
