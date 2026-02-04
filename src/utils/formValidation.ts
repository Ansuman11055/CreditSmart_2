// Phase 4C UX Stability Fix - Form Input Utilities

/**
 * Safely converts string input to number, returning null if invalid
 * Prevents forcing empty/invalid inputs to 0 during typing
 */
export function sanitizeNumberInput(value: string): number | null {
  // Allow empty string (user clearing field)
  if (value.trim() === '') {
    return null;
  }

  // Allow partial inputs like "12." or ".5" during typing
  const num = parseFloat(value);
  
  // Check if parsing succeeded and result is valid
  if (isNaN(num) || !isFinite(num)) {
    return null;
  }

  return num;
}

/**
 * Validates that a string can be parsed as a positive number
 */
export function isValidPositiveNumber(value: string): boolean {
  const num = sanitizeNumberInput(value);
  return num !== null && num > 0;
}

/**
 * Formats a number for display in input field
 * Returns empty string for null/undefined to prevent "0" flash
 */
export function formatNumberForInput(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '';
  }
  return value.toString();
}
