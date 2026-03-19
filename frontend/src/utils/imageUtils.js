export const getFullImageUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  
  // Extract host from VITE_API_BASE_URL or fallback
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/api';
  const host = apiBase.replace('/api', '');
  
  // Ensure we don't have double slashes if url already starts with one
  const cleanUrl = url.startsWith('/') ? url : `/${url}`;
  return `${host}${cleanUrl}`;
};
