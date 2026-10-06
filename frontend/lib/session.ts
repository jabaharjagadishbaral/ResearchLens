const KEY = "rm_token";
export const getToken = (): string | null => (typeof window === "undefined" ? null : sessionStorage.getItem(KEY));
export const setToken = (t: string) => sessionStorage.setItem(KEY, t);
export const clearToken = () => sessionStorage.removeItem(KEY);
