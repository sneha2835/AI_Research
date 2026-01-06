import React, { useState } from 'react';

const PasswordInput = ({ 
  id, 
  value, 
  onChange, 
  required = false, 
  minLength, 
  placeholder, 
  autoComplete,
  label 
}) => {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      <div className="field-password">
        <input
          id={id}
          type={showPassword ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          required={required}
          minLength={minLength}
          placeholder={placeholder}
          autoComplete={autoComplete}
        />
        <button
          type="button"
          className="toggle-button"
          onClick={() => setShowPassword((prev) => !prev)}
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? '🙈' : '👁️'}
        </button>
      </div>
    </label>
  );
};

export default PasswordInput;
