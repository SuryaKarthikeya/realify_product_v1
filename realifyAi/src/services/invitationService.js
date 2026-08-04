import emailjs from "@emailjs/browser";

const SERVICE_ID  = import.meta.env.VITE_EMAILJS_SERVICE_ID;
const TEMPLATE_ID = import.meta.env.VITE_EMAILJS_TEMPLATE_ID;
const PUBLIC_KEY  = import.meta.env.VITE_EMAILJS_PUBLIC_KEY;

// Initialize EmailJS once when the module loads (v4 recommended pattern)
emailjs.init({ publicKey: PUBLIC_KEY });

/**
 * Sends an invitation email via EmailJS.
 */
export const sendInviteEmail = ({ email, userName, roleName, inviteLink }) => {
  if (!SERVICE_ID || !TEMPLATE_ID || !PUBLIC_KEY) {
    return Promise.reject(
      new Error("EmailJS credentials are missing. Check VITE_EMAILJS_* env vars.")
    );
  }

  return emailjs.send(
    SERVICE_ID,
    TEMPLATE_ID,
    {
      email,
      user_name:   userName || email.split("@")[0],
      role_name:   roleName,
      invite_link: inviteLink,
    }
    // No 4th arg needed — public key is set via init() above
  );
};
