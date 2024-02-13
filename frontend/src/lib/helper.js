// Helper functions examples, remove it not required

/**
 * Capitalizes the given string, e.g. from 'mouse' to 'Mouse'
 * @param {String} s 
 * @returns String
 */
export const capitalize = (s) => {
  if (typeof s !== 'string') return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
};
