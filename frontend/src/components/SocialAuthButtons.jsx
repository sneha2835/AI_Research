import React from 'react';

const SocialAuthButtons = ({ mode = 'signin' }) => {
  const actionText = mode === 'signin' ? 'Sign in' : 'Sign up';

  return (
    <>
      <div className="dialog-divider">or continue with</div>
      <div className="dialog-social">
        <button type="button" className="btn-secondary">
          <span>🔐</span>
          {actionText} with Google
        </button>
        <button type="button" className="btn-secondary">
          <span>🆔</span>
          {actionText} with ORCID
        </button>
      </div>
    </>
  );
};

export default SocialAuthButtons;