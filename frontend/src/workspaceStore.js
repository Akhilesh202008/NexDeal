const data = new Map();

export const workspaceStore = {
  getItem(key) {
    return data.has(key) ? data.get(key) : null;
  },

  setItem(key, value) {
    data.set(key, String(value));
  },

  removeItem(key) {
    data.delete(key);
  },

  clear() {
    data.clear();
  }
};
