/**
 * Form validation utilities for pre-join lobby
 */

export interface ValidationErrors {
  displayName?: string;
  roomCode?: string;
  camera?: string;
}

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Validates display name input
 * @param name - The display name to validate
 * @returns ValidationResult with isValid flag and optional error message
 */
export function validateDisplayName(name: string): ValidationResult {
  if (!name || name.trim().length === 0) {
    return {
      isValid: false,
      error: 'Please enter your name to join the meeting'
    };
  }

  if (name.trim() !== name.trim().replace(/\s+/g, ' ')) {
    return {
      isValid: false,
      error: 'Display name cannot contain only spaces'
    };
  }

  if (name.trim().length < 1) {
    return {
      isValid: false,
      error: 'Display name cannot be empty or contain only spaces'
    };
  }

  return { isValid: true };
}

/**
 * Validates room code format
 * @param roomCode - The room code to validate
 * @returns ValidationResult with isValid flag and optional error message
 */
export function validateRoomCode(roomCode: string): ValidationResult {
  if (!roomCode || roomCode.trim().length === 0) {
    return {
      isValid: false,
      error: 'Room code is required'
    };
  }

  return { isValid: true };
}

/**
 * Form validation class for managing validation state
 */
export class FormValidation {
  private errors: ValidationErrors = {};

  constructor() {
    this.errors = {};
  }

  /**
   * Validates display name and updates errors
   */
  validateDisplayName(name: string): ValidationResult {
    const result = validateDisplayName(name);
    if (result.isValid) {
      delete this.errors.displayName;
    } else {
      this.errors.displayName = result.error;
    }
    return result;
  }

  /**
   * Validates room code and updates errors
   */
  validateRoomCode(roomCode: string): ValidationResult {
    const result = validateRoomCode(roomCode);
    if (result.isValid) {
      delete this.errors.roomCode;
    } else {
      this.errors.roomCode = result.error;
    }
    return result;
  }

  /**
   * Validates entire form
   */
  validateForm(displayName: string, roomCode: string): ValidationResult {
    const displayNameResult = this.validateDisplayName(displayName);
    const roomCodeResult = this.validateRoomCode(roomCode);

    const isValid = displayNameResult.isValid && roomCodeResult.isValid;
    
    return {
      isValid,
      error: isValid ? undefined : 'Please fix the errors above'
    };
  }

  /**
   * Clears all validation errors
   */
  clearErrors(): void {
    this.errors = {};
  }

  /**
   * Gets current validation errors
   */
  getErrors(): ValidationErrors {
    return { ...this.errors };
  }

  /**
   * Checks if form is valid (no errors)
   */
  get isValid(): boolean {
    return Object.keys(this.errors).length === 0;
  }
}